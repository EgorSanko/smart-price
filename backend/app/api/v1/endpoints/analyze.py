"""Price analysis SSE endpoint."""

import json

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.services.price_analyzer import PriceAnalyzer


router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.get("/stream")
async def analyze_stream(
    q: str = Query(..., min_length=2, max_length=200),
    region: str = Query("RU", pattern="^(BY|RU)$"),
) -> StreamingResponse:
    """Analyze the price of a product via SSE streaming.

    Events emitted (data: <json>):
    - {"status": "start", "query": ..., "region": ...}
    - {"status": "parsing", "sources": [...]}
    - {"status": "scraped", "total": N}
    - {"status": "stats", "stats": {...}}
    - {"status": "analyzing"}
    - {"status": "result", "payload": {...}}
    - {"status": "error", "message": "..."}  (on validation / not-enough-offers)
    """
    analyzer = PriceAnalyzer()

    async def event_stream():
        async for event in analyzer.stream(q, region):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
