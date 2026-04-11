"""Query correction using AI (OpenRouter) + Yandex Speller fallback.

AI understands context: "ipone 17 pra" → "iPhone 17 Pro",
"sams s25 ultra" → "Samsung Galaxy S25 Ultra".
"""

import httpx
import structlog
from openai import AsyncOpenAI

from app.config import settings


logger = structlog.get_logger()

_SPELLER_URL = "https://speller.yandex.net/services/spellservice.json/checkText"


def _get_client() -> AsyncOpenAI:
    api_key = settings.OPENROUTER_API_KEY or settings.ANTHROPIC_API_KEY
    if not api_key:
        return None
    return AsyncOpenAI(api_key=api_key, base_url=settings.OPENROUTER_BASE_URL)


_SYSTEM_PROMPT = """You are a search query corrector for an electronics price comparison website.

Your ONLY job: fix typos and normalize the query to the correct product/brand name for marketplace search.

KNOWN BRANDS (user may misspell these):
Phones: Samsung, Apple/iPhone, Xiaomi, Redmi, POCO, Huawei, Honor, OnePlus, Google Pixel, Nothing, Realme, vivo, OPPO, Motorola, ASUS, Sony
TVs: Samsung, LG, Sony, Hisense, TCL, Tuvio, Haier, Xiaomi, Philips, Horizont, Hi, BBK, Starwind, Hyundai, Dexp
Laptops: Apple/MacBook, Lenovo, ASUS, HP, Dell, Acer, MSI, Huawei, Honor, Xiaomi
Audio: Apple/AirPods, Samsung/Galaxy Buds, Sony, JBL, Marshall, Bose, Sennheiser, Beats
Vacuum/Home: Dyson, Roborock, Dreame, Xiaomi Mijia, Ecovacs, 360, iLife
Other: DJI, GoPro, PlayStation, Nintendo, Xbox, Steam Deck

SLANG & ABBREVIATIONS:
- "телек" = "телевизор"
- "ноут" = "ноутбук"
- "наушники TWS" = "беспроводные наушники"
- "макбук" = "MacBook"
- "айфон" = "iPhone"
- "самс" / "самсунг" = "Samsung"
- "сяоми" / "ксиоми" = "Xiaomi"
- "тувио" / "тавио" = "Tuvio"
- "хуавей" = "Huawei"
- "хонор" = "Honor"

Rules:
- Fix misspellings and recognize the closest brand from the list above
- Expand slang: "тавио телек" → "Tuvio телевизор", "сони наушники" → "Sony наушники"
- Add missing brand context when obvious: "s25 ultra" → "Samsung Galaxy S25 Ultra"
- Fix model names: "pra"/"пра" → "Pro", "ulrta" → "Ultra"
- Do NOT add extra words, descriptions, or explanations
- Do NOT change the meaning — if they want "iPhone 17 Pro", don't change to "iPhone 16 Pro"
- Do NOT substitute one brand for another. Dreame ≠ Roborock, Redmi ≠ Xiaomi, Honor ≠ Huawei — they are SEPARATE brands even if related
- Do NOT add a brand that is not in the query. Only add brand when the model name unambiguously identifies it (e.g. "s25" → Samsung, "airpods" → Apple). If unsure, leave as-is
- Remove marketing fluff words (мощный, новый, лучший, оригинальный, etc.) — keep only the product name
- If the query is already correct, return it unchanged
- Return ONLY the corrected query, nothing else — no quotes, no explanation

Examples:
- "ipone 17 pra" → "iPhone 17 Pro"
- "sams s25 ultra" → "Samsung Galaxy S25 Ultra"
- "сяоми 15 про" → "Xiaomi 15 Pro"
- "тавио телек" → "Tuvio телевизор"
- "redmi note 15 pro" → "Redmi Note 15 Pro"
- "airpods pro 3" → "AirPods Pro 3"
- "макбук эйр м4" → "MacBook Air M4"
- "дайсон пылесос" → "Dyson пылесос"
- "джибиэль колонка" → "JBL колонка"
- "Samsung Galaxy S25 Ultra" → "Samsung Galaxy S25 Ultra"
- "Мощный робот-пылесос Dreame BOT D9 MAX" → "Dreame Bot D9 Max"
- "робот-пылесос roborock s8" → "Roborock S8"
"""


async def correct_query(query: str) -> tuple[str, str | None]:
    """Correct typos in search query using AI.

    Returns:
        Tuple of (corrected_query, original_query_if_changed).
        If no corrections needed, returns (query, None).
    """
    if not query or len(query) < 2:
        return query, None

    # Try AI correction first
    corrected = await _ai_correct(query)
    if corrected and corrected.lower() != query.lower():
        logger.info("query_ai_corrected", original=query, corrected=corrected)
        return corrected, query

    # Fallback to Yandex Speller
    corrected = await _speller_correct(query)
    if corrected and corrected != query:
        logger.info("query_speller_corrected", original=query, corrected=corrected)
        return corrected, query

    return query, None


async def _ai_correct(query: str) -> str | None:
    """Use AI to correct the query."""
    try:
        client = _get_client()
        if not client:
            return None

        response = await client.chat.completions.create(
            model=settings.AI_MODEL,
            max_tokens=60,
            temperature=0,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": query},
            ],
        )

        result = response.choices[0].message.content.strip()

        # Sanity check: absolute length cap only. The previous ratio-based
        # check (len(result) > len(query) * 3) silently killed legitimate
        # expansions of short abbreviations — e.g. "пс5" (3 chars) → "PlayStation 5"
        # (13 chars, ratio 4.3x, rejected) — forcing short slang queries to go
        # to scrapers unchanged. 150 chars is enough to catch hallucinated
        # rambling responses while allowing any reasonable brand expansion.
        if not result or len(result) > 150:
            return None

        # Remove quotes if AI wrapped in them
        if (result.startswith('"') and result.endswith('"')) or (
            result.startswith("'") and result.endswith("'")
        ):
            result = result[1:-1].strip()

        return result

    except Exception as e:
        logger.debug("ai_correct_error", error=str(e))
        return None


async def _speller_correct(query: str) -> str | None:
    """Fallback: Yandex Speller for simple typos."""
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(
                _SPELLER_URL,
                params={"text": query, "lang": "ru,en"},
            )
            if r.status_code != 200:
                return None

            corrections = r.json()
            if not corrections:
                return None

            corrected = query
            for fix in reversed(corrections):
                if fix.get("s"):
                    suggestion = fix["s"][0]
                    pos = fix["pos"]
                    length = fix["len"]
                    corrected = corrected[:pos] + suggestion + corrected[pos + length :]

            return corrected if corrected != query else None

    except Exception as e:
        logger.debug("speller_error", error=str(e))
        return None
