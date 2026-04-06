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


logger = structlog.get_logger()

_FILTER_PROMPT = """You are a product relevance filter for a price comparison website.

USER QUERY: "{query}"

Below is a list of products found by marketplace scrapers. Your job:
Return ONLY the numbers of products that MATCH the user's query.

Rules:
- Match the EXACT product the user is looking for
- "Samsung Galaxy S25 Ultra" → only S25 Ultra, NOT S25, S25 FE, S25+, S24, A25, cases, cables
- "Cactus Moto Expert 100" (projector screen) → only projector screens by Cactus, NOT printer ink, cartridges
- "Tuvio телевизор 55" → only Tuvio TVs ~55 inch, NOT remotes, brackets, boards, cables
- "iPhone 17 Pro" → only iPhone 17 Pro, NOT iPhone 17, iPhone 16 Pro, cases, chargers
- Accessories (cases, cables, chargers, mounts, brackets, screen protectors) are NOT the main product
- Spare parts (boards, matrices, flex cables, power supplies) are NOT the main product
- Fakes/clones at suspiciously low prices should be EXCLUDED
- If NOTHING matches, return empty array []

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

        # If AI filtered everything, return all (don't trust empty)
        return filtered if filtered else products

    except Exception as e:
        logger.error("ai_filter_error", error=str(e), query=query)
        # Fallback: return all products if AI fails
        return products
