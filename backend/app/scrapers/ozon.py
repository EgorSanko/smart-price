"""Ozon marketplace scraper.

Uses Ozon's internal entrypoint-api.bx JSON endpoint.
Falls back to Apify actor if the API is blocked by Cloudflare.
Falls back to nodriver as last resort.
"""

import asyncio
import json
import re

import httpx
import structlog


logger = structlog.get_logger()

_OZON_API_URL = "https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2"

_PRICE_RE = re.compile(r"[\d]+")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://www.ozon.ru/",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

ACCESSORY_KEYWORDS = [
    "чехол",
    "кейс",
    "стекло",
    "пленка",
    "плёнка",
    "кабель",
    "зарядк",
    "ремешок",
    "адаптер",
    "подставк",
    "колонк",
    "держатель",
]


def _is_accessory(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in ACCESSORY_KEYWORDS)


def _parse_price(price_str: str | None) -> float:
    """Parse price string like '89 990 ₽' into float 89990.0."""
    if not price_str:
        return 0.0
    if isinstance(price_str, (int, float)):
        return float(price_str)
    digits = _PRICE_RE.findall(str(price_str))
    if not digits:
        return 0.0
    try:
        return float("".join(digits))
    except ValueError:
        return 0.0


def _fmt_price(price_num: float) -> str:
    if price_num <= 0:
        return ""
    return f"{int(price_num):,}".replace(",", " ") + " ₽"


