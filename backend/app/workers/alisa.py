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
from urllib.parse import urlparse, urlunparse


def _normalize_product_url(url: str) -> str:
    """Strip tracking query-string / fragments. Alisa chokes on Ozon ?at=... tokens."""
    try:
        p = urlparse(url.strip())
        if not p.scheme:
            p = urlparse("https://" + url.strip())
        return urlunparse((p.scheme, p.netloc, p.path.rstrip("/") + "/", "", "", ""))
    except Exception:
        return url


import structlog
from playwright.async_api import Page, async_playwright


logger = structlog.get_logger()


# Regex reused across frames. The WS payload arrives as JSON text where
# `json_data` values are JSON strings with `\"` escaped quotes — hence `\\\"`.
_QUERY_RX = re.compile(r'\\"Query\\":\s*\\"([^"\\]{3,80})\\"')
_REJECTION_RX = re.compile(
    r'"text":"[^"]*(?:'
    r"не поддерживается|"
    r"не могу найти похожие|"
    r"не умею искать|"
    r"пока не умею|"
    r"Поищем что-то другое|"
    r"товары 18\+|"
    r"нет в продаже"
    r')[^"]*'
)


def _iter_json_data_payloads(payload: str):
    """Yield parsed dicts from every ``"json_data":"<escaped-json>"`` blob in frame.

    Alisa's rich_uicard offers arrive as an escaped JSON string under the
    ``json_data`` key. Field order inside that inner JSON is not stable — in
    particular the source (Ozon) offer has ``url`` before ``price`` while
    competitor offers have it after — so regex windowing misses half of them.
    Parsing each blob as JSON sidesteps ordering entirely.
    """
    idx = 0
    n = len(payload)
    needle = '"json_data":"'
    while True:
        pos = payload.find(needle, idx)
        if pos == -1:
            return
        start = pos + len(needle)
        i = start
        while i < n:
            c = payload[i]
            if c == "\\":
                i += 2
                continue
            if c == '"':
                break
            i += 1
        inner = payload[start:i]
        idx = i + 1
        try:
            unescaped = json.loads('"' + inner + '"')
            obj = json.loads(unescaped)
        except Exception:
            continue
        if isinstance(obj, dict):
            yield obj
            # EAliceOfferList bundles many merchant offers under offerList[];
            # each item has the same shape as an individual offer card.
            inner_list = obj.get("offerList")
            if isinstance(inner_list, list):
                for it in inner_list:
                    if isinstance(it, dict):
                        yield it


@dataclass
class AlisaOffer:
    domain: str
    price: float
    product_name: str | None = None
    img_url: str | None = None
    product_url: str | None = None
    rating: float | None = None
    review_cnt: int | None = None
    old_price: float | None = None
    discount_pct: int | None = None
    discount_end_ts: int | None = None
    shop_text: str | None = None
    delivery_methods: list[str] = field(default_factory=list)
    has_split: bool = False
    has_yapay: bool = False
    is_crossborder: bool = False
    is_adv: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "price": self.price,
            "product_name": self.product_name,
            "img_url": self.img_url,
            "product_url": self.product_url,
            "rating": self.rating,
            "review_cnt": self.review_cnt,
            "old_price": self.old_price,
            "discount_pct": self.discount_pct,
            "discount_end_ts": self.discount_end_ts,
            "shop_text": self.shop_text,
            "delivery_methods": self.delivery_methods,
            "has_split": self.has_split,
            "has_yapay": self.has_yapay,
            "is_crossborder": self.is_crossborder,
            "is_adv": self.is_adv,
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
    dialog_closed: bool = False  # True after DialogControl frame — Alisa finished streaming


