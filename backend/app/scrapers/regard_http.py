"""Regard.ru HTTP scraper — fast SSR-based scraping without Playwright.

Regard.ru renders products server-side with Next.js SSR.
Products are available in Schema.org JSON-LD (OfferCatalog) and in HTML DOM.
No anti-bot protection — simple HTTP requests work perfectly.
"""

import json
import re

import httpx
import structlog


logger = structlog.get_logger()

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

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
]


def _is_accessory(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in _ACCESSORY_KEYWORDS)


def _fmt_price(price_num: float) -> str:
    if price_num <= 0:
        return ""
    return f"{int(price_num):,}".replace(",", " ") + " ₽"


class RegardHttpScraper:
    """Fast HTTP scraper for Regard.ru using Schema.org JSON-LD + HTML fallback."""

    marketplace_name = "regard"
    region = "RU"
    currency = "RUB"

    async def search(self, query: str, *, max_results: int = 15) -> list[dict]:
        results: list[dict] = []
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                r = await client.get(
                    "https://www.regard.ru/catalog",
                    params={"search": query},
                    headers=_HEADERS,
                )
                if r.status_code != 200:
                    logger.warning("regard_http_error", status=r.status_code)
                    return results

                html = r.text

                # Strategy 1: Parse Schema.org JSON-LD (OfferCatalog)
                results = self._parse_jsonld(html)

                # Strategy 2: Fallback to HTML regex parsing
                if not results:
                    results = self._parse_html(html)

                # Filter accessories — skip if the query itself is for an accessory
                if not _is_accessory(query):
                    results = [p for p in results if not _is_accessory(p["title"])]
                results = results[:max_results]

                if results:
                    logger.info("regard_http_ok", query=query, count=len(results))
                else:
                    logger.warning("regard_http_no_results", query=query)

        except Exception as e:
            logger.error("regard_http_failed", error=str(e), query=query)

        return results

    def _parse_jsonld(self, html: str) -> list[dict]:
        """Extract products from Schema.org JSON-LD OfferCatalog."""
        results = []
        for m in re.finditer(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html,
            re.DOTALL,
        ):
            try:
                data = json.loads(m.group(1).strip())
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") != "OfferCatalog":
                        continue
                    offers = item.get("itemListElement", [])
                    for offer in offers:
                        item_offered = offer.get("itemOffered", offer)
                        name = item_offered.get("name", "").strip()
                        if not name:
                            continue

                        # Price from offers
                        price_num = 0.0
                        offer_data = item_offered.get("offers", {})
                        if isinstance(offer_data, list):
                            for o in offer_data:
                                p = float(o.get("price", 0))
                                if p > 0:
                                    price_num = p
                                    break
                        elif isinstance(offer_data, dict):
                            price_num = float(offer_data.get("price", 0))

                        if not price_num:
                            price_num = float(offer.get("price", 0))

                        if price_num <= 0:
                            continue

                        # URL
                        url = item_offered.get("url", "")
                        if url and not url.startswith("http"):
                            url = f"https://www.regard.ru{url}"

                        # Image
                        image = ""
                        img_data = item_offered.get("image", "")
                        if isinstance(img_data, list):
                            image = img_data[0] if img_data else ""
                        elif isinstance(img_data, str):
                            image = img_data
                        if image and not image.startswith("http"):
                            image = f"https://www.regard.ru{image}"

                        results.append(
                            {
                                "title": name[:200],
                                "price": _fmt_price(price_num),
                                "price_num": price_num,
                                "url": url,
                                "marketplace": "regard",
                                "image": image,
                                "shop": "Регард",
                                "specs": "",
                                "category": "",
                                "onliner_key": "",
                            }
                        )
            except (json.JSONDecodeError, TypeError, KeyError, ValueError):
                continue

        return results

    def _parse_html(self, html: str) -> list[dict]:
        """Fallback: extract products from HTML using regex."""
        results = []
        seen_urls = set()

        # Regard product links: /product/NNNN/slug
        for m in re.finditer(
            r'<a[^>]*href="(/product/\d+/[^"]*)"[^>]*>',
            html,
        ):
            url_path = m.group(1)
            if url_path in seen_urls:
                continue
            seen_urls.add(url_path)

            # Look in surrounding context for title and price
            start = max(0, m.start() - 500)
            end = min(len(html), m.end() + 2000)
            chunk = html[start:end]

            # Title from link text or nearby text
            title = ""
            title_m = re.search(r"CardText[^>]*>([^<]{15,200})<", chunk)
            if not title_m:
                title_m = re.search(r'title="([^"]{15,200})"', chunk)
            if title_m:
                title = title_m.group(1).strip()

            if not title:
                continue

            # Price
            price_num = 0.0
            price_m = re.search(r"CardPrice_price[^>]*>[\s]*(\d[\d\s]*)", chunk)
            if price_m:
                price_num = float(price_m.group(1).replace(" ", "").replace("\xa0", ""))
            else:
                price_m = re.search(r"(\d[\d\s]{2,8})\s*₽", chunk)
                if price_m:
                    price_num = float(price_m.group(1).replace(" ", "").replace("\xa0", ""))

            if price_num <= 0:
                continue

            # Image
            image = ""
            img_m = re.search(r'<img[^>]*src="([^"]*regard[^"]*)"', chunk)
            if not img_m:
                img_m = re.search(r'<img[^>]*src="(/api/site/cacheimg/[^"]*)"', chunk)
            if img_m:
                img_url = img_m.group(1)
                image = img_url if img_url.startswith("http") else f"https://www.regard.ru{img_url}"

            results.append(
                {
                    "title": title[:200],
                    "price": _fmt_price(price_num),
                    "price_num": price_num,
                    "url": f"https://www.regard.ru{url_path}",
                    "marketplace": "regard",
                    "image": image,
                    "shop": "Регард",
                    "specs": "",
                    "category": "",
                    "onliner_key": "",
                }
            )

        return results
