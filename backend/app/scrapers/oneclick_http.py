"""1click.ru HTTP scraper — parallel-import electronics store based in Omsk.

Wide Apple-centric assortment (iPhone, iPad, MacBook, AirPods, Watch) plus
Samsung, Xiaomi, Google, OnePlus, and smart-home gadgets. No game consoles.
Prices typically below official/premium resellers — dual-SIM Global eSIM
variants dominate the lineup (indicator of parallel import).

Search endpoint: GET /search/?q=QUERY — returns standard catalog page with
`<div class=product>` cards. No anti-bot protection, plain Bitrix HTML.

Price parsing: the product card contains multiple `product__buy-price-item`
spans — one for cashback (inside `cashback-price`), an optional crossed-out
old price (`product__buy-price-item_old`), and the real current price
(`product__buy-price-item` inside `<form class="product__buy">`). We scope
the price match to the content of the form to avoid the cashback trap.
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


def _fmt_price(price_num: float) -> str:
    if price_num <= 0:
        return ""
    return f"{int(price_num):,}".replace(",", " ") + " ₽"


class OneclickHttpScraper:
    """HTTP scraper for 1click.ru (Bitrix storefront, parallel import)."""

    marketplace_name = "oneclick"
    region = "RU"
    currency = "RUB"

    async def search(self, query: str, *, max_results: int = 20) -> list[dict]:
        results: list[dict] = []
        try:
            async with httpx.AsyncClient(
                timeout=15, follow_redirects=True, headers=_HEADERS
            ) as client:
                r = await client.get(
                    "https://1click.ru/search/",
                    params={"q": query},
                )
                if r.status_code != 200:
                    logger.warning("oneclick_http_error", status=r.status_code)
                    return results

                results = self._parse_html(r.text)
                results = results[:max_results]

                if results:
                    logger.info("oneclick_ok", query=query, count=len(results))
                else:
                    logger.warning("oneclick_no_results", query=query)

        except Exception as e:
            logger.error("oneclick_failed", error=str(e), query=query)

        return results

    def _parse_html(self, html: str) -> list[dict]:
        """Extract products from <div class=product> blocks on the search page.

        The search page embeds two kinds of results:
          1. An autocomplete dropdown (`header__bottom-search-drop`) — title +
             URL only, no prices. We skip it by anchoring on the real product
             card marker below.
          2. The actual product grid — `<div class=product>` blocks with
             `product__img`, `product__name`, and a `product__buy` form.
        """
        results: list[dict] = []
        seen_urls: set[str] = set()

        # Drop the header autocomplete section if present, so we don't parse
        # priceless dropdown items as "products with price 0".
        drop_idx = html.find("header__bottom-search-drop")
        if drop_idx != -1:
            # Cut everything before the first real product card past the drop
            real_start = html.find("<div class=product>", drop_idx)
            if real_start != -1:
                html = html[real_start:]

        blocks = re.split(r"<div\s+class=product>", html)
        for blk in blocks[1:]:
            name_m = re.search(
                r'class=product__name\s+href="([^"]+)"\s*>\s*<span>([^<]+)</span>',
                blk,
            )
            if not name_m:
                continue
            url = name_m.group(1).strip()
            title = name_m.group(2).strip()
            if not title or url in seen_urls:
                continue

            # The real price lives inside <div class=product__buy-price> ...
            # which itself lives inside <form class="product__buy js-buy">.
            # We match the price item NOT suffixed with _old.
            buy_m = re.search(r"class=product__buy-price>(.*?)</form>", blk, re.DOTALL)
            if not buy_m:
                continue
            buy_html = buy_m.group(1)
            # Current price = last product__buy-price-item that isn't _old.
            # Format: `<div class=product__buy-price-item>\n127 640 ₽ </div>`
            price_matches = re.findall(
                r"class=product__buy-price-item>\s*([\d\s\u00a0]+)\s*₽",
                buy_html,
            )
            if not price_matches:
                continue
            # Take the last match — the "old price" has its own class suffix
            # _old which the regex above skips, so price_matches only ever
            # contains current prices.
            price_str = re.sub(r"[\s\u00a0]", "", price_matches[-1])
            try:
                price_num = float(price_str)
            except ValueError:
                continue
            if price_num <= 0:
                continue

            # Image from product__img block preceding the bottom.
            image = ""
            img_m = re.search(
                r'class=product__img[^>]*>.*?<img\s+src="([^"]+)"',
                blk,
                re.DOTALL,
            )
            if img_m:
                image = img_m.group(1).strip()

            if url and not url.startswith("http"):
                url = f"https://1click.ru{url}"
            if image and not image.startswith("http"):
                image = f"https://1click.ru{image}"

            # Product category label ("Смартфон", "Планшет" etc.) — handy as
            # a specs hint for the UI though not required for filtering.
            category = ""
            cat_m = re.search(r"class=product__type[^>]*>\s*([^<]+?)\s*</span>", blk)
            if cat_m:
                category = cat_m.group(1).strip()

            seen_urls.add(url)
            results.append(
                {
                    "title": title[:200],
                    "price": _fmt_price(price_num),
                    "price_num": price_num,
                    "url": url,
                    "marketplace": "oneclick",
                    "image": image,
                    "shop": "1click",
                    "specs": category,
                    "category": "",
                    "onliner_key": "",
                }
            )

        return results