async def _click_menu_item(page: Page) -> bool:
    """Open '+' attachments menu next to textarea then click 'Найти дешевле β'."""
    # Find the "+" button immediately adjacent to the textarea (same parent row)
    plus_clicked = False
    try:
        ta = page.locator("textarea").first
        ta_box = await ta.bounding_box()
        if ta_box:
            buttons = await page.locator("button").all()
            best = None
            best_dist = 1e9
            for b in buttons:
                try:
                    if not await b.is_visible():
                        continue
                    box = await b.bounding_box()
                    if not box or box["width"] > 60 or box["height"] > 60:
                        continue
                    # Same row as textarea (within 100px vertically below it)
                    dy = box["y"] - (ta_box["y"] + ta_box["height"])
                    if not (-20 <= dy <= 100):
                        continue
                    # Closest to the LEFT edge of textarea
                    dx = abs(box["x"] - ta_box["x"])
                    if dx < best_dist:
                        best_dist = dx
                        best = b
                except Exception:
                    continue
            if best is not None:
                await best.click(timeout=3000)
                plus_clicked = True
                logger.info("alisa.plus_clicked", method="dom-proximity")
    except Exception as e:
        logger.warning("alisa.plus_dom_search_failed", err=str(e))

    if not plus_clicked:
        # Coordinate fallback (UI-version-specific)
        try:
            await page.mouse.click(494, 453)
            await page.wait_for_timeout(800)
            plus_clicked = True
            logger.info("alisa.plus_clicked", method="coord")
        except Exception:
            pass

    if not plus_clicked:
        try:
            await page.screenshot(path="/tmp/alice_no_plus.png")
        except Exception:
            pass
        logger.warning("alisa.plus_button_not_found")
        return False

    await page.wait_for_timeout(1500)
    try:
        await page.screenshot(path="/tmp/alice_after_plus.png")
    except Exception:
        pass

    for _ in range(6):
        candidates = await page.locator(':text("Найти дешевле")').all()
        for cand in reversed(candidates):
            try:
                if not await cand.is_visible():
                    continue
                await cand.click(timeout=2000)
                await page.wait_for_timeout(1500)
                placeholder = await page.locator("textarea").first.get_attribute("placeholder")
                if placeholder and "ссылк" in placeholder.lower():
                    return True
            except Exception:
                continue
        await page.wait_for_timeout(500)
    try:
        await page.screenshot(path="/tmp/alice_no_cheaper.png")
    except Exception:
        pass
    return False


