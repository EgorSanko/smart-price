"""Symmetric category extraction — the query and the candidate items are
classified INTO THE SAME canonical taxonomy, then filtered by equality.

Why this beats "is this title relevant to query" prompting:
The relevance task is subjective ("does X match Y?"). The category task
is objective ("what is X?"). Amazon's arxiv 2310.14820 reports an 8-12%
F1 improvement from switching relevance prompts to category extraction
prompts on the same data, because the per-item judgement no longer
depends on seeing the query.

Failure mode of the old filter this replaces:
  query = "RTX 4090"
  item  = "Кабель питания 8-pin для RTX 4090, 500mm"
The old relevance prompt read the shared token "RTX 4090" and kept the
cable. Category extraction sees `computer_component_gpu` vs
`accessory_cable` and drops it on equality.

The taxonomy is intentionally coarse (14 buckets). Finer categories
(e.g. laptop vs tablet vs phone) are handled by the downstream regex
brand/model filter, not here. Here we only answer "is this even the
same KIND of thing as what the user asked for".
"""

import asyncio
import json
import re

import structlog
from openai import AsyncOpenAI

from app.config import settings
from app.data.category_negatives import negatives_for


logger = structlog.get_logger()

# Canonical taxonomy. Keep this list short and stable — it is embedded
# in every LLM prompt and changing it invalidates the cache.
CATEGORIES: tuple[str, ...] = (
    "electronics_device",  # phone, tablet, laptop, tv, console, camera, drone, projector, e-reader
    "computer_component",  # gpu, cpu, ram, ssd, motherboard, psu, case, cooler
    "audio_device",  # headphones, earbuds, speakers, soundbars, microphones
    "wearable",  # smartwatch, fitness band, VR headset
    "home_appliance",  # vacuum, mixer, iron, coffee machine, air purifier
    "videogame",  # disc, digital code, game card, subscription card
    "media_content",  # film, music, book, streaming subscription
    "accessory_case",  # case, cover, sleeve, bag, pouch, skin, film/screen protector
    "accessory_cable",  # cable, adapter, charger, dock, power supply (external)
    "accessory_mount",  # mount, bracket, stand, tripod, holder
    "accessory_controller",  # gamepad, joystick, remote, stylus, keyboard/mouse (as standalone)
    "spare_part",  # battery, screen/matrix, board, motor, fan, filter (as replacement part)
    "consumable",  # ink, toner, bag, filter (single-use), detergent, pod
    "other",
)

_CATEGORY_SET = set(CATEGORIES)


# ---------------------------------------------------------------------------
# Deterministic intent detection — fast path before the LLM call.
#
# When the query CONTAINS an accessory/part/consumable keyword as a whole
# token, we know the user is asking for that kind of thing — no need to
# pay an LLM round-trip and risk Gemini misclassifying it as a device.
#
# The patterns match only at word boundaries on the query (not on item
# titles). Order matters only within a category — first match wins inside
# the category, but every keyword in one category is treated equally.
#
# Word boundary is `(?:^|\W)` / `(?:\W|$)` instead of `\b` because `\b` in
# Python's `re` doesn't treat Cyrillic well — `\b` looks for a transition
# between [a-zA-Z0-9_] and the rest, which means "чехол" inside "чехлы"
# would not be considered separately. We want stemming, so we accept any
# trailing Cyrillic suffix.
# ---------------------------------------------------------------------------
_W = r"(?:^|[\s\-\.,;:!?\(\)\[\]/\"'«»])"  # left boundary
# Right boundary is implicit by allowing a word stem (the patterns end
# with optional Cyrillic/Latin chars).