class OzonScraper:
    """Ozon scraper: API → Apify actor → nodriver fallback."""

    marketplace_name = "ozon"
    region = "RU"
    currency = "RUB"

    async def search(self, query: str) -> list[dict]:
        results: list[dict] = []

        try:
            # 1. Try the internal JSON API first
            results = await self._search_via_api(query)
            if results:
                return results

            # 2. Fallback: Apify actor (bypasses Cloudflare)
            results = await self._search_via_apify(query)
            if results:
                return results

            # 3. Last resort: nodriver
            results = await self._search_via_browser(query)

        except Exception as e:
            logger.error("ozon_search_failed", error=str(e), query=query)

        return results

    async def _search_via_api(self, query: str) -> list[dict]:
        """Search via Ozon's internal entrypoint-api.bx endpoint."""
        results: list[dict] = []
        from app.config import settings

        proxy = settings.SCRAPER_PROXY or None

        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=15,
                http2=True,
                proxy=proxy,
            ) as client:
                r = await client.get(
                    _OZON_API_URL,
                    params={"url": f"/search/?text={query}&from_global=true"},
                    headers=HEADERS,
                )

                if r.status_code != 200:
                    logger.warning("ozon_api_status", status=r.status_code, query=query)
                    return []

                data = r.json()

            # Extract products from widgetStates
            widget_states = data.get("widgetStates", {})

            for key, value in widget_states.items():
                if "searchResultsV2" not in key:
                    continue

                if isinstance(value, str):
                    try:
                        state = json.loads(value)
                    except json.JSONDecodeError:
                        continue
                else:
                    state = value

                items = state.get("items", [])
                for item in items:
                    product = self._parse_api_item(item)
                    if product:
                        results.append(product)

                if results:
                    logger.info("ozon_api_ok", query=query, count=len(results))
                    return results

        except Exception as e:
            logger.debug("ozon_api_failed", error=str(e))

        return results

    async def _search_via_apify(self, query: str) -> list[dict]:
        """Search via Apify Ozon scraper actor (bypasses Cloudflare)."""
        from app.config import settings

        token = settings.APIFY_API_TOKEN
        if not token:
            logger.debug("ozon_apify_no_token")
            return []

        actor_id = "zen-studio~ozon-scraper-pro"
        run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs"

        run_input = {
            "query": query,
            "maxItems": 30,
            "proxyCountry": "RU",
        }

        try:
            async with httpx.AsyncClient(timeout=90) as client:
                # Start the actor run (synchronous mode — wait up to 60s)
                r = await client.post(
                    run_url,
                    json=run_input,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    params={"waitForFinish": 60},
                    timeout=90,
                )

                if r.status_code not in (200, 201):
                    logger.warning(
                        "ozon_apify_run_failed",
                        status=r.status_code,
                        body=r.text[:300],
                    )
                    return []

                run_data = r.json().get("data", {})
                status = run_data.get("status")
                dataset_id = run_data.get("defaultDatasetId")

                if not dataset_id:
                    logger.warning("ozon_apify_no_dataset", status=status)
                    return []

                # If still running, poll briefly
                if status not in ("SUCCEEDED", "FINISHED"):
                    run_id = run_data.get("id")
                    for _ in range(6):
                        await asyncio.sleep(10)
                        check = await client.get(
                            f"https://api.apify.com/v2/actor-runs/{run_id}",
                            headers={"Authorization": f"Bearer {token}"},
                        )
                        if check.status_code == 200:
                            st = check.json().get("data", {}).get("status")
                            if st in ("SUCCEEDED", "FINISHED"):
                                break
                            if st in ("FAILED", "ABORTED", "TIMED-OUT"):
                                logger.warning("ozon_apify_run_status", status=st)
                                return []

                # Fetch dataset items
                items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
                items_r = await client.get(
                    items_url,
                    headers={"Authorization": f"Bearer {token}"},
                    params={"format": "json", "limit": 30},
                )

                if items_r.status_code != 200:
                    logger.warning("ozon_apify_dataset_failed", status=items_r.status_code)
                    return []

                items = items_r.json()
                if not isinstance(items, list):
                    items = []

                results = []
                for item in items:
                    product = self._parse_apify_item(item)
                    if product:
                        results.append(product)

                if results:
                    logger.info("ozon_apify_ok", query=query, count=len(results))

                return results

        except Exception as e:
            logger.error("ozon_apify_error", error=str(e), query=query)
            return []

    def _parse_apify_item(self, item: dict) -> dict | None:
        """Parse a product from Apify Ozon actor output."""
        title = (item.get("title") or item.get("name") or item.get("productName") or "").strip()

        if not title:
            return None

        if _is_accessory(title):
            return None

        # Price — Apify actors return various formats
        price_num = 0.0
        for key in ("price", "finalPrice", "currentPrice", "salePrice"):
            val = item.get(key)
            if val:
                price_num = _parse_price(val)
                if price_num > 0:
                    break

        if price_num <= 0:
            return None

        # URL
        url = item.get("url") or item.get("link") or ""
        if url and not url.startswith("http"):
            url = f"https://www.ozon.ru{url}"

        product_id = str(item.get("id") or item.get("productId") or "")
        if not url and product_id:
            url = f"https://www.ozon.ru/product/{product_id}"

        # Image
        image = ""
        img = item.get("image") or item.get("imageUrl") or item.get("mainImage")
        if isinstance(img, str):
            image = img
        elif isinstance(img, list) and img:
            image = img[0] if isinstance(img[0], str) else ""

        # Rating
        rating = item.get("rating", 0)
        reviews = item.get("reviewsCount") or item.get("feedbackCount") or 0

        specs = ""
        if rating:
            specs = f"★ {rating}"
            if reviews:
                specs += f" ({reviews} отзывов)"

        return {
            "title": title,
            "price": _fmt_price(price_num),
            "price_num": price_num,
            "url": url,
            "marketplace": "ozon",
            "image": image,
            "shop": "Ozon",
            "specs": specs,
            "category": "",
            "onliner_key": "",
        }

    def _parse_api_item(self, item: dict) -> dict | None:
        """Parse a product from Ozon's JSON API response."""
        title = None
        price_num = 0.0

        main_state = item.get("mainState", [])
        for block in main_state:
            atom = block.get("atom", {})
            atom_type = atom.get("type", "")

            if atom_type == "title":
                text_atom = atom.get("textAtom", {})
                title = text_atom.get("text", "")

            elif atom_type == "price":
                price_atom = atom.get("priceAtom", {})
                price_num = _parse_price(price_atom.get("price"))

        if not title:
            title = item.get("name") or item.get("title") or ""

        if not price_num:
            price_num = _parse_price(item.get("finalPrice") or item.get("price") or "")

        if not title or not price_num:
            return None

        if _is_accessory(title):
            return None

        product_id = str(item.get("id", ""))

        image = ""
        tile_image = item.get("tileImage")
        if isinstance(tile_image, dict):
            image = tile_image.get("url", "")
        elif isinstance(tile_image, str):
            image = tile_image

        rating = item.get("rating", 0)
        reviews = item.get("reviewsCount") or item.get("feedbackCount") or 0

        specs = ""
        if rating:
            specs = f"★ {rating}"
            if reviews:
                specs += f" ({reviews} отзывов)"

        return {
            "title": title.strip(),
            "price": _fmt_price(price_num),
            "price_num": price_num,
            "url": f"https://www.ozon.ru/product/{product_id}" if product_id else "",
            "marketplace": "ozon",
            "image": image,
            "shop": "Ozon",
            "specs": specs,
            "category": "",
            "onliner_key": "",
        }

    async def _search_via_browser(self, query: str) -> list[dict]:
        """Fallback: use nodriver (undetectable Chrome) to render Ozon."""
        results: list[dict] = []

        try:
            import nodriver as uc
        except ImportError:
            logger.debug("ozon_nodriver_not_available")
            return []

        browser = None
        try:
            browser = await uc.start(headless=True)
            page = await browser.get(f"https://www.ozon.ru/search/?text={query}&from_global=true")

            await page.sleep(5)

            source = await page.get_content()

            if not source or "captcha" in source.lower():
                logger.warning("ozon_nodriver_blocked", query=query)
                browser.stop()
                return []

            import re as _re

            for state_match in _re.finditer(r'data-state="([^"]+)"', source):
                raw = state_match.group(1)
                decoded = (
                    raw.replace("&quot;", '"')
                    .replace("&amp;", "&")
                    .replace("&lt;", "<")
                    .replace("&gt;", ">")
                )
                try:
                    state = json.loads(decoded)
                except (json.JSONDecodeError, ValueError):
                    continue

                items = state.get("items", [])
                for item in items:
                    product = self._parse_api_item(item)
                    if product:
                        results.append(product)

                if results:
                    break

            if not results:
                for script_match in _re.finditer(r'"widgetStates"\s*:\s*(\{[^}]+\})', source):
                    try:
                        ws = json.loads(script_match.group(1))
                        for k, v in ws.items():
                            if "searchResultsV2" in k:
                                state = json.loads(v) if isinstance(v, str) else v
                                for item in state.get("items", []):
                                    product = self._parse_api_item(item)
                                    if product:
                                        results.append(product)
                                if results:
                                    break
                    except (json.JSONDecodeError, ValueError):
                        continue

            if results:
                logger.info("ozon_nodriver_ok", query=query, count=len(results))

        except Exception as e:
            logger.error("ozon_nodriver_failed", error=str(e), query=query)
        finally:
            if browser:
                try:
                    browser.stop()
                except Exception:
                    pass

        return results
