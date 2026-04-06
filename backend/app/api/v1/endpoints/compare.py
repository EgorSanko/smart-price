"""Product comparison endpoints with SSE streaming via OpenRouter."""

import json
from collections.abc import AsyncGenerator

import structlog
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import settings


logger = structlog.get_logger()

router = APIRouter(prefix="/ai", tags=["ai"])

COMPARE_SYSTEM = """Ты — эксперт по сравнению электроники. Сравни товары по разделам.
Кратко и по делу. На русском. Эмодзи в заголовках.

## 💰 Цена
Где дешевле, разница

## 📊 Характеристики
Ключевые отличия: экран, процессор, камера, батарея, память

## ⭐ Отзывы
Рейтинг, плюсы, минусы

## 🏆 Вердикт
Кому какой. Чёткая рекомендация."""


class CompareRequest(BaseModel):
    products: list[dict]


def _build_compare_prompt(products: list[dict]) -> str:
    """Build comparison prompt from product data."""
    parts = []
    for i, p in enumerate(products, 1):
        s = f"### Товар {i}: {p.get('title', '?')}\n"
        prices = p.get("prices", [])
        if prices:
            s += "Цены:\n"
            for pr in prices[:6]:
                s += f"  - {pr.get('shop', '?')}: {pr.get('price', '?')}\n"
        det = p.get("onliner_details", {})
        if det:
            if det.get("price_min"):
                s += f"Диапазон: {det['price_min']:.2f}–{det.get('price_max', 0):.2f} BYN "
                s += f"({det.get('offers_count', 0)} предл.)\n"
        specs = p.get("specs", "") or det.get("description", "")
        if specs:
            s += f"Характеристики: {specs}\n"
        micro = det.get("micro_description", "")
        if micro:
            s += f"Детали: {micro}\n"
        rating = det.get("rating", 0)
        rc = det.get("reviews_count", 0)
        if rating:
            s += f"Рейтинг: {rating}/5 ({rc} отзывов)\n"
        reviews = p.get("reviews", [])
        if reviews:
            s += "Отзывы:\n"
            for rv in reviews[:5]:
                s += f"  [{rv.get('rating', '?')}/5] {rv['text'][:200]}\n"
        parts.append(s)
    return "Сравни:\n\n" + "\n---\n".join(parts)


@router.post("/compare")
async def compare_products(request: CompareRequest) -> StreamingResponse:
    """Compare products using AI analysis with SSE streaming."""
    products = request.products
    if len(products) < 2:
        return StreamingResponse(
            iter([f'data: {json.dumps({"error": "Need at least 2 products"})}\n\n']),
            media_type="text/event-stream",
        )

    # Enrich with Onliner details if keys available
    from app.scrapers.onliner import OnlinerScraper

    scraper = OnlinerScraper()
    for p in products:
        key = p.get("key") or p.get("onliner_key", "")
        if key:
            p["onliner_details"] = await scraper.get_product_details(key)
            p["reviews"] = await scraper.get_reviews(key, limit=8)

    prompt = _build_compare_prompt(products)

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            api_key = settings.OPENROUTER_API_KEY or settings.ANTHROPIC_API_KEY
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY is not set")
            client = AsyncOpenAI(
                api_key=api_key,
                base_url=settings.OPENROUTER_BASE_URL,
            )
            stream = await client.chat.completions.create(
                model=settings.AI_MODEL,
                max_tokens=2000,
                messages=[
                    {"role": "system", "content": COMPARE_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield f"data: {json.dumps({'text': delta.content}, ensure_ascii=False)}\n\n"
        except Exception as e:
            logger.error("compare_error", error=str(e))
            yield f'data: {json.dumps({"text": "Ошибка сравнения"})}\n\n'
        yield f'data: {json.dumps({"done": True})}\n\n'

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
