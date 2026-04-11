"""Yandex Market scraper.

Method: httpx GET → regex extraction from JSON embedded in HTML.
Yandex embeds product data as JSON in the search HTML (~1.7 MB).
We find "skuId" anchors and extract title, price, productId, offerId
from surrounding chunks.
"""

import asyncio
import random
import re
from urllib.parse import quote_plus

import httpx
import structlog


logger = structlog.get_logger()

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


def _build_headers() -> dict[str, str]:
    ua = random.choice(_USER_AGENTS)
    chrome_ver_match = re.search(r"Chrome/(\d+)", ua)
    chrome_ver = chrome_ver_match.group(1) if chrome_ver_match else "124"
    return {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "max-age=0",
        "Referer": "https://market.yandex.ru/",
        "sec-ch-ua": f'"Chromium";v="{chrome_ver}", "Google Chrome";v="{chrome_ver}", "Not-A.Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
        if "Windows" in ua
        else ('"macOS"' if "Mac" in ua else '"Linux"'),
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "Connection": "keep-alive",
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
    "наушник",
    "колонк",
    "держатель",
]


def _is_accessory(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in ACCESSORY_KEYWORDS)


def _fmt_price(price_num: float) -> str:
    if price_num <= 0:
        return ""
    return "≈ " + f"{int(price_num):,}".replace(",", " ") + " ₽"


def _extract_image(chunk: str) -> str:
    """Extract image URL from a chunk of JSON/HTML."""
    patterns = [
        r'"picture"\s*:\s*"(https://avatars\.mds\.yandex\.net/[^"]+)"',
        r'"src"\s*:\s*"(https://avatars\.mds\.yandex\.net/[^"]+)"',
        r'"(?:entity|thumb|original)"\s*:\s*"(https://[^"]*avatars[^"]*mds\.yandex\.net[^"]+)"',
        r'"(https://avatars\.mds\.yandex\.net/get-mpic/\d+/[^"]+)"',
    ]
    for pat in patterns:
        m = re.search(pat, chunk)
        if m:
            url = m.group(1)
            if "/orig" not in url and "%" not in url:
                url = re.sub(r"/\d+x\d+", "/200x200", url)
            return url
    return ""


def _parse_products_from_html(html: str, *, query_is_accessory: bool = False) -> list[dict]:
    """Extract products from Yandex Market HTML using skuId anchors.

    Proven approach: find "skuId" in embedded JSON, grab ±1000 chars chunk,
    extract title, value (price), productId, offerId from the chunk.
    """
    results: list[dict] = []
    seen: set[str] = set()

    # --- Primary: skuId-based extraction ---
    for m in re.finditer(r'"skuId"\s*:\s*"(\d+)"', html):
        sku = m.group(1)
        if sku in seen:
            continue

        # Chunk: -500 before, +1500 after the match (wide range for context)
        s = max(0, m.start() - 500)
        e = min(len(html), m.end() + 1500)
        chunk = html[s:e]

        # Title
        title_m = re.search(r'"title"\s*:\s*"([^"]{15,120})"', chunk)
        if not title_m:
            title_m = re.search(r'"name"\s*:\s*"([^"]{15,120})"', chunk)

        # Price (value field in Yandex JSON)
        price_m = re.search(r'"value"\s*:\s*"(\d+)"', chunk)
        if not price_m:
            price_m = re.search(r'"price"\s*:\s*"?(\d{4,})"?', chunk)

        # Product ID and Offer ID for URL building
        pid_m = re.search(r'"productId"\s*:\s*"?(\d+)"?', chunk)
        offer_m = re.search(r'"offerId"\s*:\s*"([^"]+)"', chunk)

        if not title_m or not price_m:
            continue

        title = title_m.group(1)
        price_num = int(price_m.group(1))

        if price_num < 1000 or (not query_is_accessory and _is_accessory(title)):
            continue

        seen.add(sku)

        # Build URL — link to product+sku page (actual prices shown there)
        url = ""
        if pid_m:
            url = f"https://market.yandex.ru/product/{pid_m.group(1)}?sku={sku}"

        image = _extract_image(chunk)

        # Try to extract shop name from nearby context
        shop_name = "Яндекс Маркет"
        shop_m = re.search(r'"shopName"\s*:\s*"([^"]+)"', chunk)
        if not shop_m:
            shop_m = re.search(r'"supplierName"\s*:\s*"([^"]+)"', chunk)
        if shop_m:
            shop_name = shop_m.group(1)

        results.append(
            {
                "title": title,
                "price": _fmt_price(price_num),
                "price_num": price_num,
                "url": url,
                "marketplace": "yandex",
                "image": image,
                "shop": shop_name,
                "specs": "",
                "category": "",
                "onliner_key": "",
            }
        )

    # --- Fallback: productId-based extraction (if no skuId found) ---
    if not results:
        for m in re.finditer(r'"productId"\s*:\s*"?(\d+)"?', html):
            pid_val = m.group(1)
            if pid_val in seen:
                continue

            s = max(0, m.start() - 500)
            e = min(len(html), m.end() + 1500)
            chunk = html[s:e]

            title_m = re.search(r'"title"\s*:\s*"([^"]{15,120})"', chunk)
            if not title_m:
                title_m = re.search(r'"name"\s*:\s*"([^"]{15,120})"', chunk)

            price_m = re.search(r'"value"\s*:\s*"(\d+)"', chunk)
            if not price_m:
                price_m = re.search(r'"price"\s*:\s*"?(\d{4,})"?', chunk)

            sku_m = re.search(r'"skuId"\s*:\s*"(\d+)"', chunk)
            offer_m = re.search(r'"offerId"\s*:\s*"([^"]+)"', chunk)

            if not title_m or not price_m:
                continue

            title = title_m.group(1)
            price_num = int(price_m.group(1))

            if price_num < 1000 or _is_accessory(title):
                continue

            seen.add(pid_val)

            url = ""
            sku_part = f"?sku={sku_m.group(1)}" if sku_m else ""
            if pid_val:
                url = f"https://market.yandex.ru/product/{pid_val}{sku_part}"

            image = _extract_image(chunk)

            shop_name = "Яндекс Маркет"
            shop_m = re.search(r'"shopName"\s*:\s*"([^"]+)"', chunk)
            if not shop_m:
                shop_m = re.search(r'"supplierName"\s*:\s*"([^"]+)"', chunk)
            if shop_m:
                shop_name = shop_m.group(1)

            results.append(
                {
                    "title": title,
                    "price": _fmt_price(price_num),
                    "price_num": price_num,
                    "url": url,
                    "marketplace": "yandex",
                    "image": image,
                    "shop": shop_name,
                    "specs": "",
                    "category": "",
                    "onliner_key": "",
                }
            )

    return results


