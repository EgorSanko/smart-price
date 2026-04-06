"""Wildberries marketplace scraper.

Uses the undocumented WB search API (v18).
Includes retry with exponential backoff for 429 rate limits.
"""

import asyncio
import random

import httpx
import structlog


logger = structlog.get_logger()

_WB_API_VERSIONS = ["v18", "v17", "v19", "v7"]

_WB_SEARCH_DOMAINS = ["search.wb.ru", "search.wildberries.ru"]
_WB_SEARCH_URL_TPL = "https://{domain}/exactmatch/ru/common/{version}/search"

HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Origin": "https://www.wildberries.ru",
    "Referer": "https://www.wildberries.ru/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) " "Gecko/20100101 Firefox/109.0"
    ),
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
    "бампер",
    "накладк",
    "защитн",
]

_BASKET_RANGES: list[tuple[int, str]] = [
    (143, "01"),
    (287, "02"),
    (431, "03"),
    (719, "04"),
    (1007, "05"),
    (1061, "06"),
    (1115, "07"),
    (1169, "08"),
    (1313, "09"),
    (1601, "10"),
    (1655, "11"),
    (1919, "12"),
    (2045, "13"),
    (2189, "14"),
    (2405, "15"),
    (2621, "16"),
    (2837, "17"),
    (3053, "18"),
    (3269, "19"),
    (3485, "20"),
    (3701, "21"),
    (3917, "22"),
    (4133, "23"),
    (4349, "24"),
    (4565, "25"),
    (4781, "26"),
    (5189, "27"),
    (5501, "28"),
    (5860, "29"),
    (6120, "30"),
    (6400, "31"),
    (6700, "32"),
    (7000, "33"),
    (7300, "34"),
    (7700, "35"),
    (7900, "36"),
    (8300, "37"),
    (8600, "38"),
]


def _is_accessory(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in ACCESSORY_KEYWORDS)


def _fmt_price(price_num: float) -> str:
    if price_num <= 0:
        return ""
    return f"{int(price_num):,}".replace(",", " ") + " ₽"


def _get_basket_number(vol: int) -> str:
    for max_vol, basket in _BASKET_RANGES:
        if vol <= max_vol:
            return basket
    return "39"


def _build_image_url(product_id: int) -> str:
    vol = product_id // 100_000
    part = product_id // 1_000
    basket = _get_basket_number(vol)
    basket_num = int(basket)
    # Newer baskets (17+) use wbcontent.net, older use wbbasket.ru
    domain = "wbcontent.net" if basket_num >= 17 else "wbbasket.ru"
    return (
        f"https://basket-{basket}.{domain}" f"/vol{vol}/part{part}/{product_id}/images/big/1.webp"
    )


def _extract_price(item: dict) -> float:
    """Extract price in rubles from WB product item.

    WB stores prices in different places depending on API version:
    - sizes[0].price.product (kopecks, v18+)
    - salePriceU (kopecks, older versions)
    """
    # Try sizes[].price.product first (v18 format)
    sizes = item.get("sizes", [])
    if sizes:
        price_obj = sizes[0].get("price", {})
        product_price = price_obj.get("product") or price_obj.get("total") or 0
        if product_price > 0:
            return float(product_price) / 100.0

    # Fallback to salePriceU
    raw = item.get("salePriceU") or item.get("priceU") or 0
    if raw > 0:
        return float(raw) / 100.0

    return 0.0


class WildberriesScraper:
    """Wildberries scraper using the public search API."""

    marketplace_name = "wildberries"
    region = "RU"
    currency = "RUB"

    async def _fetch_with_retry(self, params: dict, query: str) -> dict:
        """Try multiple API versions with exponential backoff on 429."""
        from app.config import settings

        proxy = settings.SCRAPER_PROXY or None

        for domain in _WB_SEARCH_DOMAINS:
            for version in _WB_API_VERSIONS:
                url = _WB_SEARCH_URL_TPL.format(domain=domain, version=version)

                for attempt in range(2):
                    try:
                        async with httpx.AsyncClient(
                            follow_redirects=True,
                            timeout=15,
                            proxy=proxy,
                        ) as client:
                            r = await client.get(url, params=params, headers=HEADERS)

                            if r.status_code == 200:
                                data = r.json()
                                if data:
                                    logger.info(
                                        "wb_search_ok",
                                        domain=domain,
                                        version=version,
                                        query=query,
                                        attempt=attempt,
                                    )
                                    return data

                            if r.status_code == 429:
                                wait = 1.5 + random.uniform(0.5, 1.5)
                                logger.warning(
                                    "wb_rate_limited",
                                    domain=domain,
                                    version=version,
                                    attempt=attempt,
                                    wait=wait,
                                )
                                await asyncio.sleep(wait)
                                continue

                            # Other error — try next version
                            logger.debug(
                                "wb_api_error",
                                domain=domain,
                                version=version,
                                status=r.status_code,
                            )
                            break

                    except Exception as e:
                        logger.debug("wb_fetch_error", domain=domain, version=version, error=str(e))
                        break

        return {}

    async def search(self, query: str) -> list[dict]:
        results: list[dict] = []
        try:
            params = {
                "appType": "1",
                "curr": "rub",
                "dest": "-1257786",
                "lang": "ru",
                "query": query,
                "resultset": "catalog",
                "sort": "popular",
                "spp": "30",
                "suppressSpellcheck": "false",
            }

            data = await self._fetch_with_retry(params, query)

            products = data.get("data", {}).get("products") or data.get("products") or []

            for item in products:
                try:
                    product_id = item.get("id")
                    if not product_id:
                        continue

                    product_id = int(product_id)
                    name = (item.get("name") or "").strip()
                    brand = (item.get("brand") or "").strip()

                    if not name:
                        continue

                    title = f"{brand} {name}".strip() if brand else name

                    if _is_accessory(title):
                        continue

                    # Filter out-of-stock items
                    # WB indicates stock via sizes[].stocks[] — if all sizes have
                    # empty stocks arrays, item is not actually purchasable
                    # (still shown in search with price, but clicking leads to OOS page)
                    sizes = item.get("sizes") or []
                    total_qty = item.get("totalQuantity", None)
                    if total_qty is not None and total_qty == 0:
                        continue
                    if sizes:
                        has_stock = False
                        for sz in sizes:
                            stocks = sz.get("stocks") or []
                            if stocks:
                                has_stock = True
                                break
                        if not has_stock:
                            continue

                    price_num = _extract_price(item)
                    if price_num <= 0:
                        continue

                    rating = item.get("rating", 0)
                    feedbacks = item.get("feedbacks", 0)

                    specs = ""
                    if rating:
                        specs = f"★ {rating}"
                        if feedbacks:
                            specs += f" ({feedbacks} отзывов)"

                    results.append(
                        {
                            "title": title,
                            "price": _fmt_price(price_num),
                            "price_num": price_num,
                            "url": f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
                            "marketplace": "wildberries",
                            "image": _build_image_url(product_id),
                            "shop": brand or "Wildberries",
                            "specs": specs,
                            "category": "",
                            "onliner_key": "",
                        }
                    )
                except Exception as exc:
                    logger.debug("wb_item_parse_skip", error=str(exc))

        except Exception as e:
            logger.error("wb_search_failed", error=str(e), query=query)

        return results