def _extract_from_payload(payload: str, result: AlisaResult) -> list[dict]:
    """Parse a single WS frame string, update `result` in-place, return new events."""
    events: list[dict] = []

    # Dialog-closed signal: DialogControl with update_time_last_read ONLY fires after
    # Alisa has streamed answer chunks. Note: DialogControl with enrich_with_full_info
    # appears at the START of the dialog (setup) and must NOT be treated as end-of-stream.
    # Multiple update_time_last_read frames may arrive as Alisa streams more chunks —
    # we mark dialog_closed on the first one, but _finalize still waits for a quiet
    # window of new-offer activity before actually exiting.
    if (
        '"name":"DialogControl"' in payload
        and "update_time_last_read" in payload
        and not result.dialog_closed
    ):
        result.dialog_closed = True
        events.append({"type": "dialog_closed", "data": {}})

    # Planned shops (arrive once at the start)
    shops_in_frame = set(_QUERY_RX.findall(payload))
    new_shops = [s for s in shops_in_frame if s not in result.planned_shops]
    if new_shops:
        result.planned_shops.extend(new_shops)
        events.append({"type": "planned_shops", "data": {"shops": result.planned_shops[:]}})

    for obj in _iter_json_data_payloads(payload):
        url_s = obj.get("url") if isinstance(obj.get("url"), str) else None
        price_obj = obj.get("price")
        price = None
        if isinstance(price_obj, dict):
            try:
                price = float(price_obj.get("value"))
            except (TypeError, ValueError):
                price = None

        product_name = obj.get("productName")
        if isinstance(product_name, str):
            product_name = product_name[:300]
        else:
            product_name = None
        img_url = obj.get("imgUrl") if isinstance(obj.get("imgUrl"), str) else None
        try:
            rating = float(obj["rating"]) if obj.get("rating") is not None else None
        except (TypeError, ValueError):
            rating = None
        rc_raw = obj.get("review_cnt", obj.get("reviewCnt", obj.get("reviewsCount")))
        try:
            review_cnt = int(rc_raw) if rc_raw is not None else None
        except (TypeError, ValueError):
            review_cnt = None

        # discount
        old_price = None
        discount_pct = None
        disc = obj.get("discount")
        if isinstance(disc, dict):
            try:
                old_price = (
                    float(disc.get("oldprice")) if disc.get("oldprice") is not None else None
                )
            except (TypeError, ValueError):
                old_price = None
            try:
                discount_pct = (
                    int(float(disc.get("percent"))) if disc.get("percent") is not None else None
                )
            except (TypeError, ValueError):
                discount_pct = None
        discount_end_ts = None
        det = obj.get("discountEndTimestamp")
        if isinstance(det, (int, float)):
            discount_end_ts = int(det) // (1000 if det > 10_000_000_000 else 1)

        # greenUrl.text ("OZON", "UPSTORE24") — shop display name
        shop_text = None
        if isinstance(gu := obj.get("greenUrl"), dict):
            t = gu.get("text")
            if isinstance(t, str) and t:
                shop_text = t[:80]

        # delivery methods
        delivery_methods: list[str] = []
        for d in obj.get("delivery") or []:
            if isinstance(d, dict):
                m = d.get("method")
                if isinstance(m, str) and m not in delivery_methods:
                    delivery_methods.append(m)

        # bnpl providers → has_split
        has_split = False
        for b in obj.get("bnpl") or []:
            if isinstance(b, dict) and b.get("provider") == "YANDEX_SPLIT":
                has_split = True
                break

        # Yandex Pay cashback
        has_yapay = False
        if isinstance(ci := obj.get("cashback_info"), dict):
            if ci.get("default_pay_type") == "YA_PAY_SYSTEM":
                has_yapay = True

        is_crossborder = bool(obj.get("isCrossborder"))
        is_adv = bool(obj.get("isAdv"))

        # Emit product_name on the first offer card we see
        if result.product_name is None and product_name:
            result.product_name = product_name
            result.product_img_url = img_url
            events.append(
                {
                    "type": "product_name",
                    "data": {"name": product_name, "img_url": img_url},
                }
            )

        if not (url_s and price):
            continue

        # Prefer greenUrl.domain (Alisa's canonical shop host) when present
        host = ""
        gu_top = obj.get("greenUrl")
        if isinstance(gu_top, dict):
            gu_domain = gu_top.get("domain")
            if isinstance(gu_domain, str):
                host = gu_domain.replace("www.", "").lower()
        if not host:
            try:
                host = (urlparse(url_s).hostname or "").replace("www.", "").lower()
            except Exception:
                host = ""
        if not host:
            continue

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
                old_price=old_price,
                discount_pct=discount_pct,
                discount_end_ts=discount_end_ts,
                shop_text=shop_text,
                delivery_methods=delivery_methods,
                has_split=has_split,
                has_yapay=has_yapay,
                is_crossborder=is_crossborder,
                is_adv=is_adv,
            )
            result.offers[host] = offer
            events.append({"type": "offer", "data": offer.to_dict()})
        else:
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
            if old_price is not None and existing.old_price is None:
                existing.old_price = old_price
                changed = True
            if discount_pct is not None and existing.discount_pct is None:
                existing.discount_pct = discount_pct
                changed = True
            if discount_end_ts is not None and existing.discount_end_ts is None:
                existing.discount_end_ts = discount_end_ts
                changed = True
            if shop_text and not existing.shop_text:
                existing.shop_text = shop_text
                changed = True
            if delivery_methods and not existing.delivery_methods:
                existing.delivery_methods = delivery_methods
                changed = True
            if has_split and not existing.has_split:
                existing.has_split = True
                changed = True
            if has_yapay and not existing.has_yapay:
                existing.has_yapay = True
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