_INTENT_PATTERNS: dict[str, tuple[str, ...]] = {
    "accessory_case": (
        # Russian "чехол" loses the «о» in oblique forms (чехла, чехлы,
        # чехлами, чехлов). Stem on "чехл" with optional "о" between the
        # «х» and «л» catches both nominative "чехол" and all declined
        # forms in one pattern.
        rf"{_W}чех[ол]?л",
        rf"{_W}кейс",
        rf"{_W}бампер",
        rf"{_W}накладк",
        rf"{_W}case\b",
        rf"{_W}cover\b",
        rf"{_W}sleeve\b",
        rf"{_W}skin\b",
        rf"{_W}защитн\w*\s+стекл",
        rf"{_W}стекло\s+защитн",
        rf"{_W}защитн\w*\s+плёнк",
        rf"{_W}защитн\w*\s+пленк",
        rf"{_W}плёнк\w*\s+для",
        rf"{_W}пленк\w*\s+для",
        rf"{_W}гидрогел",
        rf"{_W}наклейк",
    ),
    "accessory_cable": (
        rf"{_W}кабел",
        rf"{_W}провод\s+для",
        rf"{_W}зарядк",  # зарядка, зарядку
        rf"{_W}зарядн\w*\s+(устройств|кабел|блок)",
        rf"{_W}зарядное\s+устройств",
        rf"{_W}переходник",
        rf"{_W}адаптер",  # адаптер, адаптеры
        rf"{_W}блок\s+питани",
        rf"{_W}dock\b",
        rf"{_W}docking\b",
        rf"{_W}charger\b",
        rf"{_W}cable\b",
    ),
    "accessory_mount": (
        rf"{_W}кронштейн",
        rf"{_W}подставк",
        rf"{_W}держател\w*\s+для",
        rf"{_W}креплени",
        rf"{_W}штатив",
        rf"{_W}mount\b",
        rf"{_W}bracket\b",
        rf"{_W}stand\b",
        rf"{_W}tripod\b",
    ),
    "accessory_controller": (
        rf"{_W}геймпад",
        rf"{_W}джойстик",
        rf"{_W}контроллер",
        rf"{_W}пульт",
        rf"{_W}стилус",
        rf"{_W}gamepad\b",
        rf"{_W}controller\b",
        rf"{_W}joystick\b",
        rf"{_W}stylus\b",
        rf"{_W}remote\b",
    ),
    "spare_part": (
        rf"{_W}аккумулятор\s+(для|на|к)\b",
        rf"{_W}батаре\w*\s+(для|на)\b",
        rf"{_W}акб\s+(для|на)",
        rf"{_W}дисплей\s+для",
        rf"{_W}матриц\w*\s+для",
        rf"{_W}экран\s+для",
        rf"{_W}тачскрин",
        rf"{_W}шлейф\b",
        rf"{_W}корпус\s+для",
        rf"{_W}задн\w*\s+крышк",
        rf"{_W}запчаст",
    ),
    "videogame": (
        rf"^игра\s",
        rf"{_W}диск\s+с\s+игр",
        rf"{_W}game\s+(disc|disk|card)\b",
        rf"{_W}gift\s+card\b",
        rf"{_W}подарочн\w*\s+карт",
    ),
    "consumable": (
        rf"{_W}картридж",
        rf"{_W}тонер",
        rf"{_W}чернил",
        rf"{_W}мешок\s+для",
        rf"{_W}мешк\w*\s+для",
        rf"{_W}фильтр\s+для",
        rf"{_W}сменн\w*\s+фильтр",
        rf"{_W}hepa\s+для",
    ),
}


def detect_intent_from_keywords(query: str) -> str | None:
    """Determine query category from keywords alone, without an LLM call.

    Returns a canonical category if the query unambiguously names an
    accessory / spare part / consumable / game. Returns None when the
    query has no such marker — caller should fall back to LLM
    classification (or treat as device by default).

    Note: a query that *combines* an accessory keyword with a device name
    (e.g. "чехол iPhone 16 Pro") still gets the accessory category. The
    device name is shared between accessory and device queries, so it
    cannot disambiguate — the accessory keyword is the decisive token.
    """
    if not query:
        return None
    q = " " + query.lower() + " "  # padding helps left-boundary matches
    for category, patterns in _INTENT_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, q, flags=re.IGNORECASE | re.UNICODE):
                return category
    return None


