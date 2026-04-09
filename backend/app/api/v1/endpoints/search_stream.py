"""Live search endpoints with SSE streaming (real-time marketplace scraping)."""

import asyncio
import json
from collections.abc import AsyncGenerator

import structlog
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.scrapers.ai_relevance_filter import ai_filter_relevant
from app.scrapers.category_extractor import filter_by_category
from app.scrapers.manager import get_parsers
from app.scrapers.query_corrector import correct_query
from app.services import cleanup


logger = structlog.get_logger()

router = APIRouter(prefix="/live-search", tags=["live-search"])


MP_DISPLAY = {
    "onliner": "Onliner",
    "yandex": "Яндекс Маркет",
    "wildberries": "Wildberries",
    "citilink": "Ситилинк",
    "regard": "Регард",
    "aliexpress": "AliExpress",
    "worlddevices": "World Devices",
    "oneclick": "1click",
    "biggeek": "BigGeek",
}


async def _scrape_one(marketplace: str, query: str) -> list[dict]:
    """Run a single scraper with error handling."""
    try:
        if marketplace == "onliner":
            from app.scrapers.onliner import OnlinerScraper

            return await OnlinerScraper().search(query)
        elif marketplace == "yandex":
            from app.scrapers.playwright_scrapers import YandexMarketPlaywright

            return await YandexMarketPlaywright().search(query)
        elif marketplace == "wildberries":
            from app.scrapers.playwright_scrapers import WildberriesPlaywright

            return await WildberriesPlaywright().search(query)
        elif marketplace == "citilink":
            from app.scrapers.playwright_scrapers import CitilinkPlaywright

            return await CitilinkPlaywright().search(query)
        elif marketplace == "regard":
            from app.scrapers.regard_http import RegardHttpScraper

            return await RegardHttpScraper().search(query)
        elif marketplace == "aliexpress":
            from app.scrapers.playwright_scrapers import AliExpressPlaywright

            return await AliExpressPlaywright().search(query)
        elif marketplace == "worlddevices":
            from app.scrapers.worlddevices_http import WorldDevicesHttpScraper

            return await WorldDevicesHttpScraper().search(query)
        elif marketplace == "oneclick":
            from app.scrapers.oneclick_http import OneclickHttpScraper

            return await OneclickHttpScraper().search(query)
        elif marketplace == "biggeek":
            from app.scrapers.biggeek_http import BigGeekHttpScraper

            return await BigGeekHttpScraper().search(query)
        else:
            return []
    except Exception as e:
        logger.error("scraper_error", marketplace=marketplace, query=query, error=str(e))
        return []


@router.get("/stream")
async def search_stream(
    q: str = Query(..., min_length=1, description="Search query"),
    region: str = Query("all", description="Region filter: BY, RU, all"),
) -> StreamingResponse:
    """Search products across marketplaces with SSE streaming progress."""

    async def event_stream() -> AsyncGenerator[str, None]:
        parsers = get_parsers(region)
        sources = [k for k, v in parsers.items() if v.get("enabled")]

        corrected_q, original_q = await correct_query(q)

        yield _sse({"status": "start", "query": corrected_q, "region": region, "sources": sources})

        if original_q:
            yield _sse(
                {
                    "status": "corrected",
                    "original": original_q,
                    "corrected": corrected_q,
                }
            )

        all_products: list[dict] = []

        tasks = {}
        for key in sources:
            name = MP_DISPLAY.get(key, key)
            yield _sse({"status": "parsing", "source": key, "name": name})
            tasks[key] = asyncio.create_task(_scrape_one(key, corrected_q))

        try:
            for key, task in tasks.items():
                name = MP_DISPLAY.get(key, key)
                try:
                    products = await asyncio.wait_for(task, timeout=60)
                    # Stage 1: Fast regex filter (instant, free)
                    try:
                        products = cleanup.fast_filter(products, corrected_q)
                    except Exception as filter_err:
                        logger.warning("fast_filter_error", source=key, error=str(filter_err))
                    all_products.extend(products)
                    yield _sse(
                        {
                            "status": "done",
                            "source": key,
                            "name": name,
                            "count": len(products),
                            "products": products,
                        }
                    )
                except Exception as e:
                    logger.error("scraper_task_error", source=key, error=str(e))
                    yield _sse(
                        {
                            "status": "done",
                            "source": key,
                            "name": name,
                            "count": 0,
                            "products": [],
                        }
                    )

            # Stage 2: price clustering on combined pool — drops cheap
            # accessory/game clusters when the query is for an expensive
            # device. Must run on the COMBINED list (per-source batches
            # are too small to detect bimodality). Symmetric with analyze.
            if all_products:
                all_products, cluster_meta = cleanup.cluster_filter_by_price(all_products)
                logger.info("live_search_cluster", query=corrected_q, **cluster_meta)

            # Stage 3: Symmetric category filter. Drops wrong-category items
            # the regex and cluster stages missed (e.g. cables/mounts that
            # mention the queried component name, games that share the
            # console name). Must run on the COMBINED pool — per-source
            # batches leak context between marketplaces and titles repeat,
            # so the in-memory cache inside filter_by_category shines at
            # the combined-pool level. Symmetric with the analyze pipeline.
            if all_products:
                try:
                    all_products, cat_meta = await filter_by_category(all_products, corrected_q)
                    logger.info("live_search_category", query=corrected_q, **cat_meta)
                except Exception as cat_err:
                    logger.warning("category_filter_error", error=str(cat_err))

            # Stage 4: AI filter as a second pass — handles within-category
            # model/variant mismatches (iPhone 14 vs 15, S24 vs S25). Must
            # not fail the stream.
            if all_products:
                try:
                    all_products = await ai_filter_relevant(all_products, corrected_q)
                except Exception as ai_err:
                    logger.warning("ai_filter_error", error=str(ai_err))

            all_products.sort(key=lambda x: x.get("price_num", 0))

            # Emit the FINAL combined-pool filtered list. Per-source `done`
            # events only ran through fast_filter — they still contain cheap
            # accessories/games the combined-pool stages later dropped. The
            # frontend must replace its accumulated list with this one so
            # the user sees the final, correct result. Without this the UI
            # shows ghost products (e.g. PS5 games leaking through for a
            # "PlayStation 5" query because Regard's per-source batch has
            # no bimodality to cluster on).
            yield _sse(
                {
                    "status": "complete",
                    "total": len(all_products),
                    "products": all_products,
                }
            )
        except asyncio.CancelledError:
            logger.info("sse_stream_cancelled", query=q)
            for task in tasks.values():
                task.cancel()
            raise
        except Exception as stream_err:
            # Any unhandled error inside the stream must still emit a terminal
            # event — otherwise EventSource hangs forever on the client.
            logger.error("sse_stream_error", query=q, error=str(stream_err))
            yield _sse(
                {
                    "status": "complete",
                    "total": len(all_products),
                    "error": "stream_aborted",
                }
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