async def _alisa_button_probe(page: Page) -> dict | None:
    """Probe visible buttons near the textarea: returns info for picking a stop/send selector.

    Strategy: find the textarea, look at all visible buttons within ~120px below/right of it.
    For each, collect aria-label, title, data-testid, class fragment, svg path signature,
    background-color (accent color is a strong stop-button tell in Alisa's UI).
    """
    try:
        return await page.evaluate(
            """
            () => {
              const ta = document.querySelector('textarea');
              if (!ta) return null;
              const trect = ta.getBoundingClientRect();
              const btns = Array.from(document.querySelectorAll('button'));
              const near = [];
              for (const b of btns) {
                const style = window.getComputedStyle(b);
                if (style.display === 'none' || style.visibility === 'hidden') continue;
                const r = b.getBoundingClientRect();
                if (r.width < 8 || r.height < 8) continue;
                // within +/- 200px vertically of textarea, and right/below it
                const dy = r.y - (trect.y + trect.height);
                const dx = r.x - trect.x;
                if (dy > 150 || dy < -200) continue;
                if (r.x < trect.x - 50) continue;
                const svgPaths = Array.from(b.querySelectorAll('svg path')).map(p => (p.getAttribute('d')||'').slice(0, 40));
                near.push({
                  aria: b.getAttribute('aria-label') || '',
                  title: b.getAttribute('title') || '',
                  testid: b.getAttribute('data-testid') || '',
                  cls: (b.className || '').toString().slice(0, 120),
                  bg: style.backgroundColor,
                  color: style.color,
                  text: (b.textContent || '').trim().slice(0, 40),
                  disabled: b.disabled,
                  x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
                  svg: svgPaths.slice(0, 2),
                });
              }
              // Sort by x desc (send/stop is usually rightmost)
              near.sort((a, b) => b.x - a.x);
              return {textarea: {x: Math.round(trect.x), y: Math.round(trect.y), w: Math.round(trect.width)}, buttons: near.slice(0, 8)};
            }
            """
        )
    except Exception:
        return None


async def _is_alisa_idle(page: Page) -> bool | None:
    """Check Alisa's oknyx button aria-label.

    During generation: aria-label="Алиса, стоп" (button lets you interrupt).
    When idle:         aria-label="Алиса, начни слушать" (button starts voice input).

    Returns True if idle, False if streaming, None if we can't locate the button.
    """
    try:
        label = await page.evaluate(
            """
            () => {
              const el = document.querySelector('[data-testid="oknyx"]');
              return el ? (el.getAttribute('aria-label') || '') : null;
            }
            """
        )
        if not isinstance(label, str):
            return None
        low = label.lower()
        if "стоп" in low or "stop" in low:
            return False
        if "начни слуш" in low or "слушать" in low or "listen" in low:
            return True
        return None
    except Exception:
        return None


