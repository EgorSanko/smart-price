"""Playwright-based scrapers for Russian marketplaces.

Uses real Chromium browser to bypass anti-bot protection.
Each scraper opens search page, waits for content, and extracts products from DOM/JSON.
"""

import asyncio
import re

import structlog


logger = structlog.get_logger()

# Shared browser instance (reuse across scrapers in one search cycle)
_browser = None
_playwright = None
_lock = asyncio.Lock()

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

REFURBISHED_KEYWORDS = [
    "восстановленный",
    "восстановлен",
    "восстановл",
    "refurbished",
    "реф.",
    "реф ",
    "б/у",
    "б.у.",
    "бу ",
    " бу",
    "уценка",
    "уцен.",
    "витринный образец",
    "витринный",
    "витрина",
    "не новый",
    "как новый",
    "восст.",
]


def _is_accessory(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in ACCESSORY_KEYWORDS)


def _is_refurbished(title: str) -> bool:
    t = title.lower()
    return any(kw in t for kw in REFURBISHED_KEYWORDS)


def _fmt_price(price_num: float) -> str:
    if price_num <= 0:
        return ""
    return f"{int(price_num):,}".replace(",", " ") + " ₽"


async def _get_browser():
    """Get or create shared browser instance."""
    global _browser, _playwright
    async with _lock:
        if _browser and _browser.is_connected():
            return _browser
        try:
            from playwright.async_api import async_playwright

            _playwright = await async_playwright().start()
            _browser = await _playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--window-size=1920,1080",
                ],
            )
            logger.info("playwright_browser_started")
            return _browser
        except Exception as e:
            logger.error("playwright_browser_start_failed", error=str(e))
            raise