# In-memory cache for item titles. Titles repeat across marketplaces
# (Onliner and Yandex both list the same "Sony PlayStation 5 Slim 1TB
# Digital" SKU), so a process-local dict cuts LLM calls by ~30-50%
# within a single session. Not persisted across restarts — that would
# need Redis, and the caller should be robust to cold starts anyway.
_ITEM_CACHE: dict[str, str] = {}
_ITEM_CACHE_MAX = 5_000


def _get_client() -> AsyncOpenAI | None:
    api_key = settings.OPENROUTER_API_KEY or settings.ANTHROPIC_API_KEY
    if not api_key:
        return None
    return AsyncOpenAI(api_key=api_key, base_url=settings.OPENROUTER_BASE_URL)


_CATEGORIES_LINE = ", ".join(CATEGORIES)

_QUERY_PROMPT = f"""You are a product taxonomy classifier.

Classify the search query into EXACTLY ONE of these categories:
{_CATEGORIES_LINE}

Rules:
- Return ONLY the category label, nothing else — no quotes, no explanation.
- "electronics_device" = the device itself (phone, laptop, console, tv, camera, drone, projector, etc.)
- "computer_component" = GPU, CPU, RAM, SSD, motherboard, PSU, PC case, cooler (parts that go inside a PC)
- "accessory_case" = case, cover, sleeve, screen protector
- "accessory_cable" = cable, charger, adapter, dock
- "accessory_controller" = gamepad, joystick, remote, stylus, standalone keyboard/mouse
- "videogame" = a game title / disc / digital code (NOT the console)
- "spare_part" = replacement component (battery, display, board) sold as a repair part
- If the query explicitly names one of the accessory/part types, use that category — NOT electronics_device.

Examples:
- "PS5" → electronics_device
- "PlayStation 5 Slim" → electronics_device
- "God of War PS5" → videogame
- "геймпад PS5" → accessory_controller
- "чехол iPhone 15" → accessory_case
- "кабель USB-C" → accessory_cable
- "RTX 4090" → computer_component
- "кабель для RTX 4090" → accessory_cable
- "AirPods Pro 3" → audio_device
- "робот пылесос" → home_appliance
- "Sony телевизор" → electronics_device
- "картридж HP" → consumable
- "батарея iPhone 12" → spare_part
"""


_ITEMS_PROMPT = f"""You are a product taxonomy classifier.

For each numbered product title, return its category from EXACTLY this list:
{_CATEGORIES_LINE}

Rules:
- Return a JSON array of strings, one per input line, SAME ORDER as input.
- No explanation, no markdown, just the array. Example: ["electronics_device", "videogame", "accessory_case"]
- Judge each title in isolation. Do NOT assume they all belong to the same category.
- Look at the ROLE of the item: "кабель для X" → accessory_cable (even if X is a device).
  "чехол на X" → accessory_case. "игра X" / "диск X" → videogame. "батарея для X" / "аккумулятор X" → spare_part.
- A bundled listing (device + extra) is still the primary item's category
  (e.g. "PS5 + игра" → electronics_device because the console is the primary).
"""


async def classify_query(query: str) -> str | None:
    """Classify a search query into one canonical category. None on failure.

    Fast path: if the query contains an unambiguous accessory / part /
    consumable keyword (e.g. "чехол", "кабель для", "картридж"), we
    decide the category deterministically and skip the LLM. This makes
    the result reproducible across runs and removes a class of bugs
    where Gemini 2.5 Flash occasionally returns `electronics_device`
    for "чехол iPhone 16 Pro" — which then triggered the device-only
    negative-keyword list and silently dropped every case from the pool.
    """
    keyword_cat = detect_intent_from_keywords(query)
    if keyword_cat is not None:
        logger.info("category_query_keyword_hit", query=query, category=keyword_cat)
        return keyword_cat

    client = _get_client()
    if not client:
        return None

    try:
        response = await client.chat.completions.create(
            model=settings.AI_MODEL,
            max_tokens=20,
            temperature=0,
            messages=[
                {"role": "system", "content": _QUERY_PROMPT},
                {"role": "user", "content": query},
            ],
        )
        raw = (response.choices[0].message.content or "").strip().lower()
        # Strip quotes / punctuation the LLM sometimes adds
        raw = raw.strip("\"'`.,; \n\t")
        if raw in _CATEGORY_SET:
            return raw
        # Sometimes the LLM returns "electronics_device." or "Category: electronics_device"
        for cat in CATEGORIES:
            if cat in raw:
                return cat
        logger.warning("category_query_unknown_label", query=query, raw=raw)
        return None
    except Exception as e:
        logger.warning("category_query_error", query=query, error=str(e))
        return None


