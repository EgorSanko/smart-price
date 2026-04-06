"""Onliner.by marketplace scraper.

Uses httpx directly since Onliner exposes public JSON APIs.
No browser rendering or scrapling needed.

Onliner API endpoints:
- catalog.onliner.by/sdapi/catalog.api/search/products — product search
- catalog.onliner.by/sdapi/catalog.api/products/{key} — product details
- catalog.onliner.by/sdapi/shop.api/products/{key}/positions — shop prices
- catalog.onliner.by/sdapi/catalog.api/products/{key}/reviews — user reviews
- Prices in BYN (Belarusian rubles), returned as string amounts
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog


logger = structlog.get_logger()

# Onliner API endpoints
_SEARCH_API = "https://catalog.onliner.by/sdapi/catalog.api/search/products"
_PRODUCT_API = "https://catalog.onliner.by/sdapi/catalog.api/products"
_POSITIONS_API = "https://catalog.onliner.by/sdapi/shop.api/products"
_PRICES_HISTORY_API = "https://catalog.onliner.by/sdapi/catalog.api/products"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/html",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

# Keywords to filter out accessories from search results
_ACCESSORY_KEYWORDS = [
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
    "накладк",
    "бампер",
    "протектор",
    "стилус",
    "переходник",
    "хаб",
    "чистящ",
    "салфетк",
    "крепление",
    "штатив",
    "монопод",
    "селфи",
    "сумка",
    "рюкзак",
    "брелок",
    "strap",
    "case",
    "cover",
]


def _is_accessory(name: str) -> bool:
    """Check if the product name indicates it's an accessory."""
    name_lower = name.lower()
    return any(kw in name_lower for kw in _ACCESSORY_KEYWORDS)


def _fmt_price(price_num: float) -> str:
    """Format price in BYN."""
    if price_num <= 0:
        return ""
    return f"{price_num:,.2f} BYN".replace(",", " ")


