"""AI-powered relevance filter for search results.

Instead of 250+ lines of regex, brand lists, and accessory keywords,
one AI call understands what the user wants and filters irrelevant products.

"Cactus Moto Expert 100" (projector screen) → filters out Cactus printer ink
"Samsung Galaxy S25 Ultra" → filters out S25 FE, S24, cases, cables
"Tuvio телевизор 55" → filters out remotes, brackets, boards
"""

import json

import structlog
from openai import AsyncOpenAI

from app.config import settings
from app.scrapers.category_extractor import detect_intent_from_keywords


logger = structlog.get_logger()


# Categories where the user IS asking for the "for X" thing. Used to bias
# the relevance prompt — without this hint Gemini ignores the exception
# clause maybe 1 in 5 calls and drops every "чехол iPhone" item.
_ACCESSORY_INTENT_CATS = {
    "accessory_case",
    "accessory_cable",
    "accessory_mount",
    "accessory_controller",
    "spare_part",
    "consumable",
    "videogame",
}

_INTENT_HINT_TEMPLATE = """

CRITICAL — INTENT HINT FOR THIS QUERY:
The query "{query}" is asking for: {category}.
This means items whose role is "{category}" are EXACTLY what the user wants.
Do NOT exclude an item just because its title contains "{kw_hint}". That word
is the QUERY ITSELF, not a disqualifier.

Apply these rules instead:
- KEEP items that are the {category} for the device named in the query
  (model number, brand, generation must match).
- REJECT items that are the device itself (the user wants the {category},
  not the device).
- REJECT cross-model items (e.g. a case for iPhone 14 when the query
  names iPhone 16).
- REJECT obvious junk, fakes, refurbished, used.
"""


_INTENT_KEYWORD_FOR_CATEGORY = {
    "accessory_case": "чехол / кейс / case / cover / защитное стекло",
    "accessory_cable": "кабель / зарядка / адаптер / провод / cable / charger",
    "accessory_mount": "кронштейн / держатель / подставка / mount / bracket",
    "accessory_controller": "геймпад / джойстик / пульт / controller / gamepad",
    "spare_part": "аккумулятор / дисплей / шлейф / запчасть",
    "consumable": "картридж / тонер / чернила / фильтр",
    "videogame": "игра / диск / gift card",
}


_FILTER_PROMPT = """You are a product relevance filter for a price comparison website.

USER QUERY: "{query}"

Below is a list of products found by marketplace scrapers. Return ONLY the numbers
of products that are THE SAME PRODUCT the user is looking for.

CORE PRINCIPLE — the product IS, not "goes with":
A product is relevant ONLY if it is literally the thing named in the query.
Anything that is used WITH, FOR, INSIDE, INSTEAD OF, or AS A REPLACEMENT FOR
that thing is a DIFFERENT product and must be excluded, even if the title
contains the exact query words.

IMPORTANT — edition/trim variants of the SAME product are RELEVANT:
If the query names a base product without specifying a variant (e.g. "PlayStation 5",
"iPhone 15", "MacBook Air"), then ALL editions/trims of that base product are
relevant: Slim, Pro, Digital Edition, Disc Edition, regional bundles, different
storage/memory, different colors, with/without included extras. Do NOT reject
these as "different variants". A "Sony PlayStation 5 Slim Digital Edition 1TB"
IS a PlayStation 5. An "iPhone 15 128GB Blue" IS an iPhone 15. Variant rejection
applies ONLY when the query ITSELF specifies a variant — then keep only that one.

Exclude as a DIFFERENT product (non-exhaustive — apply the principle, not the list):
- Content that runs on a device: games, films, music, software, subscriptions,
  gift cards — these are NOT the device
- Accessories and peripherals: cases, covers, cables, chargers, adapters,
  mounts, brackets, stands, straps, bags, remotes, controllers (unless the
  query IS a controller), styluses, screen protectors, films
- Spare parts and components: boards, matrices, displays, flex cables,
  batteries, power supplies, hinges, housings, fans, keyboards "for X",
  "replacement for X"
- Consumables for a device: ink, cartridges, toner, filters, bags, pods
- Different model / generation: if the query specifies a specific generation
  or numbered model (e.g. "iPhone 15" vs iPhone 14, "S25" vs S24, "RTX 4090"
  vs 4080), reject items with a different one — close is not equal.
  But see the edition/trim rule above: variants of the SAME generation
  (Slim/Pro/Digital/storage tiers) stay unless the query names a specific one.
- Different brand: if the query names a brand, reject other brands (even if
  the title mentions the queried brand as a compatibility tag like "для Brand")

Signal words in titles that usually mean "NOT the product itself":
  для / for / к / под / совместим / compatible / replacement / запчасть /
  чехол / кейс / case / cover / кабель / cable / адаптер / adapter /
  кронштейн / mount / bracket / игра / game / подписка / subscription /
  картридж / cartridge / пульт / remote / ремешок / strap

Exception: if the query itself names one of these things (e.g. "чехол iPhone",
"кабель USB-C", "картридж HP 305"), then that IS the product — keep it.

Additional rules:
- Refurbished / used / "восстановленный" / "б/у" / "витринный" — EXCLUDE
- Suspiciously cheap clones / fakes — EXCLUDE
- If NOTHING matches, return empty array []. An empty result is STRICTLY
  BETTER than returning wrong products. Do not be lenient. Do not "try to
  be helpful" by including near-matches.

PRODUCTS:
{products}

Respond with ONLY a JSON array of matching product numbers. Example: [1, 3, 5]
No explanation, no text, just the array."""