async def classify_items(titles: list[str]) -> list[str | None]:
    """Classify a batch of product titles. Returns per-title category or None.

    Uses an in-memory cache — identical titles across marketplaces are
    only sent to the LLM once per process lifetime.
    """
    if not titles:
        return []

    # Split into cached vs unknown. Keep the original positions so we can
    # reassemble the output in order.
    cached: dict[int, str] = {}
    unknown_positions: list[int] = []
    unknown_titles: list[str] = []
    for i, t in enumerate(titles):
        key = (t or "").strip().lower()
        if not key:
            cached[i] = "other"
            continue
        hit = _ITEM_CACHE.get(key)
        if hit is not None:
            cached[i] = hit
        else:
            unknown_positions.append(i)
            unknown_titles.append(t)

    # If everything was cached, skip the LLM call entirely.
    if not unknown_titles:
        return [cached[i] for i in range(len(titles))]

    client = _get_client()
    if not client:
        # LLM unavailable — fill unknowns with None so caller can pass them through
        result: list[str | None] = [None] * len(titles)
        for i, c in cached.items():
            result[i] = c
        return result

    numbered = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(unknown_titles))
    user_content = (
        f"PRODUCTS:\n{numbered}\n\nReturn JSON array of {len(unknown_titles)} category labels."
    )

    predictions: list[str | None] = [None] * len(unknown_titles)
    try:
        response = await client.chat.completions.create(
            model=settings.AI_MODEL,
            max_tokens=30 + 25 * len(unknown_titles),
            temperature=0,
            messages=[
                {"role": "system", "content": _ITEMS_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
        raw = (response.choices[0].message.content or "").strip()
        # Extract the JSON array — Gemini sometimes wraps in ```json ... ```
        m = re.search(r"\[[^\[\]]*\]", raw, flags=re.DOTALL)
        if not m:
            logger.warning("category_items_no_array", raw=raw[:200])
        else:
            try:
                parsed = json.loads(m.group(0))
            except Exception:
                # Extract quoted strings as a last resort
                parsed = re.findall(r'"([a-z_]+)"', m.group(0))
            if isinstance(parsed, list):
                for i, label in enumerate(parsed[: len(unknown_titles)]):
                    if isinstance(label, str):
                        lab = label.strip().lower()
                        if lab in _CATEGORY_SET:
                            predictions[i] = lab
    except Exception as e:
        logger.warning("category_items_error", error=str(e), count=len(unknown_titles))

    # Write successful predictions into the cache (bounded)
    for title, pred in zip(unknown_titles, predictions, strict=False):
        if pred is None:
            continue
        if len(_ITEM_CACHE) >= _ITEM_CACHE_MAX:
            # Crude eviction: clear half on overflow. A real LRU would be
            # better but this is a diploma project and this path is rare.
            for k in list(_ITEM_CACHE.keys())[: _ITEM_CACHE_MAX // 2]:
                _ITEM_CACHE.pop(k, None)
        _ITEM_CACHE[(title or "").strip().lower()] = pred

    # Reassemble full result in original order
    result = [None] * len(titles)
    for i, c in cached.items():
        result[i] = c
    for pos, pred in zip(unknown_positions, predictions, strict=False):
        result[pos] = pred
    return result


def _apply_negative_keywords(products: list[dict], category: str | None) -> tuple[list[dict], int]:
    """Drop products whose title hits any of the category's negative keywords.

    Runs before the expensive per-item LLM classification so we save both
    latency and tokens. Returns (kept_products, dropped_count).
    """
    negs = negatives_for(category)
    if not negs:
        return list(products), 0
    kept: list[dict] = []
    dropped = 0
    for p in products:
        title_lower = (p.get("title") or "").lower()
        if any(n in title_lower for n in negs):
            dropped += 1
            continue
        kept.append(p)
    return kept, dropped


async def filter_by_category(products: list[dict], query: str) -> tuple[list[dict], dict]:
    """Drop products whose extracted category != query's category.

    Pipeline inside this function:
      1. classify_query(q)                       — 1 LLM call
      2. negative keyword regex on title         — free
      3. classify_items(remaining titles)        — 1 batched LLM call
      4. equality filter on categories           — free

    Returns (filtered_products, meta_dict). On any failure the input is
    returned unchanged so the pipeline never dies on a category service
    hiccup — the downstream regex/cluster filters already caught the
    obvious junk.
    """
    if not products or len(products) <= 2:
        return products, {"action": "noop_too_few", "total_in": len(products)}

    original_products = products  # keep full pool for safety-net fallback
    original_in = len(products)

    # Step 1: Classify the query first (needed for both negatives and the
    # per-item equality check). This is a single cheap call.
    query_cat = await classify_query(query)
    if query_cat is None:
        logger.warning("category_filter_no_query_cat", query=query)
        return original_products, {"action": "noop_no_query_cat", "total_in": original_in}

    # Step 2: Apply per-category negative keywords. This drops obvious
    # accessory/fake/part/refurb noise BEFORE we pay for per-item LLM
    # classification. For categories with no negatives (accessory_case,
    # spare_part, etc.) this is a no-op.
    products, negatives_dropped = _apply_negative_keywords(original_products, query_cat)

    if not products:
        # Shouldn't happen unless every single title hit a negative,
        # which is unrealistic — but fall back safely.
        logger.warning("category_filter_all_negated", query=query, query_cat=query_cat)
        return original_products, {
            "action": "noop_all_negated",
            "total_in": original_in,
            "negatives_dropped": negatives_dropped,
            "query_cat": query_cat,
        }

    # Step 3: Classify the surviving items (batched, cached).
    titles = [p.get("title", "") for p in products]
    item_cats = await classify_items(titles)

    # Count how many items got a valid category vs None
    classified = sum(1 for c in item_cats if c is not None)
    if classified == 0:
        logger.warning("category_filter_no_items_cat", query=query)
        return original_products, {
            "action": "noop_no_item_cats",
            "total_in": original_in,
        }

    filtered: list[dict] = []
    kept_by_cat: dict[str, int] = {}
    dropped_by_cat: dict[str, int] = {}
    for p, cat in zip(products, item_cats, strict=False):
        if cat is None:
            # Unknown category → keep (safer default; regex/cluster already vetted it)
            filtered.append(p)
            kept_by_cat["__unknown__"] = kept_by_cat.get("__unknown__", 0) + 1
            continue
        if cat == query_cat:
            filtered.append(p)
            kept_by_cat[cat] = kept_by_cat.get(cat, 0) + 1
        else:
            dropped_by_cat[cat] = dropped_by_cat.get(cat, 0) + 1

    meta = {
        "action": "applied",
        "query_cat": query_cat,
        "total_in": original_in,
        "total_out": len(filtered),
        "classified": classified,
        "negatives_dropped": negatives_dropped,
        "kept_by_cat": kept_by_cat,
        "dropped_by_cat": dropped_by_cat,
    }

    # Safety net: if category filter would drop >=95% of the ORIGINAL
    # non-trivial pool (including what negatives removed), it almost
    # certainly misclassified the query. Fall back to input. Same
    # defensive pattern as ai_filter_relevant.
    if original_in >= 10 and len(filtered) <= max(1, original_in // 20):
        logger.warning("category_filter_suspicious_drop", query=query, **meta)
        meta["action"] = "applied_fallback_suspicious"
        # Return original full input so the pipeline can fall back to
        # unfiltered rather than collapse. We restore the negatives-stripped
        # items too since the classifier failure suggests our whole
        # category guess is wrong.
        return original_products, meta

    logger.info("category_filter_result", query=query, **meta)
    return filtered, meta