async def run_alisa(
    url: str,
    user_data_dir: str | None,
    on_event: callable,
    *,
    storage_state_path: str | None = None,
    edge_channel: str = "msedge",
    hard_timeout_sec: int = 900,
    stable_finish_sec: int = 600,
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
        import os as _os

        _dump_dir = "/tmp/ws_dump"
        _os.makedirs(_dump_dir, exist_ok=True)
        _frame_counter = [0]

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
                try:
                    idx = _frame_counter[0]
                    _frame_counter[0] += 1
                    with open(f"{_dump_dir}/frame_{idx:04d}.json", "w", encoding="utf-8") as f:
                        f.write(s)
                except Exception:
                    pass

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

            try:
                ph = await page.locator("textarea").first.get_attribute("placeholder")
                logger.info("alisa.menu_activated", placeholder=ph)
            except Exception:
                pass

            # Paste URL and send
            clean_url = _normalize_product_url(url)
            logger.info("alisa.url_normalized", orig=url, clean=clean_url)
            inp = page.locator("textarea").first
            logger.info("alisa.textarea_click_start")
            await inp.click(timeout=10000)
            logger.info("alisa.textarea_click_done")
            await inp.fill(clean_url, timeout=10000)
            logger.info("alisa.textarea_filled", url_len=len(clean_url))
            try:
                await page.screenshot(path="/tmp/alice_filled.png")
            except Exception as e:
                logger.warning("alisa.screenshot_fail", step="filled", err=str(e))
            await inp.press("Enter")
            logger.info("alisa.enter_pressed")
            await page.wait_for_timeout(3000)
            try:
                await page.screenshot(path="/tmp/alice_after_send.png")
            except Exception as e:
                logger.warning("alisa.screenshot_fail", step="after_send", err=str(e))

            start = time.monotonic()
            last_frame_count = 0
            stable_since = time.monotonic()
            last_debug_shot = 0.0
            dom_idle_hits = 0

            while time.monotonic() - start < hard_timeout_sec:
                await page.wait_for_timeout(3000)

                elapsed = time.monotonic() - start
                if elapsed - last_debug_shot > 15:
                    try:
                        await page.screenshot(path=f"/tmp/alice_poll_{int(elapsed)}s.png")
                        last_debug_shot = elapsed
                    except Exception:
                        pass
                    logger.info(
                        "alisa.poll",
                        elapsed=int(elapsed),
                        frames=len(frames),
                        planned=len(result.planned_shops),
                        offers=len(result.offers),
                    )

                # Parse any new frames since last pass. Count "content" frames separately
                # from Ping/keepalive — Alisa sends Ping every ~5s, so treating *all* frames
                # as liveness means stable_finish never fires. A content frame is one that
                # carries actual dialog payload: Vins/DeferredAliceResponse, json_rephrase,
                # or rich offer cards (json_data).
                new_content_frames = 0
                while len(frames) > last_frame_count:
                    new_payload = frames[last_frame_count]
                    last_frame_count += 1
                    is_content = (
                        "DeferredAliceResponse" in new_payload
                        or "json_data" in new_payload
                        or "json_rephrase" in new_payload
                    )
                    if is_content:
                        new_content_frames += 1
                    events = _extract_from_payload(new_payload, result)
                    for ev in events:
                        await on_event(ev)
                if new_content_frames > 0:
                    stable_since = time.monotonic()

                result.frames_captured = len(frames)

                # rejection only aborts if we haven't found anything —
                # Alisa sometimes says "не поддерживается" mid-stream but still streams offers after.
                if result.rejected and not result.offers:
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

                # DOM idle signal — Alisa's oknyx button aria-label flips from "Алиса, стоп"
                # (streaming) to "Алиса, начни слушать" (idle) when she finishes speaking.
                # Require ≥1 offer, ≥30s since start, ≥60s since last content frame, and
                # 3 consecutive idle reads. The 60s WS-quiet gate avoids finishing in the
                # short pauses between offer batches that Alisa sometimes shows.
                if (
                    result.offers
                    and (time.monotonic() - start) > 30
                    and (time.monotonic() - stable_since) > 60
                ):
                    idle = await _is_alisa_idle(page)
                    logger.info(
                        "alisa.dom_idle_check",
                        idle=idle,
                        hits=dom_idle_hits,
                        elapsed=int(time.monotonic() - start),
                    )
                    if idle is True:
                        dom_idle_hits += 1
                    else:
                        dom_idle_hits = 0
                    if dom_idle_hits >= 3:
                        logger.info(
                            "alisa.dom_idle_finish",
                            offers=len(result.offers),
                            elapsed=int(time.monotonic() - start),
                        )
                        break
                else:
                    # Outside gating window — reset streak so a single earlier hit doesn't carry over
                    dom_idle_hits = 0

                # Stable finish: no new frames for stable_finish_sec + have offers
                if (time.monotonic() - stable_since) > stable_finish_sec and result.offers:
                    logger.info("alisa.stable_finish", offers=len(result.offers))
                    break

                # Silent-block finish: no WS frames at all after 45s → Alisa ignored us
                if result.frames_captured == 0 and (time.monotonic() - start) > 45:
                    logger.warning("alisa.silent_block", elapsed=int(time.monotonic() - start))
                    result.error = (
                        "Алиса не ответила на запрос — возможно, товар в неподдерживаемой "
                        "категории или сработал анти-бот. Попробуйте другой товар."
                    )
                    await on_event({"type": "error", "data": {"message": result.error}})
                    break

                # Planned shops arrived but no offers after 2 min → category has no competitors
                if result.planned_shops and not result.offers and (time.monotonic() - start) > 120:
                    logger.info(
                        "alisa.no_offers_finish",
                        planned=len(result.planned_shops),
                    )
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
