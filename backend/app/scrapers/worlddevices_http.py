"""World-Devices.ru HTTP scraper — OpenCart-based electronics store in St. Petersburg.

Simple HTML parsing, no anti-bot protection.
Search URL: /index.php?route=product/search&search=QUERY
"""

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
    "держатель",
    "брелок",
    "strap",
    "case",
    "cover",
    "сумка",
]


def _is_accessory(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in _ACCESSORY_KEYWORDS)


def _fmt_price(price_num: float) -> str:
    if price_num <= 0:
        return ""
    return f"{int(price_num):,}".replace(",", " ") + " ₽"


class WorldDevicesHttpScraper:
    """HTTP scraper for world-devices.ru (OpenCart store)."""

    marketplace_name = "worlddevices"
    region = "RU"
    currency = "RUB"

    _STOP = {"для", "и", "с", "в", "на", "по", "от", "до", "из", "the", "for", "of", "with"}

    @staticmethod
    def _trim_query(query: str, max_words: int = 6) -> str:
        """Shorten query for OpenCart which chokes on long searches."""
        words = query.split()
        significant = [w for w in words if w.lower() not in WorldDevicesHttpScraper._STOP]
        if len(significant) <= max_words:
            return " ".join(significant)
        return " ".join(significant[:max_words])

    async def search(self, query: str, *, max_results: int = 15) -> list[dict]:
        results: list[dict] = []
        # OpenCart search breaks on very long queries (>~50 chars) —
        # keep only the first 6 significant words (drop prepositions/articles).
        search_q = self._trim_query(query)
        skip_acc = _is_accessory(query)
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                results = await self._fetch(client, search_q)

                # OpenCart full-text is picky: too many keywords → 0 results.
                # Retry with progressively shorter queries until something hits.
                if not results:
                    words = search_q.split()
                    for limit in (4, 3, 2):
                        if len(words) <= limit:
                            continue
                        short_q = " ".join(words[:limit])
                        results = await self._fetch(client, short_q)
                        if results:
                            break

                # Filter accessories — skip if the query itself IS for an accessory
                if not skip_acc:
                    results = [p for p in results if not _is_accessory(p["title"])]
                results = results[:max_results]

                if results:
                    logger.info("worlddevices_ok", query=query, count=len(results))
                else:
                    logger.warning("worlddevices_no_results", query=query)

        except Exception as e:
            logger.error("worlddevices_failed", error=str(e), query=query)

        return results

    async def _fetch(self, client: httpx.AsyncClient, search_q: str) -> list[dict]:
        """Single search request to WD OpenCart."""
        r = await client.get(
            "https://world-devices.ru/index.php",
            params={"route": "product/search", "search": search_q, "limit": "48"},
            headers=_HEADERS,
        )
        if r.status_code != 200:
            return []
        return self._parse_html(r.text)

    def _parse_html(self, html: str) -> list[dict]:
        """Extract products from OpenCart product-layout blocks."""
        results = []
        seen_urls: set[str] = set()

        # Split by product-layout divs
        blocks = re.split(r'<div\s+class="product-layout', html)

        for block in blocks[1:]:  # skip first chunk before any product
            # Title + URL from <a class="product-thumb__name" href="...">Title</a>
            link_m = re.search(
                r'<a\s+class="product-thumb__name"\s+href="([^"]+)"[^>]*>(.*?)</a>',
                block,
                re.DOTALL,
            )
            if not link_m:
                continue

            url = link_m.group(1).strip()
            title = re.sub(r"<[^>]+>", "", link_m.group(2)).strip()

            if not title or url in seen_urls:
                continue
            seen_urls.add(url)

            if not url.startswith("http"):
                url = f"https://world-devices.ru{url}"

            # Price from data-price attribute (most reliable)
            price_num = 0.0
            price_attr_m = re.search(r'data-price="(\d+)"', block)
            if price_attr_m:
                try:
                    price_num = float(price_attr_m.group(1))
                except ValueError:
                    pass

            # Fallback: text price
            if not price_num:
                price_m = re.search(r"([\d]+[\d\s]*)\s*р\.", block)
                if price_m:
                    price_str = price_m.group(1).replace(" ", "").replace("\xa0", "")
                    try:
                        price_num = float(price_str)
                    except ValueError:
                        pass

            if price_num <= 0:
                continue

            # Image from product-thumb__image block
            image = ""
            img_m = re.search(
                r'product-thumb__image[^>]*>.*?<img[^>]*src="([^"]+)"',
                block,
                re.DOTALL,
            )
            if img_m:
                image = img_m.group(1).strip()
                if image and not image.startswith("http"):
                    image = f"https://world-devices.ru{image}"

            # Stock status
            stock = ""
            stock_m = re.search(r"qty-indicator__text[^>]*>\s*(.*?)\s*</div>", block, re.DOTALL)
            if stock_m:
                stock = stock_m.group(1).strip()

            results.append(
                {
                    "title": title[:200],
                    "price": _fmt_price(price_num),
                    "price_num": price_num,
                    "url": url,
                    "marketplace": "worlddevices",
                    "image": image,
                    "shop": "World Devices",
                    "specs": stock,
                    "category": "",
                    "onliner_key": "",
                }
            )

        return results