def _get_client() -> AsyncOpenAI | None:
    api_key = settings.OPENROUTER_API_KEY or settings.ANTHROPIC_API_KEY
    if not api_key:
        return None
    return AsyncOpenAI(api_key=api_key, base_url=settings.OPENROUTER_BASE_URL)


async def ai_filter_relevant(products: list[dict], query: str) -> list[dict]:
    """Filter products using AI to determine relevance.

    Args:
        products: Raw products from scrapers
        query: User's search query

    Returns:
        Only the relevant products, or all products if AI is unavailable
    """
    if not products or len(products) <= 2:
        return products

    client = _get_client()
    if not client:
        logger.warning("ai_filter_no_client")
        return products

    # Build numbered product list for AI
    product_lines = []
    for i, p in enumerate(products, 1):
        title = p.get("title", "?")
        price = p.get("price", "?")
        shop = p.get("shop", "?")
        product_lines.append(f"{i}. {title} — {price} ({shop})")

    products_text = "\n".join(product_lines)

    prompt = _FILTER_PROMPT.format(query=query, products=products_text)

    # Inject explicit intent hint when the query unambiguously names an
    # accessory / part / consumable / game. Without this Gemini sometimes
    # ignores the exception clause inside _FILTER_PROMPT and rejects every
    # "чехол ..." item even when the user wrote "чехол" themselves.
    intent_cat = detect_intent_from_keywords(query)
    if intent_cat in _ACCESSORY_INTENT_CATS:
        kw_hint = _INTENT_KEYWORD_FOR_CATEGORY.get(intent_cat, intent_cat)
        prompt = prompt + _INTENT_HINT_TEMPLATE.format(
            query=query, category=intent_cat, kw_hint=kw_hint
        )

    try:
        response = await client.chat.completions.create(
            model=settings.AI_MODEL,
            max_tokens=300,
            temperature=0,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )

        result_text = response.choices[0].message.content.strip()

        # Extract JSON array from response — Gemini may add text around it
        import re

        # Strategy 1: find [N, N, N] pattern (digits, spaces, commas only)
        json_match = re.search(r"\[[\d\s,]*\]", result_text)
        if json_match:
            result_text = json_match.group(0)
        # Strategy 2: find any [...] array (may contain extra text)
        elif "[" in result_text and "]" in result_text:
            start = result_text.index("[")
            end = result_text.rindex("]") + 1
            result_text = result_text[start:end]
            # Clean: extract just numbers from between brackets
            inner = result_text[1:-1]
            numbers = re.findall(r"\d+", inner)
            result_text = "[" + ", ".join(numbers) + "]"
        # Strategy 3: code block
        elif "```" in result_text:
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]
            result_text = result_text.strip()

        indices = json.loads(result_text)

        if not isinstance(indices, list):
            logger.warning("ai_filter_bad_response", response=result_text)
            return products

        # Convert 1-indexed to 0-indexed and filter
        filtered = []
        for idx in indices:
            if isinstance(idx, int) and 1 <= idx <= len(products):
                filtered.append(products[idx - 1])

        logger.info(
            "ai_filter_result",
            query=query,
            total=len(products),
            kept=len(filtered),
            indices=indices,
        )

        # Safety net 1: total wipeout — if AI returns [] on ANY non-empty
        # pool, degrade to input. The upstream fast_filter + cluster +
        # category stages already removed obvious junk; an empty AI verdict
        # almost always means the model was too strict (e.g. rejecting
        # "compatible with X" items when the user searched for "X brush").
        # Showing something is always better than "ничего не найдено".
        if len(products) >= 3 and len(filtered) == 0:
            logger.warning(
                "ai_filter_total_wipeout",
                query=query,
                total=len(products),
            )
            return products

        # Safety net 2: if the LLM drops almost everything from a non-trivial
        # input pool, it is overwhelmingly likely a prompt/temperature glitch
        # (observed: same corrected query "PlayStation 5" → 24 kept on one
        # call, 1 kept on the next). The upstream regex + price-cluster stages
        # already removed the obvious junk, so a >=95% drop on a pool of ≥10
        # items means the LLM disagreed with itself, not that 95% are junk.
        # Degrade gracefully to the input so the user still sees something.
        if len(products) >= 10 and len(filtered) <= max(1, len(products) // 20):
            logger.warning(
                "ai_filter_suspicious_drop",
                query=query,
                total=len(products),
                kept=len(filtered),
            )
            return products

        return filtered

    except Exception as e:
        logger.error("ai_filter_error", error=str(e), query=query)
        # Network / JSON error is NOT the same as "nothing matches" — fall
        # back to the input so that live-search still shows something.
        # The analyze path adds its own min-count check on top.
        return products