async def _new_page(browser):
    """Create a new page with stealth settings."""
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        ),
        locale="ru-RU",
        timezone_id="Europe/Moscow",
    )
    # Stealth: hide webdriver flag
    await context.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = {runtime: {}};
    """
    )
    page = await context.new_page()
    return page


async def _safe_close_page(page):
    if page:
        try:
            await page.context.close()
        except Exception:
            pass


# ──────────────────────────────────────────────────────────────────
# YANDEX MARKET
# ──────────────────────────────────────────────────────────────────


class YandexMarketPlaywright:
    """Yandex Market scraper using Playwright."""

    marketplace_name = "yandex"
    region = "RU"
    currency = "RUB"

    async def search(self, query: str) -> list[dict]:
        results = []
        page = None
        try:
            browser = await _get_browser()
            page = await _new_page(browser)

            url = f"https://market.yandex.ru/search?text={query}"
            logger.info("yandex_pw_navigating", query=query)

            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            # Wait for products to appear
            try:
                await page.wait_for_selector('[data-autotest-id="product-snippet"]', timeout=10000)
            except Exception:
                # Try alternative selector
                try:
                    await page.wait_for_selector('[data-zone-name="snippetList"]', timeout=5000)
                except Exception:
                    pass

            # Scroll to load more products
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(0.5)

            # Strategy 1: Extract from page source (JSON embedded in HTML)
            html = await page.content()
            results = self._parse_from_html(html)

            if results:
                logger.info("yandex_pw_html_ok", query=query, count=len(results))
                return results

            # Strategy 2: Extract from DOM directly
            results = await self._parse_from_dom(page)

            if results:
                logger.info("yandex_pw_dom_ok", query=query, count=len(results))
            else:
                logger.warning("yandex_pw_no_results", query=query)

        except Exception as e:
            logger.error("yandex_pw_failed", error=str(e), query=query)
        finally:
            await _safe_close_page(page)

        return results

    def _parse_from_html(self, html: str) -> list[dict]:
        """Extract products from embedded JSON in HTML (skuId-based)."""
        results = []
        seen = set()

        for m in re.finditer(r'"skuId"\s*:\s*"(\d+)"', html):
            sku = m.group(1)
            if sku in seen:
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

            pid_m = re.search(r'"productId"\s*:\s*"?(\d+)"?', chunk)

            if not title_m or not price_m:
                continue

            title = title_m.group(1)
            price_num = int(price_m.group(1))

            if price_num < 100 or (_is_accessory(title) or _is_refurbished(title)):
                continue

            seen.add(sku)

            url_str = ""
            if pid_m:
                url_str = f"https://market.yandex.ru/product/{pid_m.group(1)}?sku={sku}"

            # Image
            image = ""
            img_pats = [
                r'"picture"\s*:\s*"(https://avatars\.mds\.yandex\.net/[^"]+)"',
                r'"src"\s*:\s*"(https://avatars\.mds\.yandex\.net/[^"]+)"',
                r'"(https://avatars\.mds\.yandex\.net/get-mpic/\d+/[^"]+)"',
            ]
            for pat in img_pats:
                img_m = re.search(pat, chunk)
                if img_m:
                    image = img_m.group(1)
                    break

            results.append(
                {
                    "title": title,
                    "price": _fmt_price(price_num),
                    "price_num": price_num,
                    "url": url_str,
                    "marketplace": "yandex",
                    "image": image,
                    "shop": "Яндекс Маркет",
                    "specs": "",
                    "category": "",
                    "onliner_key": "",
                }
            )

        return results

    async def _parse_from_dom(self, page) -> list[dict]:
        """Fallback: extract products directly from DOM elements."""
        results = []
        try:
            items = await page.evaluate(
                """
                () => {
                    const products = [];
                    // Try multiple selectors
                    const selectors = [
                        '[data-autotest-id="product-snippet"]',
                        '[data-zone-name="snippet-card"]',
                        'article[data-autotest-id]',
                    ];
                    let elements = [];
                    for (const sel of selectors) {
                        elements = document.querySelectorAll(sel);
                        if (elements.length > 0) break;
                    }
                    elements.forEach(el => {
                        const titleEl = el.querySelector('h3, [data-auto="snippet-title"], [data-zone-name="title"] span');
                        const priceEl = el.querySelector('[data-auto="price-value"], [data-auto="snippet-price-current"]');
                        const linkEl = el.querySelector('a[href*="/product/"]');
                        const imgEl = el.querySelector('img[src*="avatars"]');

                        if (titleEl && priceEl) {
                            const priceText = priceEl.textContent.replace(/[^0-9]/g, '');
                            products.push({
                                title: titleEl.textContent.trim(),
                                price_num: parseInt(priceText) || 0,
                                url: linkEl ? linkEl.href : '',
                                image: imgEl ? imgEl.src : '',
                            });
                        }
                    });
                    return products;
                }
            """
            )

            for item in items:
                if not item.get("title") or not item.get("price_num"):
                    continue
                if _is_accessory(item["title"]) or _is_refurbished(item["title"]):
                    continue
                results.append(
                    {
                        "title": item["title"],
                        "price": _fmt_price(item["price_num"]),
                        "price_num": item["price_num"],
                        "url": item.get("url", ""),
                        "marketplace": "yandex",
                        "image": item.get("image", ""),
                        "shop": "Яндекс Маркет",
                        "specs": "",
                        "category": "",
                        "onliner_key": "",
                    }
                )
        except Exception as e:
            logger.debug("yandex_dom_parse_failed", error=str(e))

        return results


# ──────────────────────────────────────────────────────────────────
# WILDBERRIES
# ──────────────────────────────────────────────────────────────────

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


def _get_basket_number(vol: int) -> str:
    for max_vol, basket in _BASKET_RANGES:
        if vol <= max_vol:
            return basket
    return "39"


def _build_wb_image_url(product_id: int) -> str:
    vol = product_id // 100_000
    part = product_id // 1_000
    basket = _get_basket_number(vol)
    basket_num = int(basket)
    domain = "wbcontent.net" if basket_num >= 17 else "wbbasket.ru"
    return (
        f"https://basket-{basket}.{domain}" f"/vol{vol}/part{part}/{product_id}/images/big/1.webp"
    )


class WildberriesPlaywright:
    """Wildberries scraper using Playwright."""

    marketplace_name = "wildberries"
    region = "RU"
    currency = "RUB"

    async def search(self, query: str) -> list[dict]:
        results = []
        page = None
        try:
            browser = await _get_browser()
            page = await _new_page(browser)

            url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}"
            logger.info("wb_pw_navigating", query=query)

            # Intercept API responses to get product data
            api_data = []

            async def handle_response(response):
                try:
                    resp_url = response.url
                    if "search" in resp_url and (
                        "wb.ru" in resp_url or "wildberries.ru" in resp_url
                    ):
                        if response.status == 200:
                            ct = response.headers.get("content-type", "")
                            if "json" in ct or "application" in ct:
                                body = await response.json()
                                if isinstance(body, dict):
                                    api_data.append(body)
                except Exception:
                    pass

            page.on("response", handle_response)

            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for products to load
            try:
                await page.wait_for_selector(
                    '.product-card, [class*="product-card"], .j-card-item', timeout=15000
                )
            except Exception:
                pass

            # Scroll to trigger lazy loading + give time for API responses
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 600)")
                await asyncio.sleep(0.7)
            await asyncio.sleep(2)

            # Strategy 1: Use intercepted API data
            for data in api_data:
                products = data.get("data", {}).get("products") or data.get("products") or []
                for item in products:
                    product = self._parse_api_item(item)
                    if product:
                        results.append(product)
                if results:
                    break

            if results:
                logger.info("wb_pw_api_ok", query=query, count=len(results))
                return results

            # Strategy 2: Parse from DOM
            results = await self._parse_from_dom(page)

            if results:
                logger.info("wb_pw_dom_ok", query=query, count=len(results))
            else:
                logger.warning("wb_pw_no_results", query=query)

        except Exception as e:
            logger.error("wb_pw_failed", error=str(e), query=query)
        finally:
            await _safe_close_page(page)

        return results

    def _parse_api_item(self, item: dict) -> dict | None:
        """Parse product from intercepted WB API response."""
        product_id = item.get("id")
        if not product_id:
            return None

        product_id = int(product_id)
        name = (item.get("name") or "").strip()
        brand = (item.get("brand") or "").strip()

        if not name:
            return None

        title = f"{brand} {name}".strip() if brand else name
        if _is_accessory(title) or _is_refurbished(title):
            return None

        # Stock check: skip items where no size has actual stocks.
        # WB still returns OOS items with prices in search but they can't be bought.
        sizes = item.get("sizes", []) or []
        total_qty = item.get("totalQuantity")
        if total_qty == 0:
            return None
        if sizes:
            has_stock = any((sz.get("stocks") or []) for sz in sizes)
            if not has_stock:
                return None

        # Extract price
        price_num = 0.0
        if sizes:
            price_obj = sizes[0].get("price", {})
            price_num = (price_obj.get("product") or price_obj.get("total") or 0) / 100.0
        if not price_num:
            raw = item.get("salePriceU") or item.get("priceU") or 0
            price_num = float(raw) / 100.0

        if price_num <= 0:
            return None

        rating = item.get("rating", 0)
        feedbacks = item.get("feedbacks", 0)
        specs = ""
        if rating:
            specs = f"★ {rating}"
            if feedbacks:
                specs += f" ({feedbacks} отзывов)"

        return {
            "title": title,
            "price": _fmt_price(price_num),
            "price_num": price_num,
            "url": f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx",
            "marketplace": "wildberries",
            "image": _build_wb_image_url(product_id),
            "shop": brand or "Wildberries",
            "specs": specs,
            "category": "",
            "onliner_key": "",
        }

    async def _parse_from_dom(self, page) -> list[dict]:
        """Fallback: extract from DOM."""
        results = []
        try:
            items = await page.evaluate(
                """
                () => {
                    const products = [];
                    // WB uses various card selectors
                    const selectors = [
                        '.product-card',
                        '[class*="product-card"]',
                        '.j-card-item',
                        '[data-nm-id]',
                        'article.product-card',
                    ];
                    let cards = [];
                    for (const sel of selectors) {
                        cards = document.querySelectorAll(sel);
                        if (cards.length > 0) break;
                    }

                    cards.forEach(card => {
                        const linkEl = card.querySelector('a[href*="/catalog/"]');
                        // Try multiple name selectors
                        let nameText = '';
                        const nameSelectors = [
                            '.product-card__name',
                            '[class*="product-card__name"]',
                            '.goods-name',
                            'span.goods-name',
                        ];
                        for (const ns of nameSelectors) {
                            const el = card.querySelector(ns);
                            if (el && el.textContent.trim()) { nameText = el.textContent.trim(); break; }
                        }

                        let brandText = '';
                        const brandEl = card.querySelector('.product-card__brand, [class*="brand-name"]');
                        if (brandEl) brandText = brandEl.textContent.trim();

                        // Price: look for ins tag or price-specific class
                        let priceText = '0';
                        const priceSelectors = [
                            'ins.price__lower-price',
                            'ins[class*="lower-price"]',
                            'ins',
                            '.price__lower-price',
                            '[class*="price-value"]',
                        ];
                        for (const ps of priceSelectors) {
                            const el = card.querySelector(ps);
                            if (el) {
                                const txt = el.textContent.replace(/[^0-9]/g, '');
                                if (txt.length >= 3) { priceText = txt; break; }
                            }
                        }

                        const imgEl = card.querySelector('img');

                        const title = (brandText ? brandText + ' ' : '') + nameText;
                        if (title.trim() && parseInt(priceText) > 0) {
                            const href = linkEl ? linkEl.href : '';
                            const idMatch = href.match(/catalog\\/(\\d+)/);
                            products.push({
                                title: title.trim(),
                                price_num: parseInt(priceText),
                                url: href,
                                product_id: idMatch ? parseInt(idMatch[1]) : 0,
                                image: imgEl ? imgEl.src : '',
                            });
                        }
                    });
                    return products;
                }
            """
            )

            for item in items:
                if not item.get("title") or not item.get("price_num"):
                    continue
                if _is_accessory(item["title"]) or _is_refurbished(item["title"]):
                    continue

                pid = item.get("product_id", 0)
                image = item.get("image", "")
                if pid and not image:
                    image = _build_wb_image_url(pid)

                results.append(
                    {
                        "title": item["title"],
                        "price": _fmt_price(item["price_num"]),
                        "price_num": item["price_num"],
                        "url": item.get("url", ""),
                        "marketplace": "wildberries",
                        "image": image,
                        "shop": "Wildberries",
                        "specs": "",
                        "category": "",
                        "onliner_key": "",
                    }
                )
        except Exception as e:
            logger.debug("wb_dom_parse_failed", error=str(e))

        return results


# ──────────────────────────────────────────────────────────────────
# CITILINK
# ──────────────────────────────────────────────────────────────────

_PRICE_RE = re.compile(r"[\d]+")


class CitilinkPlaywright:
    """Citilink scraper using Playwright.

    Citilink is a major Russian electronics retailer.
    Uses Next.js frontend with GraphQL API.
    DOM parsing extracts product data from rendered cards.
    """

    marketplace_name = "citilink"
    region = "RU"
    currency = "RUB"

    async def search(self, query: str) -> list[dict]:
        results = []
        page = None
        try:
            browser = await _get_browser()
            page = await _new_page(browser)

            url = f"https://www.citilink.ru/search/?text={query}"
            logger.info("citilink_pw_navigating", query=query)

            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # Wait for product links to appear
            try:
                await page.wait_for_selector('a[href*="/product/"]', timeout=12000)
            except Exception:
                pass

            # Scroll to load more
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 600)")
                await asyncio.sleep(0.5)

            await asyncio.sleep(1)

            # Extract products from DOM
            items = await page.evaluate(
                """
                () => {
                    const products = [];
                    const seen = new Set();

                    const links = document.querySelectorAll('a[href*="/product/"]');
                    links.forEach(link => {
                        const href = link.href;
                        // Skip review/otzyvy links and duplicates
                        if (href.includes('/otzyvy') || href.includes('/reviews')) return;
                        if (seen.has(href)) return;
                        seen.add(href);

                        // Find parent card (walk up ~5 levels)
                        let card = link;
                        for (let i = 0; i < 6; i++) {
                            if (card.parentElement) card = card.parentElement;
                        }

                        const text = card.innerText;
                        if (!text || text.length < 20) return;

                        // Extract title: look for product description pattern
                        // Citilink titles look like: '6.1" Смартфон Apple iPhone 16 256Gb, ...'
                        let title = '';
                        const lines = text.split('\\n').filter(l => l.trim().length > 15);
                        for (const line of lines) {
                            const l = line.trim();
                            // Title is usually a line with product specs (contains brand or size)
                            if ((l.includes('"') || l.includes('Смартфон') || l.includes('Ноутбук') ||
                                 l.includes('Телевизор') || l.includes('Монитор') || l.includes('Наушники') ||
                                 l.length > 30) && !l.includes('₽') && !l.includes('пунктов') &&
                                !l.includes('Привезём') && !l.includes('Скидка') && !l.includes('Суперцена') &&
                                !l.includes('по релевантности') && !l.includes('Добавить')) {
                                title = l;
                                break;
                            }
                        }

                        if (!title) return;

                        // Extract price: find number followed by ₽
                        // Take the FIRST valid price (main price), not the last
                        let price_num = 0;
                        const priceMatches = text.match(/(\\d[\\d\\s]+)₽/g);
                        if (priceMatches) {
                            for (const pm of priceMatches) {
                                const digits = pm.replace(/[^0-9]/g, '');
                                const p = parseInt(digits);
                                if (p > 500 && p < 10000000) {
                                    price_num = p;
                                    break;  // take FIRST valid price
                                }
                            }
                        }

                        if (!price_num) return;

                        // Extract image — try multiple selectors
                        let image = '';
                        // Try product image selectors (Citilink uses various CDN domains)
                        const imgSelectors = [
                            'img[src*="citilink"]',
                            'img[src*="cdn-img"]',
                            'img[src*="static.citilink"]',
                            'img[src*="images.citilink"]',
                            'img[data-src*="citilink"]',
                            'img[src*="cdn"]',
                        ];
                        for (const sel of imgSelectors) {
                            const imgEl = card.querySelector(sel);
                            if (imgEl) {
                                image = imgEl.src || imgEl.dataset.src || imgEl.getAttribute('data-src') || '';
                                if (image && !image.includes('data:')) break;
                                image = '';
                            }
                        }
                        // Fallback: any non-inline img with reasonable src
                        if (!image) {
                            const imgs = card.querySelectorAll('img');
                            for (const img of imgs) {
                                const s = img.src || img.dataset.src || '';
                                if (s && !s.includes('data:') && !s.includes('svg') &&
                                    (s.includes('http') || s.startsWith('//'))) {
                                    image = s;
                                    break;
                                }
                            }
                        }

                        // Extract rating
                        let rating = 0;
                        const ratingMatch = text.match(/(\\d\\.?\\d?)\\s*\\n\\s*(\\d+)/);
                        if (ratingMatch) {
                            const r = parseFloat(ratingMatch[1]);
                            if (r >= 1 && r <= 5) rating = r;
                        }

                        products.push({
                            title: title,
                            price_num: price_num,
                            url: href,
                            image: image,
                            rating: rating,
                        });
                    });

                    return products;
                }
            """
            )

            for item in items:
                title = item.get("title", "").strip()
                price_num = item.get("price_num", 0)

                if not title or not price_num:
                    continue
                if _is_accessory(title) or _is_refurbished(title):
                    continue

                specs = ""
                rating = item.get("rating", 0)
                if rating:
                    specs = f"★ {rating}"

                results.append(
                    {
                        "title": title,
                        "price": _fmt_price(price_num),
                        "price_num": price_num,
                        "url": item.get("url", ""),
                        "marketplace": "citilink",
                        "image": item.get("image", ""),
                        "shop": "Ситилинк",
                        "specs": specs,
                        "category": "",
                        "onliner_key": "",
                    }
                )

            if results:
                logger.info("citilink_pw_ok", query=query, count=len(results))
            else:
                logger.warning("citilink_pw_no_results", query=query)

        except Exception as e:
            logger.error("citilink_pw_failed", error=str(e), query=query)
        finally:
            await _safe_close_page(page)

        return results


# ──────────────────────────────────────────────────────────────────
# CITILINK CATALOG BROWSER
# ──────────────────────────────────────────────────────────────────


class CitilinkCatalogScraper:
    """Scrapes Citilink category pages to extract brands and product models.

    Used for deep catalog navigation:
    Category → Brand → Specific Model → Price Comparison
    """

    async def browse_category(self, citilink_path: str) -> dict:
        """Browse a Citilink category page, extract brands and products.

        Args:
            citilink_path: e.g. "/catalog/naushniki/"

        Returns:
            {"brands": [...], "products": [...]}
        """
        page = None
        try:
            browser = await _get_browser()
            page = await _new_page(browser)

            url = f"https://www.citilink.ru{citilink_path}"
            logger.info("citilink_catalog_navigating", path=citilink_path)

            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

            try:
                await page.wait_for_selector('a[href*="/product/"]', timeout=12000)
            except Exception:
                pass

            # Scroll to load products
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(0.4)
            await asyncio.sleep(1)

            # Extract brands and products from DOM
            data = await page.evaluate(
                """
                () => {
                    const brands = new Map();
                    const products = [];
                    const seen = new Set();

                    const links = document.querySelectorAll('a[href*="/product/"]');
                    links.forEach(link => {
                        const href = link.href;
                        if (href.includes('/otzyvy') || href.includes('/reviews')) return;
                        if (seen.has(href)) return;
                        seen.add(href);

                        // Card is 2 levels up from product link
                        let card = link;
                        for (let i = 0; i < 2; i++) {
                            if (card.parentElement) card = card.parentElement;
                        }

                        const text = card.innerText;
                        if (!text || text.length < 20) return;

                        // Extract title: longest line that looks like a product name
                        let title = '';
                        const lines = text.split('\\n').filter(l => l.trim().length > 0);
                        for (const line of lines) {
                            const l = line.trim();
                            if (l.length < 15) continue;
                            // Skip noise lines
                            if (/\\u20bd|\\u20b4|Привез|Скидка|Суперцена|релевантн|Добавить|Сравнить|В корзину|Клубная|Рассрочка|пунктов|Показать|Загрузить/.test(l)) continue;
                            // Title is the longest descriptive line
                            if (l.length > title.length) {
                                title = l;
                            }
                        }
                        if (!title || title.length < 15) return;

                        // Extract price
                        let price_num = 0;
                        const priceMatches = text.match(/(\\d[\\d\\s]+)\\u20bd/g);
                        if (priceMatches) {
                            // Take first valid price (main price)
                            for (const pm of priceMatches) {
                                const digits = pm.replace(/[^0-9]/g, '');
                                const p = parseInt(digits);
                                if (p > 100) {
                                    price_num = p;
                                    break;
                                }
                            }
                        }
                        if (!price_num) return;

                        // Extract image from THIS card only
                        let image = '';
                        const imgEl = card.querySelector('img[src*="cdn"]');
                        if (imgEl) image = imgEl.src;
                        if (!image) {
                            const anyImg = card.querySelector('img');
                            if (anyImg && anyImg.src && !anyImg.src.includes('data:'))
                                image = anyImg.src;
                        }

                        // Extract brand from title
                        let brand = '';
                        const knownBrands = [
                            'Apple', 'Samsung', 'Xiaomi', 'Sony', 'JBL', 'Marshall', 'Bose',
                            'Sennheiser', 'Huawei', 'Honor', 'Realme', 'OPPO', 'OnePlus',
                            'Google', 'Nothing', 'Beats', 'AKG', 'Audio-Technica', 'Jabra',
                            'Philips', 'LG', 'Hisense', 'TCL', 'Haier', 'Lenovo', 'ASUS',
                            'Acer', 'HP', 'Dell', 'MSI', 'Gigabyte', 'Intel', 'AMD',
                            'NVIDIA', 'Corsair', 'Logitech', 'Razer', 'HyperX', 'SteelSeries',
                            'Kingston', 'Crucial', 'Western Digital', 'Seagate', 'Dyson',
                            'Bosch', 'Siemens', 'Electrolux', 'Braun', 'Panasonic', 'Canon',
                            'Nikon', 'Fujifilm', 'GoPro', 'DJI', 'Garmin', 'Fitbit',
                            'QCY', 'Edifier', 'Harman Kardon', 'Bang & Olufsen', 'Sonos',
                            'Creative', 'Plantronics', 'Skullcandy', 'Anker', 'Baseus',
                            'Vivo', 'ZTE', 'Motorola', 'Nokia', 'POCO', 'Redmi', 'iQOO',
                            'Tecno', 'Infinix', 'Blackview', 'DOOGEE', 'Oukitel',
                            'DeepCool', 'be quiet!', 'Noctua', 'Thermaltake', 'Cooler Master',
                            'Palit', 'ZOTAC', 'EVGA', 'Sapphire', 'PowerColor', 'XFX',
                            'BenQ', 'AOC', 'ViewSonic', 'iiyama', 'Aopen',
                            'Midea', 'Daikin', 'Ballu', 'Polaris', 'Vitek', 'Redmond',
                            'Krups', 'Nespresso', 'Saeco', 'Jura', 'HOCO', 'URAL',
                            'Toshiba', 'Sharp', 'Hyundai', 'Starwind', 'BBK',
                            'Cougar', 'Genesis', 'Trust', 'Defender', 'A4Tech', 'Bloody',
                            'SanDisk', 'Transcend', 'ADATA', 'Patriot', 'G.Skill',
                        ];

                        const titleUpper = title.toUpperCase();
                        for (const b of knownBrands) {
                            const idx = titleUpper.indexOf(b.toUpperCase());
                            if (idx !== -1) {
                                brand = b;
                                break;
                            }
                        }
                        // If no known brand found, try to extract from title pattern
                        // e.g. "Наушники BRANDNAME Model..." - word after category keyword
                        if (!brand) {
                            const m = title.match(/(?:Наушники|Смартфон|Ноутбук|Телевизор|Монитор|Видеокарта|Процессор|Клавиатура|Мышь|Колонка|Камера)\\s+([A-Za-z][A-Za-z0-9]+)/i);
                            if (m) brand = m[1];
                        }

                        if (brand) {
                            brands.set(brand, (brands.get(brand) || 0) + 1);
                        }

                        products.push({
                            title, price_num, url: href, image, brand,
                        });
                    });

                    return {
                        brands: Array.from(brands.entries())
                            .map(([name, count]) => ({name, count}))
                            .sort((a, b) => b.count - a.count),
                        products,
                    };
                }
            """
            )

            logger.info(
                "citilink_catalog_ok",
                path=citilink_path,
                brands=len(data.get("brands", [])),
                products=len(data.get("products", [])),
            )
            return data

        except Exception as e:
            logger.error("citilink_catalog_failed", error=str(e), path=citilink_path)
            return {"brands": [], "products": []}
        finally:
            await _safe_close_page(page)


# ──────────────────────────────────────────────────────────────────
# REGARD
# ──────────────────────────────────────────────────────────────────


class RegardPlaywright:
    """Regard.ru scraper using Playwright.

    Regard is a major Russian computer/electronics retailer.
    Products render server-side with React, so DOM parsing works well.
    Cards use class Card_wrap, prices use CardPrice_price.
    """

    marketplace_name = "regard"
    region = "RU"
    currency = "RUB"

    async def search(self, query: str) -> list[dict]:
        results = []
        page = None
        try:
            browser = await _get_browser()
            page = await _new_page(browser)

            url = f"https://www.regard.ru/catalog?search={query}"
            logger.info("regard_pw_navigating", query=query)

            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Scroll to load more
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 600)")
                await asyncio.sleep(0.5)

            items = await page.evaluate(
                """
                () => {
                    const products = [];
                    const cards = document.querySelectorAll('[class*="Card_wrap"]');

                    cards.forEach(card => {
                        const link = card.querySelector('a[href*="/product/"]');
                        if (!link) return;

                        const priceEl = card.querySelector('[class*="CardPrice_price"]');
                        if (!priceEl) return;

                        const priceText = priceEl.textContent.replace(/[^0-9]/g, '');
                        const price_num = parseInt(priceText) || 0;
                        if (price_num < 100) return;

                        const titleEl = card.querySelector('[class*="CardText"]');
                        let title = '';
                        if (titleEl) {
                            title = titleEl.textContent.trim();
                        } else {
                            title = link.textContent.trim();
                        }
                        // Remove specs that are concatenated with title
                        const specIdx = title.search(/\\d+\\.\\d+[\\u0022\\u201C\\u201D]|\\d+ ГБ|стандарт связи/);
                        if (specIdx > 10) {
                            title = title.slice(0, specIdx).trim();
                        }

                        if (!title || title.length < 10) return;

                        const img = card.querySelector('img');
                        const image = img ? img.src : '';

                        products.push({
                            title: title.slice(0, 200),
                            price_num: price_num,
                            url: link.href,
                            image: image,
                        });
                    });

                    return products;
                }
            """
            )

            for item in items:
                title = item.get("title", "").strip()
                price_num = item.get("price_num", 0)

                if not title or not price_num:
                    continue
                if _is_accessory(title) or _is_refurbished(title):
                    continue

                results.append(
                    {
                        "title": title,
                        "price": _fmt_price(price_num),
                        "price_num": price_num,
                        "url": item.get("url", ""),
                        "marketplace": "regard",
                        "image": item.get("image", ""),
                        "shop": "Регард",
                        "specs": "",
                        "category": "",
                        "onliner_key": "",
                    }
                )

            if results:
                logger.info("regard_pw_ok", query=query, count=len(results))
            else:
                logger.warning("regard_pw_no_results", query=query)

        except Exception as e:
            logger.error("regard_pw_failed", error=str(e), query=query)
        finally:
            await _safe_close_page(page)

        return results


# ──────────────────────────────────────────────────────────────────
# ALIEXPRESS
# ──────────────────────────────────────────────────────────────────


class AliExpressPlaywright:
    """AliExpress Russia scraper using Playwright.

    AliExpress.ru renders product cards client-side.
    Products have /item/NNNNN links. DOM parsing extracts title, price, image.
    """

    marketplace_name = "aliexpress"
    region = "RU"
    currency = "RUB"

    async def search(self, query: str) -> list[dict]:
        results = []
        page = None
        try:
            browser = await _get_browser()
            page = await _new_page(browser)

            url = f"https://aliexpress.ru/wholesale?SearchText={query}"
            logger.info("ali_pw_navigating", query=query)

            await page.goto(url, wait_until="domcontentloaded", timeout=45000)

            # Wait for product content to load
            await asyncio.sleep(5)

            # Scroll to load more products
            for _ in range(4):
                await page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(1)

            items = await page.evaluate(
                """
                () => {
                    const products = [];
                    const seen = new Set();

                    const links = Array.from(document.querySelectorAll('a'))
                        .filter(a => /\\/item\\/\\d+/.test(a.href));

                    for (const a of links) {
                        const match = a.href.match(/\\/item\\/(\\d+)/);
                        if (!match || seen.has(match[1])) continue;
                        if (match[1].length < 5) continue;
                        seen.add(match[1]);

                        // Walk up to find the product card container
                        let card = a;
                        for (let i = 0; i < 6; i++) {
                            if (card.parentElement) card = card.parentElement;
                        }

                        const text = card.innerText || '';
                        if (text.length < 20) continue;

                        // Extract title (first meaningful line)
                        let title = '';
                        const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 10);
                        for (const line of lines) {
                            if (!line.includes('₽') && !line.includes('доставк') &&
                                !line.includes('купон') && !line.includes('Быстрая') &&
                                !line.includes('продано') && line.length > 15) {
                                title = line;
                                break;
                            }
                        }

                        if (!title) continue;

                        // Extract price
                        let price_num = 0;
                        const priceMatches = text.match(/(\\d[\\d\\s,.]+)\\s*₽/g);
                        if (priceMatches) {
                            for (const pm of priceMatches) {
                                const digits = pm.replace(/[^0-9]/g, '');
                                const p = parseInt(digits);
                                if (p > 100 && (price_num === 0 || p < price_num)) {
                                    price_num = p;
                                }
                            }
                        }

                        if (!price_num) continue;

                        // Image
                        let image = '';
                        const img = card.querySelector('img');
                        if (img && img.src && !img.src.includes('data:')) {
                            image = img.src;
                        }

                        products.push({
                            title: title.slice(0, 200),
                            price_num: price_num,
                            url: 'https://aliexpress.ru/item/' + match[1] + '.html',
                            image: image,
                        });
                    }

                    return products;
                }
            """
            )

            for item in items:
                title = item.get("title", "").strip()
                price_num = item.get("price_num", 0)

                if not title or not price_num:
                    continue
                if _is_accessory(title) or _is_refurbished(title):
                    continue

                results.append(
                    {
                        "title": title,
                        "price": _fmt_price(price_num),
                        "price_num": price_num,
                        "url": item.get("url", ""),
                        "marketplace": "aliexpress",
                        "image": item.get("image", ""),
                        "shop": "AliExpress",
                        "specs": "",
                        "category": "",
                        "onliner_key": "",
                    }
                )

            if results:
                logger.info("ali_pw_ok", query=query, count=len(results))
            else:
                logger.warning("ali_pw_no_results", query=query)

        except Exception as e:
            logger.error("ali_pw_failed", error=str(e), query=query)
        finally:
            await _safe_close_page(page)

        return results


async def close_browser():
    """Close shared browser instance. Call on app shutdown."""
    global _browser, _playwright
    if _browser:
        try:
            await _browser.close()
        except Exception:
            pass
        _browser = None
    if _playwright:
        try:
            await _playwright.stop()
        except Exception:
            pass
        _playwright = None
