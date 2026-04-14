"""Alisa "Найти дешевле" automation.

Reverse-engineered from Yandex Alice AI. Flow:
  1. Open https://alice.yandex.ru/ in Edge with a persistent user profile
  2. Click "+" menu → click "Найти дешевле β" (activates cheaper mode)
  3. Paste product URL into textarea, press Enter
  4. Listen to `wss://uniproxy.alice.yandex.ru/uni.ws` frames and parse:
     - `json_rephrase_items` → planned_shops
     - `EAliceOfferCard.json_data` → offers with prices
  5. Publish events to Redis pubsub as they arrive
  6. Finish when no new frames for 60s + at least one offer seen,
     or hard timeout at 10 min

Tested configurations:
  - Browser: Microsoft Edge (channel='msedge') — per user feedback
  - User data dir: C:/Users/egor3/AppData/Local/Microsoft/Edge/User Data (logged-in Yandex account)
  - Works for Ozon/WB/Yandex.Market product URLs; ~45% of categories return real competitors
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import structlog
from playwright.async_api import Page, async_playwright


logger = structlog.get_logger()


# Regex reused across frames. The WS payload arrives as JSON text where
# `json_data` values are JSON strings with `\"` escaped quotes — hence `\\\"`.
_QUERY_RX = re.compile(r'\\"Query\\":\s*\\"([^"\\]{3,80})\\"')
_OFFER_RX = re.compile(r'\\"url\\":\s*\\"(https[^\\]+?)\\"[\s\S]{0,2000}?\\"value\\":\s*([0-9.]+)')
_PRODUCT_NAME_RX = re.compile(r'\\"productName\\":\s*\\"((?:[^"\\]|\\.)+?)\\"')
_IMG_URL_RX = re.compile(r'\\"imgUrl\\":\s*\\"([^"\\]+?)\\"')
_RATING_RX = re.compile(r'\\"rating\\":\s*([0-9.]+)')
_REVIEW_CNT_RX = re.compile(r'\\"(?:reviewCnt|review_cnt|reviewsCount)\\":\s*([0-9]+)')
_OFFER_WINDOW = 3000  # chars to scan around a url+price match for side fields
_REJECTION_RX = re.compile(r'"text":"[^"]*(?:не поддержив|к сожалению|не удалось|товары 18\+)[^"]*')


@dataclass
class AlisaOffer:
    domain: str
    price: float
    product_name: str | None = None
    img_url: str | None = None
    product_url: str | None = None
    rating: float | None = None
    review_cnt: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "price": self.price,
            "product_name": self.product_name,
            "img_url": self.img_url,
            "product_url": self.product_url,
            "rating": self.rating,
            "review_cnt": self.review_cnt,
        }


@dataclass
class AlisaResult:
    planned_shops: list[str] = field(default_factory=list)
    offers: dict[str, AlisaOffer] = field(
        default_factory=dict
    )  # keyed by domain (lowest price wins)
    product_name: str | None = None
    product_img_url: str | None = None
    rejected: bool = False
    error: str | None = None
    frames_captured: int = 0


async def _click_menu_item(page: Page) -> bool:
    """Click '+' button then the 'Найти дешевле' menu item.

    Uses the coordinate click (570, 401) that proved reliable during reverse-engineering;
    falls back to text-based search if coordinates drift.
    """
    try:
        await page.locator('button[aria-label="Меню"]').first.click(timeout=5000)
    except Exception as e:
        logger.warning("alisa.menu_button_not_found", err=str(e))
        return False

    await page.wait_for_timeout(1500)

    # Primary: coordinate click (proven to work)
    await page.mouse.click(570, 401)
    await page.wait_for_timeout(1500)

    placeholder = await page.locator("textarea").first.get_attribute("placeholder")
    if placeholder and "ссылк" in placeholder.lower():
        return True

    # Fallback: text-based — find "Найти дешевле" with β label
    for _ in range(6):
        await page.wait_for_timeout(500)
        candidates = await page.locator(':text("Найти дешевле")').all()
        for cand in reversed(candidates):
            try:
                parent_text = await cand.locator("..").inner_text()
                if "β" in parent_text and await cand.is_visible():
                    await cand.click(timeout=1500)
                    await page.wait_for_timeout(1500)
                    placeholder = await page.locator("textarea").first.get_attribute("placeholder")
                    if placeholder and "ссылк" in placeholder.lower():
                        return True
            except Exception:
                continue
    return False


def _extract_from_payload(payload: str, result: AlisaResult) -> list[dict]:
    """Parse a single WS frame string, update `result` in-place, return new events."""
    events: list[dict] = []

    # Planned shops (arrive once at the start)
    shops_in_frame = set(_QUERY_RX.findall(payload))
    new_shops = [s for s in shops_in_frame if s not in result.planned_shops]
    if new_shops:
        result.planned_shops.extend(new_shops)
        events.append({"type": "planned_shops", "data": {"shops": result.planned_shops[:]}})

    # Product name — emit once per task
    if result.product_name is None:
        name_match = _PRODUCT_NAME_RX.search(payload)
        if name_match:
            pn = name_match.group(1).replace('\\"', '"').replace("\\\\", "\\")[:300]
            result.product_name = pn
            img_match = _IMG_URL_RX.search(payload)
            if img_match:
                result.product_img_url = img_match.group(1).replace("\\/", "/")
            events.append(
                {
                    "type": "product_name",
                    "data": {
                        "name": pn,
                        "img_url": result.product_img_url,
                    },
                }
            )

    # Offers (url + value pairs); scan a window around each match for extras
    for match in _OFFER_RX.finditer(payload):
        url_s = match.group(1)
        try:
            price = float(match.group(2))
            host = urlparse(url_s).hostname or ""
            host = host.replace("www.", "").lower()
            if not host:
                continue
        except Exception:
            continue

        window_start = max(0, match.start() - _OFFER_WINDOW)
        window_end = min(len(payload), match.end() + _OFFER_WINDOW)
        window = payload[window_start:window_end]

        img_m = _IMG_URL_RX.search(window)
        name_m = _PRODUCT_NAME_RX.search(window)
        rating_m = _RATING_RX.search(window)
        rev_m = _REVIEW_CNT_RX.search(window)

        img_url = img_m.group(1).replace("\\/", "/") if img_m else None
        product_name = (
            name_m.group(1).replace('\\"', '"').replace("\\\\", "\\")[:300] if name_m else None
        )
        rating = None
        if rating_m:
            try:
                rating = float(rating_m.group(1))
            except ValueError:
                pass
        review_cnt = None
        if rev_m:
            try:
                review_cnt = int(rev_m.group(1))
            except ValueError:
                pass

        existing = result.offers.get(host)
        if existing is None or price < existing.price:
            offer = AlisaOffer(
                domain=host,
                price=price,
                product_url=url_s,
                product_name=product_name,
                img_url=img_url,
                rating=rating,
                review_cnt=review_cnt,
            )
            result.offers[host] = offer
            events.append({"type": "offer", "data": offer.to_dict()})
        else:
            # Merge-in richer side data without overwriting the winning (lowest) price
            changed = False
            if product_name and not existing.product_name:
                existing.product_name = product_name
                changed = True
            if img_url and not existing.img_url:
                existing.img_url = img_url
                changed = True
            if rating is not None and existing.rating is None:
                existing.rating = rating
                changed = True
            if review_cnt is not None and existing.review_cnt is None:
                existing.review_cnt = review_cnt
                changed = True
            if changed:
                events.append({"type": "offer", "data": existing.to_dict()})

    if _REJECTION_RX.search(payload):
        result.rejected = True
        events.append(
            {
                "type": "error",
                "data": {"message": "Alisa rejected the product (unsupported category)"},
            }
        )

    return events


async def run_alisa(
    url: str,
    user_data_dir: str | None,
    on_event: callable,
    *,
    storage_state_path: str | None = None,
    edge_channel: str = "msedge",
    hard_timeout_sec: int = 600,
    stable_finish_sec: int = 60,
    headless: bool = False,
) -> AlisaResult:
    """Run one end-to-end "найти дешевле" search.

    Two auth modes:
      - user_data_dir set → launch_persistent_context (local Windows w/ Edge profile)
      - storage_state_path set → launch + new_context(storage_state=…) (Linux VPS)

    Args:
        url: Product URL to search.
        user_data_dir: Edge user profile directory. If None, uses storage_state_path.
        on_event: async callable invoked per parsed event (for Redis pubsub).
        storage_state_path: Path to exported cookies+localStorage JSON.
        edge_channel: Playwright channel, 'msedge' local / 'chromium' (None) on VPS.
        hard_timeout_sec: max wall-clock seconds before abort.
        stable_finish_sec: finish early if no new frames for this long AND ≥1 offer.
        headless: usually False — Alisa detects headless.
    """
    result = AlisaResult()
    frames: list[str] = []
    browser_instance = None

    async with async_playwright() as pw:
        if storage_state_path:
            browser_instance = await pw.chromium.launch(
                headless=headless,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            browser = await browser_instance.new_context(
                storage_state=storage_state_path,
                viewport={"width": 1440, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
                ),
            )
        else:
            browser = await pw.chromium.launch_persistent_context(
                user_data_dir,
                channel=edge_channel,
                headless=headless,
                viewport={"width": 1440, "height": 900},
                args=["--profile-directory=Default"],
            )
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1440, "height": 900})

        # Attach WS listener BEFORE navigating
        def on_ws(ws):
            if "uniproxy" not in ws.url:
                return

            def on_frame(payload):
                s = (
                    payload
                    if isinstance(payload, str)
                    else payload.decode("utf-8", errors="ignore")
                )
                frames.append(s)

            ws.on("framereceived", lambda d: on_frame(d))

        page.on("websocket", on_ws)

        try:
            await page.goto("https://alice.yandex.ru/", wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)

            # "Новый чат" if offered
            try:
                new_chat = page.locator('*:has-text("Новый чат")').first
                if await new_chat.is_visible(timeout=2000):
                    await new_chat.click()
                    await page.wait_for_timeout(1500)
            except Exception:
                pass

            if not await _click_menu_item(page):
                result.error = "Could not activate 'Найти дешевле' mode"
                await on_event({"type": "error", "data": {"message": result.error}})
                return result

            # Paste URL and send
            inp = page.locator("textarea").first
            await inp.click()
            await inp.fill(url)
            await inp.press("Enter")

            start = time.monotonic()
            last_frame_count = 0
            stable_since = time.monotonic()

            while time.monotonic() - start < hard_timeout_sec:
                await page.wait_for_timeout(3000)

                # Parse any new frames since last pass
                while len(frames) > last_frame_count:
                    new_payload = frames[last_frame_count]
                    last_frame_count += 1
                    events = _extract_from_payload(new_payload, result)
                    for ev in events:
                        await on_event(ev)
                    stable_since = time.monotonic()

                result.frames_captured = len(frames)

                if result.rejected:
                    break

                # Heartbeat progress event
                await on_event(
                    {
                        "type": "progress",
                        "data": {
                            "frames": result.frames_captured,
                            "planned": len(result.planned_shops),
                            "offers": len(result.offers),
                            "elapsed_sec": int(time.monotonic() - start),
                        },
                    }
                )

                # Stable finish: no new frames for stable_finish_sec + have offers
                if (time.monotonic() - stable_since) > stable_finish_sec and result.offers:
                    logger.info("alisa.stable_finish", offers=len(result.offers))
                    break

        except Exception as e:
            logger.exception("alisa.run_failed")
            result.error = f"{type(e).__name__}: {e}"
            await on_event({"type": "error", "data": {"message": result.error}})
        finally:
            try:
                await browser.close()
            except Exception:
                pass
            if browser_instance is not None:
                try:
                    await browser_instance.close()
                except Exception:
                    pass

    return result