class OnlinerScraper:
    """Scraper for onliner.by marketplace using public APIs."""

    marketplace_name = "onliner"
    region = "BY"
    currency = "BYN"

    async def search(self, query: str, *, max_results: int = 5) -> list[dict[str, Any]]:
        """Search Onliner catalog and return product dicts with shop prices.

        Returns list of dicts compatible with frontend format:
        {title, price, price_num, url, marketplace, image, shop, specs, onliner_key, ...}
        """
        results: list[dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                r = await client.get(
                    _SEARCH_API,
                    params={"query": query, "page": 1},
                    headers=_HEADERS,
                )
                if r.status_code != 200:
                    logger.warning("onliner_search_http_error", status=r.status_code)
                    return results

                data = r.json()
                products = data.get("products", [])

                for p in products[:max_results]:
                    try:
                        fn = p.get("full_name") or ""
                        if not fn or _is_accessory(fn):
                            continue

                        key = p.get("key", "")
                        if not key:
                            continue

                        url = p.get("html_url", "")
                        img = (p.get("images") or {}).get("header", "")
                        specs = p.get("description", "")
                        sch = p.get("schema") or {}
                        cat = sch.get("name", "")
                        catk = sch.get("key", "")

                        # Try to get shop positions (individual seller prices)
                        shop_results = await self._fetch_shop_prices(
                            client, key, fn, url, img, specs, cat, catk
                        )

                        if shop_results:
                            results.extend(shop_results)
                            continue

                        # Fallback: use min price from search results.
                        # prices/price_min/offers can all be None for discontinued items —
                        # must use `or {}` instead of dict default, otherwise .get() crashes.
                        pr = p.get("prices") or {}
                        mn = float((pr.get("price_min") or {}).get("amount", 0))
                        if mn > 0:
                            cnt = (pr.get("offers") or {}).get("count", 0)
                            results.append(
                                {
                                    "title": fn,
                                    "price": _fmt_price(mn),
                                    "price_num": mn,
                                    "url": url,
                                    "marketplace": "onliner",
                                    "image": img,
                                    "shop": f"{cnt} магазинов",
                                    "specs": specs,
                                    "category": cat,
                                    "category_key": catk,
                                    "onliner_key": key,
                                }
                            )
                    except Exception as item_err:
                        # One bad item must not drop the whole page of results.
                        logger.warning(
                            "onliner_search_item_error",
                            error=str(item_err),
                            product_key=p.get("key") if isinstance(p, dict) else None,
                        )
                        continue

        except Exception as e:
            logger.error("onliner_search_error", error=str(e))

        return results

    async def _fetch_shop_prices(
        self,
        client: httpx.AsyncClient,
        key: str,
        fn: str,
        url: str,
        img: str,
        specs: str,
        cat: str,
        catk: str,
        *,
        max_shops: int = 8,
    ) -> list[dict[str, Any]]:
        """Fetch individual shop prices for a product."""
        results: list[dict[str, Any]] = []
        try:
            r = await client.get(
                f"{_POSITIONS_API}/{key}/positions",
                headers=_HEADERS,
                timeout=10,
            )
            if r.status_code != 200:
                return results

            data = r.json()
            # Any of these can be None for out-of-stock products — use `or {}`.
            positions = (data.get("positions") or {}).get("primary") or []
            shops = data.get("shops") or {}
            seen_shops: set[str] = set()

            for pos in positions[:max_shops]:
                sid = str(pos.get("shop_id", ""))
                if sid in seen_shops:
                    continue
                seen_shops.add(sid)

                pa = float((pos.get("position_price") or {}).get("amount", 0))
                if pa <= 0:
                    continue

                sh = shops.get(sid) or {}
                sn = sh.get("title", "Магазин")
                rt = (sh.get("reviews") or {}).get("rating", 0)
                rs = f" ★{rt}" if rt else ""
                w = pos.get("warranty", 0)
                ws = f" • {w} мес." if w else ""

                shop_name = f"{sn}{rs}{ws}"

                results.append(
                    {
                        "title": fn,
                        "price": _fmt_price(pa),
                        "price_num": pa,
                        "url": url,
                        "marketplace": "onliner",
                        "image": img,
                        "shop": shop_name,
                        "specs": specs,
                        "category": cat,
                        "category_key": catk,
                        "onliner_key": key,
                    }
                )

        except Exception as e:
            logger.debug("onliner_positions_error", key=key, error=str(e))

        return results

    async def get_product_details(self, key: str) -> dict[str, Any]:
        """Fetch full product details from Onliner API."""
        info: dict[str, Any] = {}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{_PRODUCT_API}/{key}",
                    headers=_HEADERS,
                )
                if r.status_code == 200:
                    d = r.json()
                    info["full_name"] = d.get("full_name", "")
                    info["description"] = d.get("description", "")
                    info["micro_description"] = d.get("micro_description", "")
                    rv = d.get("reviews") or {}
                    info["reviews_count"] = rv.get("count", 0)
                    info["rating"] = rv.get("rating", 0)
                    pr = d.get("prices") or {}
                    info["price_min"] = float((pr.get("price_min") or {}).get("amount", 0))
                    info["price_max"] = float((pr.get("price_max") or {}).get("amount", 0))
                    info["offers_count"] = (pr.get("offers") or {}).get("count", 0)
        except Exception as e:
            logger.error("onliner_details_error", key=key, error=str(e))
        return info

    async def get_price_history(self, key: str) -> dict[str, Any]:
        """Fetch price history from Onliner's prices-history API.

        Returns dict with: chart_data (date/price pairs), prices (current/min/max), sale info.
        """
        result: dict[str, Any] = {"has_data": False}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{_PRICES_HISTORY_API}/{key}/prices-history",
                    headers=_HEADERS,
                )
                if r.status_code != 200:
                    logger.debug("onliner_history_not_found", key=key, status=r.status_code)
                    return result

                data = r.json()
                chart = data.get("chart_data", {})
                items = chart.get("items", [])
                currency = chart.get("currency", "BYN")
                prices_info = data.get("prices", {})

                # Build history array
                history = []
                for item in items:
                    price_str = item.get("price")
                    if price_str is not None:
                        history.append(
                            {
                                "date": item["date"],
                                "price": float(price_str),
                                "currency": currency,
                            }
                        )

                if not history:
                    return result

                prices = [h["price"] for h in history]
                result = {
                    "product_key": key,
                    "history": history,
                    "stats": {
                        "min": min(prices),
                        "max": max(prices),
                        "avg": round(sum(prices) / len(prices), 2),
                        "count": len(prices),
                        "current": float(prices_info.get("current", {}).get("amount", 0)),
                        "first_seen": history[0]["date"],
                        "last_seen": history[-1]["date"],
                    },
                    "has_data": True,
                }

        except Exception as e:
            logger.error("onliner_history_error", key=key, error=str(e))

        return result

    async def get_reviews(self, key: str, *, limit: int = 8) -> list[dict[str, Any]]:
        """Fetch product reviews from Onliner."""
        reviews: list[dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    f"{_PRODUCT_API}/{key}/reviews",
                    params={"order": "created_at:desc"},
                    headers=_HEADERS,
                )
                if r.status_code == 200:
                    for rv in r.json().get("reviews", [])[:limit]:
                        text = ""
                        for part in ("pros_text", "cons_text", "summary_text", "text"):
                            t = rv.get(part, "")
                            if t:
                                label = {
                                    "pros_text": "+",
                                    "cons_text": "-",
                                    "summary_text": "=",
                                    "text": "",
                                }.get(part, "")
                                text += f"{label}{t} "
                        if text.strip():
                            reviews.append(
                                {
                                    "text": text.strip()[:300],
                                    "rating": rv.get("rating", 0),
                                }
                            )
        except Exception as e:
            logger.error("onliner_reviews_error", key=key, error=str(e))
        return reviews
