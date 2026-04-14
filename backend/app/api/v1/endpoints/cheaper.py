"""Endpoints for "Найти дешевле" — POST to start, GET to poll, WS to stream.

Worker (Phase 3) publishes events to Redis channel `cheaper:task:{task_id}`:
    {"type": "planned_shops", "data": {"shops": [...]}}
    {"type": "offer", "data": {"domain": "...", "price": ...}}
    {"type": "progress", "data": {"checking": "dns-shop.ru", "checked": 5, "total": 26}}
    {"type": "done", "data": {}}
    {"type": "error", "data": {"message": "..."}}
"""

from __future__ import annotations

import asyncio
import json
from urllib.parse import urlparse

import redis.asyncio as aioredis
import structlog
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select

from app.api.v1.deps import DbSession, OptionalUser
from app.config import settings
from app.db.models.cheaper import CheaperSearch, CheaperStatus
from app.db.session import async_session_maker
from app.schemas.cheaper import (
    CheaperSearchCreated,
    CheaperSearchRequest,
    CheaperSearchResult,
    Offer,
    PlannedShop,
)


logger = structlog.get_logger()

router = APIRouter(prefix="/cheaper", tags=["cheaper"])


def _redis_channel(task_id: str) -> str:
    return f"cheaper:task:{task_id}"


def _row_to_result(row: CheaperSearch) -> CheaperSearchResult:
    return CheaperSearchResult(
        task_id=row.task_id,
        status=row.status,
        url=row.url,
        orig_domain=row.orig_domain,
        product_name=row.product_name,
        product_img_url=row.product_img_url,
        orig_price=row.orig_price,
        currency=row.currency,
        planned_shops=[PlannedShop(**s) for s in (row.planned_shops or [])],
        offers=[Offer(**o) for o in (row.offers or [])],
        error=row.error,
        created_at=row.created_at,
        started_at=row.started_at,
        finished_at=row.finished_at,
    )


@router.post("/search", response_model=CheaperSearchCreated, status_code=status.HTTP_202_ACCEPTED)
async def create_search(
    payload: CheaperSearchRequest,
    db: DbSession,
    user: OptionalUser,
) -> CheaperSearchCreated:
    """Queue a new "найти дешевле" task and return the task_id.

    The Playwright worker (Phase 3) picks it up from the DB or a Celery queue.
    """
    url_str = str(payload.url)
    try:
        domain = urlparse(url_str).hostname or ""
        domain = domain.replace("www.", "")
    except Exception:
        domain = ""

    row = CheaperSearch(
        url=url_str,
        orig_domain=domain or None,
        user_id=user.id if user else None,
        status=CheaperStatus.PENDING,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)

    # Phase 3 will push task to Celery/Redis here.
    # For now the worker polls PENDING rows.
    logger.info(
        "cheaper.search.created", task_id=row.task_id, url=url_str, user=user.id if user else None
    )

    return CheaperSearchCreated(task_id=row.task_id, status=row.status)


@router.get("/{task_id}", response_model=CheaperSearchResult)
async def get_search(task_id: str, db: DbSession) -> CheaperSearchResult:
    """Poll current state of a search (for fallback when WS is unavailable)."""
    row = (
        await db.execute(select(CheaperSearch).where(CheaperSearch.task_id == task_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return _row_to_result(row)


@router.websocket("/ws/{task_id}")
async def ws_search(websocket: WebSocket, task_id: str) -> None:
    """Live stream of task events.

    Protocol: server pushes JSON messages matching CheaperEvent. Client sends nothing.
    On connect, we first send a snapshot (current DB row) then subscribe to pubsub.
    Connection closes when status becomes terminal (completed/failed/cancelled).
    """
    await websocket.accept()

    # 1. Snapshot current state
    async with async_session_maker() as session:
        row = (
            await session.execute(select(CheaperSearch).where(CheaperSearch.task_id == task_id))
        ).scalar_one_or_none()
    if not row:
        await websocket.send_json(
            {"type": "error", "task_id": task_id, "data": {"message": "Task not found"}}
        )
        await websocket.close()
        return

    await websocket.send_json(
        {
            "type": "snapshot",
            "task_id": task_id,
            "data": _row_to_result(row).model_dump(mode="json"),
        }
    )

    if row.status in (CheaperStatus.COMPLETED, CheaperStatus.FAILED, CheaperStatus.CANCELLED):
        await websocket.close()
        return

    # 2. Subscribe to Redis pubsub for live events
    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    channel = _redis_channel(task_id)
    await pubsub.subscribe(channel)

    async def client_listener() -> None:
        """Drain client messages so we notice disconnects."""
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass

    listener_task = asyncio.create_task(client_listener())

    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            try:
                event = json.loads(message["data"])
            except json.JSONDecodeError:
                continue
            await websocket.send_json(event)
            if event.get("type") in ("done", "error"):
                break
    except WebSocketDisconnect:
        pass
    finally:
        listener_task.cancel()
        try:
            await pubsub.unsubscribe(channel)
        except Exception:
            pass
        await pubsub.close()
        await r.close()
        try:
            await websocket.close()
        except Exception:
            pass
