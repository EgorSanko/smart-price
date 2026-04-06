"""AI chat endpoints with SSE streaming."""

import json
from collections.abc import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    region: str = "all"
    products_context: str = ""


@router.post("")
async def chat(request: ChatRequest) -> StreamingResponse:
    """AI chat with ЕГОРУШКА via Server-Sent Events.

    Events format (compatible with frontend):
    - {"text": "..."} — text chunk
    - {"searching": true, "query": "..."} — tool search started
    - {"products": [...]} — product results
    - {"done": true} — conversation complete
    """
    from app.agents.shopping_agent import ShoppingAgent
    from app.scrapers.manager import search_all

    # Force user's region — don't trust AI's region parameter
    user_region = request.region

    async def search_fn(query: str, region: str, max_price: float | None) -> list[dict]:
        # Use user's selected region, not AI's guess
        effective_region = user_region if user_region != "all" else region
        return await search_all(query, effective_region, max_price)

    agent = ShoppingAgent(search_fn=search_fn)

    async def event_stream() -> AsyncGenerator[str, None]:
        async for event in agent.chat(
            message=request.message,
            history=request.history,
            context=request.products_context,
            region=request.region,
        ):
            # Convert agent events to frontend-compatible format
            evt_type = event.get("type")
            if evt_type == "text":
                yield f"data: {json.dumps({'text': event['content']}, ensure_ascii=False)}\n\n"
            elif evt_type == "searching":
                yield f"data: {json.dumps({'searching': True, 'query': event.get('query', '')}, ensure_ascii=False)}\n\n"
            elif evt_type == "products":
                yield f"data: {json.dumps({'products': event['items']}, ensure_ascii=False)}\n\n"
            elif evt_type == "done":
                yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