class YandexMarketScraper:
    """Yandex Market scraper using HTML parsing with nodriver fallback."""

    marketplace_name = "yandex"
    region = "RU"
    currency = "RUB"

    async def search(self, query: str) -> list[dict]:
        results: list[dict] = []
        _qia = _is_accessory(query)  # skip accessory filter when query IS accessory
        try:
            await asyncio.sleep(random.uniform(0.3, 1.2))

            from app.config import settings

            proxy = settings.SCRAPER_PROXY or None

            headers = _build_headers()
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=15,
                proxy=proxy,
            ) as client:
                r = await client.get(
                    f"https://market.yandex.ru/search?text={quote_plus(query)}",
                    headers=headers,
                )
                if r.status_code != 200:
                    logger.warning(
                        "yandex_bad_status",
                        status=r.status_code,
                        query=query,
                    )
                    return results

                html = r.text

                # Always try to parse if skuId is present in HTML,
                # even if captcha elements exist (Yandex often includes both)
                has_captcha = "captcha" in html.lower() or "showcaptcha" in html.lower()
                has_data = "skuId" in html or "productId" in html

                if has_captcha and not has_data:
                    logger.warning("yandex_captcha_only", query=query)
                    # Fall through to nodriver below
                else:
                    if has_captcha:
                        logger.info("yandex_captcha_with_data", query=query, html_size=len(html))
                    results = _parse_products_from_html(html, query_is_accessory=_qia)
                    if results:
                        logger.info("yandex_html_ok", query=query, count=len(results))

        except Exception as e:
            logger.error("yandex_search_failed", error=str(e), query=query)

        # If HTML scraping failed (captcha or empty), try nodriver
        if not results:
            results = await self._search_via_nodriver(query)

        return results

    async def _search_via_nodriver(self, query: str) -> list[dict]:
        """Fallback: use nodriver (undetectable Chrome) to bypass captcha."""
        try:
            import nodriver as uc
        except ImportError:
            logger.debug("yandex_nodriver_not_available")
            return []

        browser = None
        try:
            browser = await uc.start(headless=True)
            page = await browser.get(f"https://market.yandex.ru/search?text={quote_plus(query)}")

            # Wait for page to load (captcha auto-bypass by nodriver)
            await page.sleep(6)

            source = await page.get_content()
            if not source:
                return []

            # Check if still on captcha
            if "showcaptcha" in source.lower() and "skuId" not in source:
                logger.warning("yandex_nodriver_still_captcha", query=query)
                return []

            results = _parse_products_from_html(source, query_is_accessory=_is_accessory(query))
            if results:
                logger.info("yandex_nodriver_ok", query=query, count=len(results))
            return results

        except Exception as e:
            logger.error("yandex_nodriver_failed", error=str(e), query=query)
            return []
        finally:
            if browser:
                try:
                    browser.stop()
                except Exception:
                    pass
