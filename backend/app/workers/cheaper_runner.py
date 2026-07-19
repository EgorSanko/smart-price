"""Cheaper search runner — polls DB for PENDING tasks, runs Alisa, publishes to Redis.

Run with:
    python -m app.workers.cheaper_runner

Environment:
    EDGE_USER_DATA_DIR — absolute path to Edge profile (must be logged into Yandex)
    REDIS_URL, DATABASE_URL — standard backend config

Single-worker for now (one browser = one job at a time). For scaling, run N processes
with different profiles — Alisa limits concurrent jobs per account.
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
from datetime import UTC, datetime
from pathlib import Path

import redis.asyncio as aioredis
import structlog
from sqlalchemy import select

from app.config import settings
from app.db.models.cheaper import CheaperSearch, CheaperStatus
from app.db.session import async_session_maker
from app.workers.alisa import AlisaResult, run_alisa


logger = structlog.get_logger()

# Default profile dir (Windows). Override via env.
DEFAULT_EDGE_DIR = str(Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data")
EDGE_USER_DATA_DIR = os.environ.get("EDGE_USER_DATA_DIR", DEFAULT_EDGE_DIR)
# On VPS: set ALISA_STORAGE_STATE=/app/session/yandex_storage.json to skip Edge profile.
ALISA_STORAGE_STATE = os.environ.get("ALISA_STORAGE_STATE") or None
ALISA_HEADLESS = os.environ.get("ALISA_HEADLESS", "false").lower() == "true"

POLL_INTERVAL_SEC = 5
_shutdown = asyncio.Event()


def _channel(task_id: str) -> str:
    return f"cheaper:task:{task_id}"


async def _claim_next_task() -> CheaperSearch | None:
    """Atomically pick oldest PENDING task and mark it RUNNING."""
    async with async_session_maker() as session:
        row = (
            await session.execute(
                select(CheaperSearch)
                .where(CheaperSearch.status == CheaperStatus.PENDING)
                .order_by(CheaperSearch.created_at.asc())
                .limit(1)
                .with_for_update(skip_locked=True)
            )
        ).scalar_one_or_none()
        if not row:
            return None
        row.mark_running()
        await session.commit()
        await session.refresh(row)
        return row


async def _finalize(task_id: str, result: AlisaResult) -> None:
    """Persist final state to DB."""
    async with async_session_maker() as session:
        row = (
            await session.execute(select(CheaperSearch).where(CheaperSearch.task_id == task_id))
        ).scalar_one_or_none()
        if not row:
            return
        if result.planned_shops:
            row.planned_shops = [{"domain": d} for d in result.planned_shops]
        merged: dict[str, dict] = {}
        for o in row.offers or []:
            d = o.get("domain")
            if d:
                merged[d] = o
        for o in result.offers.values():
            od = o.to_dict()
            d = od.get("domain")
            if not d:
                continue
            prev = merged.get(d)
            if prev is None or od.get("price", 1e18) <= prev.get("price", 1e18):
                merged[d] = od
        row.offers = sorted(merged.values(), key=lambda o: o.get("price", 1e18))
        if result.product_name and not row.product_name:
            row.product_name = result.product_name
        if result.product_img_url and not row.product_img_url:
            row.product_img_url = result.product_img_url
        if result.error:
            row.mark_failed(result.error)
        elif result.rejected:
            row.mark_failed("Rejected by Alisa (unsupported category)")
        else:
            row.mark_completed()
        await session.commit()


async def _persist_incremental(task_id: str, event: dict) -> None:
    """Mirror key events into the DB so a late WS-connect snapshot is non-empty."""
    etype = event.get("type")
    data = event.get("data") or {}
    if etype not in ("product_name", "planned_shops", "offer"):
        return
    async with async_session_maker() as session:
        row = (
            await session.execute(select(CheaperSearch).where(CheaperSearch.task_id == task_id))
        ).scalar_one_or_none()
        if not row:
            return
        if etype == "product_name":
            if data.get("name") and not row.product_name:
                row.product_name = data["name"][:300]
            if data.get("img_url") and not row.product_img_url:
                row.product_img_url = data["img_url"]
        elif etype == "planned_shops":
            shops = data.get("shops") or []
            row.planned_shops = [{"domain": d} for d in shops]
        elif etype == "offer":
            domain = data.get("domain")
            if not domain:
                return
            current = list(row.offers or [])
            replaced = False
            for i, o in enumerate(current):
                if o.get("domain") == domain:
                    if data.get("price", 1e18) <= o.get("price", 1e18):
                        current[i] = data
                    replaced = True
                    break
            if not replaced:
                current.append(data)
            current.sort(key=lambda o: o.get("price", 1e18))
            row.offers = current
        await session.commit()


async def _process(task: CheaperSearch, redis: aioredis.Redis) -> None:
    channel = _channel(task.task_id)
    logger.info("cheaper.worker.start", task_id=task.task_id, url=task.url)

    async def publish(event: dict) -> None:
        event.setdefault("task_id", task.task_id)
        try:
            await redis.publish(channel, json.dumps(event, ensure_ascii=False))
        except Exception as e:
            logger.warning("cheaper.worker.publish_failed", err=str(e))
        try:
            await _persist_incremental(task.task_id, event)
        except Exception as e:
            logger.warning("cheaper.worker.persist_failed", err=str(e))

    await publish({"type": "started", "data": {}})

    try:
        result = await run_alisa(
            url=task.url,
            user_data_dir=None if ALISA_STORAGE_STATE else EDGE_USER_DATA_DIR,
            on_event=publish,
            storage_state_path=ALISA_STORAGE_STATE,
            headless=ALISA_HEADLESS,
        )
    except Exception as e:
        logger.exception("cheaper.worker.run_failed", task_id=task.task_id)
        result = AlisaResult(error=f"{type(e).__name__}: {e}")
        await publish({"type": "error", "data": {"message": result.error}})

    await _finalize(task.task_id, result)
    await publish(
        {
            "type": "done",
            "data": {
                "offers": sorted(
                    [o.to_dict() for o in result.offers.values()], key=lambda o: o["price"]
                ),
                "planned_shops": result.planned_shops,
                "rejected": result.rejected,
                "error": result.error,
            },
        }
    )
    logger.info(
        "cheaper.worker.done",
        task_id=task.task_id,
        offers=len(result.offers),
        planned=len(result.planned_shops),
    )


async def main() -> None:
    logger.info("cheaper.runner.starting", edge_dir=EDGE_USER_DATA_DIR)

    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await redis.ping()
    except Exception as e:
        logger.error("cheaper.runner.redis_unreachable", url=settings.REDIS_URL, err=str(e))
        return

    while not _shutdown.is_set():
        try:
            task = await _claim_next_task()
        except Exception:
            logger.exception("cheaper.runner.claim_failed")
            await asyncio.sleep(POLL_INTERVAL_SEC)
            continue

        if task is None:
            try:
                await asyncio.wait_for(_shutdown.wait(), timeout=POLL_INTERVAL_SEC)
            except asyncio.TimeoutError:
                pass
            continue

        try:
            await _process(task, redis)
        except Exception:
            logger.exception("cheaper.runner.process_crashed", task_id=task.task_id)

    await redis.close()
    logger.info("cheaper.runner.stopped")


def _install_signal_handlers(loop: asyncio.AbstractEventLoop) -> None:
    def stop() -> None:
        _shutdown.set()

    if sys.platform != "win32":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _install_signal_handlers(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        _shutdown.set()
        loop.run_until_complete(asyncio.sleep(0.1))
    finally:
        loop.close()
