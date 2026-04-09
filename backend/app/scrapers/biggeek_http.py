"""BigGeek.ru HTTP scraper — parallel-import electronics marketplace.

BigGeek is one of the largest parallel-import retailers in RU — Apple,
Samsung, Xiaomi, Google, gaming consoles (PS5, Xbox, Nintendo Switch,
Steam Deck), Dyson, audio. Typically cheaper than Regard and official
resellers. Covers the "game console" gap that 1click.ru doesn't.

Why no GET search endpoint:
  BigGeek has a search form (`action="/products"` with name="keyword")
  but the backend only returns a 404 page — their real search is
  client-side via a third-party RetailRocket widget loaded by JS.
  HTTP scrapers can't trigger it.

Routing strategy:
  Map query keywords to canonical category slugs from the sitemap, fetch
  that category page, and filter by token match on titles. Coverage is
  curated to the top categories users actually search for. Queries that
  don't match any slug return empty — the other marketplaces compensate.

HTML structure:
  <div class="catalog-card">
    <a href="/products/SLUG" class="catalog-card__img">
      <img src="//images.biggeek.ru/.../x@2x.jpg" alt="...">
    </a>
    <a href="/products/SLUG" class="catalog-card__title cart-modal-title">
      TITLE
    </a>
    <div class="catalog-card__price-row">
      <a href="..." class="catalog-card__price">
        <b class="cart-modal-count">от 55 990 <span>₽</span></b>
        <span class="old-price">140 990</span>
      </a>
      ...
    </div>
  </div>
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


# Keyword -> category slug (first match wins, so order matters:
# specific phrases like "steam deck" must come before generic "deck").
# All slugs verified against sitemap.xml at time of writing. If BigGeek
# rotates a slug we fall back to the next rule; if nothing matches we
# return empty instead of guessing.
_ROUTES: list[tuple[tuple[str, ...], str]] = [
    # consoles — check BEFORE anything mentioning iphone/games to avoid
    # misrouting "ps5 игра" to the gaming accessories slug
    (("steam deck",), "steam-deck"),
    (("nintendo switch", "switch"), "nintendo-switch"),
    (("playstation", "ps5", "ps4", "плейстейшн", "плойка"), "sony-playstation"),
    (("xbox", "xbox series", "xbox one"), "microsoft-xbox"),
    # apple line
    (("macbook pro",), "macbook-pro-14"),
    (("macbook air",), "macbook-air-13"),
    (("macbook",), "macbook-air-13"),
    (("ipad pro",), "ipad-pro-11-2024"),
    (("ipad air",), "ipad-air-11-2024"),
    (("ipad mini",), "ipad-mini-2024"),
    (("ipad",), "apple-ipad"),
    (("airpods max",), "apple-airpods-max"),
    (("airpods pro",), "apple-airpods-pro-2022"),
    (("airpods",), "apple-airpods"),
    (("apple watch ultra",), "apple-watch-ultra-2-titan"),
    (("apple watch", "iwatch"), "apple-watch"),
    # iPhone — per-generation slugs exist but the umbrella slug covers all,
    # and the downstream AI filter handles generation/variant matching.
    (("iphone", "айфон"), "apple-iphone"),
    # Samsung phones
    (("galaxy s", "samsung s", "самсунг s"), "smartfony-serii-galaxy-s"),
    (("galaxy a", "samsung a"), "smartfony-serii-galaxy-a"),
    (("galaxy z", "galaxy fold", "galaxy flip"), "smartfony-serii-galaxy-z"),
    (("samsung galaxy", "samsung", "самсунг"), "smartfony-samsung"),
    # Xiaomi — note sitemap typo "cmartfony-xiaomi" is the live slug
    (("xiaomi 15", "redmi", "xiaomi"), "cmartfony-xiaomi"),
    # Google Pixel
    (("pixel", "google pixel"), "smartfony"),
    # Audio / home
    (("наушник", "earbud", "headphone"), "besprovodnye-naushniki-i-garnitury"),
    (("dyson",), "dyson"),
    # Generic fallback for "смартфон" queries
    (("смартфон", "phone", "телефон"), "smartfony"),
]


def _pick_slug(query: str) -> str | None:
    q = query.lower().strip()
    for keywords, slug in _ROUTES:
        for kw in keywords:
            if kw in q:
                return slug
    return None


def _tokenize(query: str) -> list[str]:
    """Split query into lowercase tokens for substring matching.

    We keep tokens >=2 chars and drop pure stopwords; the goal is just to
    filter out irrelevant items inside a broad category page, so this does
    not need to be sophisticated.
    """
    stop = {"для", "в", "с", "и", "the", "of", "и"}
    toks = re.findall(r"[a-z\u0400-\u04ff0-9]+", query.lower())
    return [t for t in toks if len(t) >= 2 and t not in stop]


def _fmt_price(price_num: float) -> str:
    if price_num <= 0:
        return ""
    return f"{int(price_num):,}".replace(",", " ") + " ₽"


class BigGeekHttpScraper:
    """HTTP scraper for biggeek.ru (custom PHP storefront, parallel import)."""

    marketplace_name = "biggeek"
    region = "RU"
    currency = "RUB"

    async def search(self, query: str, *, max_results: int = 20) -> list[dict]:
        results: list[dict] = []
        slug = _pick_slug(query)
        if not slug:
            logger.info("biggeek_no_route", query=query)
            return results

        try:
            async with httpx.AsyncClient(
                timeout=15, follow_redirects=True, headers=_HEADERS
            ) as client:
                r = await client.get(f"https://biggeek.ru/catalog/{slug}")
                if r.status_code != 200:
                    logger.warning("biggeek_http_error", status=r.status_code, slug=slug)
                    return results

                parsed = self._parse_html(r.text)

                # Token-based relevance filter — category pages often carry
                # hundreds of items spanning multiple models, so we narrow
                # to items whose title shares at least one meaningful token
                # with the query. For very short queries (1 token) we keep
                # everything.
                tokens = _tokenize(query)
                if len(tokens) >= 2:
                    filtered = [p for p in parsed if any(t in p["title"].lower() for t in tokens)]
                    # Safety net: if token filter kills >90% of a populated
                    # page, the tokens are probably too specific — return
                    # the full category so downstream AI filter can decide.
                    if len(parsed) >= 10 and len(filtered) <= max(1, len(parsed) // 10):
                        logger.info(
                            "biggeek_token_filter_fallback",
                            query=query,
                            slug=slug,
                            before=len(parsed),
                            after=len(filtered),
                        )
                    else:
                        parsed = filtered

                results = parsed[:max_results]

                if results:
                    logger.info("biggeek_ok", query=query, slug=slug, count=len(results))
                else:
                    logger.warning("biggeek_no_results", query=query, slug=slug)

        except Exception as e:
            logger.error("biggeek_failed", error=str(e), query=query, slug=slug)

        return results

    def _parse_html(self, html: str) -> list[dict]:
        """Extract products from <div class="catalog-card"> blocks."""
        results: list[dict] = []
        seen_urls: set[str] = set()

        # Split on the outer catalog-card opener only. The inner DOM has
        # nested `catalog-card__colors` / `catalog-card__price-row` divs
        # we must NOT split on, so anchor on the exact class value with a
        # terminating `"` or space (no BEM suffix).
        blocks = re.split(r'<div\s+class="catalog-card(?:\s[^"]*)?"', html)
        for blk in blocks[1:]:
            title_m = re.search(
                r'class="catalog-card__title[^"]*"[^>]*>([^<]+)</a>',
                blk,
            )
            if not title_m:
                continue
            title = title_m.group(1).strip()
            if not title:
                continue

            url_m = re.search(
                r'<a\s+href="(/products/[^"]+)"\s+class="catalog-card__title',
                blk,
            )
            if not url_m:
                continue
            url = f"https://biggeek.ru{url_m.group(1)}"
            if url in seen_urls:
                continue

            # Price: inside <b class="cart-modal-count">от 55 990 <span>₽
            price_m = re.search(
                r'class="cart-modal-count"\s*>\s*(?:от\s+)?([\d\s\u00a0]+)\s*<span>\s*₽',
                blk,
            )
            if not price_m:
                continue
            try:
                price_num = float(re.sub(r"[\s\u00a0]", "", price_m.group(1)))
            except ValueError:
                continue
            if price_num <= 0:
                continue

            # Image (protocol-relative URLs are common)
            image = ""
            img_m = re.search(
                r'class="catalog-card__img".*?<img[^>]*src="([^"]+)"',
                blk,
                re.DOTALL,
            )
            if img_m:
                image = img_m.group(1).strip()
                if image.startswith("//"):
                    image = f"https:{image}"

            seen_urls.add(url)
            results.append(
                {
                    "title": title[:200],
                    "price": _fmt_price(price_num),
                    "price_num": price_num,
                    "url": url,
                    "marketplace": "biggeek",
                    "image": image,
                    "shop": "BigGeek",
                    "specs": "",
                    "category": "",
                    "onliner_key": "",
                }
            )

        return results
