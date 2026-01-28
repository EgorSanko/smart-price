"""Ozon marketplace scraper.

Scraper for ozon.ru using Playwright for JavaScript rendering.
Ozon heavily relies on client-side rendering, making browser automation necessary.
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING, Any, AsyncGenerator

from selectolax.parser import HTMLParser

from app.scrapers.base import PlaywrightScraper, ScraperError

if TYPE_CHECKING:
    from app.schemas.product import ProductCreate

logger = logging.getLogger(__name__)


class OzonParseError(ScraperError):
    """Error parsing Ozon data."""

    pass


class OzonScraper(PlaywrightScraper):
    """Scraper for Ozon marketplace.

    Ozon uses heavy JavaScript rendering and stores product data in JSON
    embedded within the page. This scraper uses Playwright to render pages
    and extracts data from embedded JSON structures.

    Attributes:
        marketplace_name: "ozon"
        base_url: "https://www.ozon.ru"
        rate_limit: 0.5 requests per second (Ozon is aggressive with bans)
    """

    marketplace_name: str = "ozon"
    base_url: str = "https://www.ozon.ru"
    rate_limit: float = 0.5  # Ozon aggressively bans scrapers

    def __init__(
        self,
        marketplace_id: int = 1,
        proxy_url: str | None = None,
    ) -> None:
        """Initialize Ozon scraper.

        Args:
            marketplace_id: Database ID for Ozon marketplace.
            proxy_url: Optional proxy URL.
        """
        super().__init__(proxy_url=proxy_url)
        self._marketplace_id = marketplace_id

    def _parse_price(self, price_str: str | None) -> float | None:
        """Parse price string to float.

        Args:
            price_str: Price string like "1 234 ₽" or "1234".

        Returns:
            Price as float or None if parsing fails.
        """
        if not price_str:
            return None

        # Remove all non-digit characters except decimal separator
        cleaned = re.sub(r"[^\d,.]", "", price_str)
        cleaned = cleaned.replace(",", ".")

        try:
            return float(cleaned)
        except ValueError:
            logger.warning("Failed to parse price: %s", price_str)
            return None

    def _extract_json_state(self, html: str) -> dict[str, Any] | None:
        """Extract JSON state data from page HTML.

        Ozon embeds product data in __NUXT_DATA__ or data-state attributes.

        Args:
            html: Raw HTML content.

        Returns:
            Extracted JSON data or None.
        """
        tree = HTMLParser(html)

        # Try to find data in script tags
        for script in tree.css("script"):
            text = script.text(strip=True)
            if not text:
                continue

            # Look for window.__NUXT_DATA__
            if "__NUXT_DATA__" in text:
                match = re.search(r"__NUXT_DATA__\s*=\s*(\[.+?\])\s*;?\s*$", text, re.DOTALL)
                if match:
                    try:
                        return {"nuxt_data": json.loads(match.group(1))}
                    except json.JSONDecodeError:
                        continue

            # Look for JSON in script type="application/json"
            if text.startswith("{") or text.startswith("["):
                try:
                    data = json.loads(text)
                    if isinstance(data, dict) and ("items" in data or "products" in data):
                        return data
                except json.JSONDecodeError:
                    continue

        # Try data-state attributes on widgets
        for element in tree.css("[data-state]"):
            data_state = element.attributes.get("data-state", "")
            if data_state:
                try:
                    data = json.loads(data_state)
                    if "items" in data or "products" in data:
                        return data
                except json.JSONDecodeError:
                    continue

        return None

    def _parse_search_item(self, item: dict[str, Any]) -> dict[str, Any] | None:
        """Parse single item from search results.

        Args:
            item: Raw item data from JSON.

        Returns:
            Normalized product data or None.
        """
        try:
            product_id = str(item.get("id", ""))
            if not product_id:
                return None

            # Extract title from mainState
            title = None
            price = None
            original_price = None
            image_url = None
            rating = None
            reviews_count = 0

            main_state = item.get("mainState", [])
            for state in main_state:
                atom = state.get("atom", {})
                atom_type = atom.get("type", "")

                if atom_type == "title":
                    text_atom = atom.get("textAtom", {})
                    title = text_atom.get("text", "")

                elif atom_type == "price":
                    price_atom = atom.get("priceAtom", {})
                    price = self._parse_price(price_atom.get("price"))
                    original_price = self._parse_price(price_atom.get("originalPrice"))

                elif atom_type == "rating":
                    rating_atom = atom.get("ratingAtom", {})
                    rating = rating_atom.get("rating")
                    reviews_count = rating_atom.get("count", 0)

            # Fallback: try direct fields
            if not title:
                title = item.get("name") or item.get("title", "")

            if not price:
                price = self._parse_price(str(item.get("price", "")))

            if not title or not price:
                return None

            # Image URL
            tile_image = item.get("tileImage", {})
            image_url = tile_image.get("url") or item.get("image")
            if image_url and not image_url.startswith("http"):
                image_url = f"https:{image_url}"

            # Additional images
            images = []
            for img in item.get("images", []):
                url = img if isinstance(img, str) else img.get("url", "")
                if url:
                    images.append(url if url.startswith("http") else f"https:{url}")

            return {
                "external_id": product_id,
                "title": title,
                "price": price,
                "original_price": original_price,
                "image_url": image_url,
                "images": images,
                "rating": rating,
                "reviews_count": reviews_count,
                "url": f"{self.base_url}/product/{product_id}",
            }

        except Exception as e:
            logger.warning("Failed to parse item: %s", e)
            return None

    def _create_product(self, data: dict[str, Any]) -> ProductCreate:
        """Create ProductCreate schema from parsed data.

        Args:
            data: Normalized product data.

        Returns:
            ProductCreate instance.
        """
        # Import here to avoid circular imports
        from app.schemas.product import ProductCreate

        return ProductCreate(
            external_id=data["external_id"],
            marketplace_id=self._marketplace_id,
            title=data["title"],
            current_price=data["price"],
            original_price=data.get("original_price"),
            url=data["url"],
            image_url=data.get("image_url"),
            images=data.get("images", []),
            rating=data.get("rating"),
            reviews_count=data.get("reviews_count", 0),
        )

    async def search(
        self,
        query: str,
        page: int = 1,
        **kwargs,
    ) -> list[ProductCreate]:
        """Search for products on Ozon.

        Args:
            query: Search query string.
            page: Page number (1-indexed).
            **kwargs: Additional parameters (not used).

        Returns:
            List of found products.

        Example:
            >>> async with OzonScraper() as scraper:
            ...     products = await scraper.search("iphone 15")
            ...     print(f"Found {len(products)} products")
        """
        url = f"{self.base_url}/search/?text={query}&page={page}"

        logger.info("Searching Ozon: query=%s, page=%d", query, page)

        try:
            html = await self.fetch_js(
                url,
                wait_selector='[data-widget="searchResultsV2"]',
                wait_timeout=15000,
            )
        except Exception as e:
            logger.error("Failed to fetch search page: %s", e)
            return []

        return self._parse_search_results(html)

    def _parse_search_results(self, html: str) -> list[ProductCreate]:
        """Parse search results page.

        Args:
            html: Raw HTML content.

        Returns:
            List of parsed products.
        """
        products: list[ProductCreate] = []

        # Try JSON extraction first
        json_data = self._extract_json_state(html)
        if json_data:
            items = json_data.get("items", json_data.get("products", []))
            for item in items:
                parsed = self._parse_search_item(item)
                if parsed:
                    products.append(self._create_product(parsed))

        # Fallback to HTML parsing if no JSON found
        if not products:
            products = self._parse_search_html(html)

        logger.info("Parsed %d products from search results", len(products))
        return products

    def _parse_search_html(self, html: str) -> list[ProductCreate]:
        """Fallback HTML parsing for search results.

        Args:
            html: Raw HTML content.

        Returns:
            List of parsed products.
        """
        products: list[ProductCreate] = []
        tree = HTMLParser(html)

        # Find product cards
        cards = tree.css('[data-widget="searchResultsV2"] .tile-root, .j8t')

        for card in cards:
            try:
                # Extract link to get product ID
                link = card.css_first("a[href*='/product/']")
                if not link:
                    continue

                href = link.attributes.get("href", "")
                match = re.search(r"/product/[^/]+-(\d+)/", href)
                if not match:
                    match = re.search(r"/product/(\d+)", href)
                if not match:
                    continue

                product_id = match.group(1)

                # Title
                title_el = card.css_first(".tsBody500Medium, .tile-title")
                title = title_el.text(strip=True) if title_el else ""

                if not title:
                    continue

                # Price
                price_el = card.css_first('[data-widget="searchResultsV2"] .c3015-a1')
                if not price_el:
                    price_el = card.css_first(".price-number, .c3015-a0")

                price = self._parse_price(price_el.text() if price_el else None)
                if not price:
                    continue

                # Image
                img = card.css_first("img")
                image_url = img.attributes.get("src") if img else None

                products.append(
                    self._create_product(
                        {
                            "external_id": product_id,
                            "title": title,
                            "price": price,
                            "url": f"{self.base_url}/product/{product_id}",
                            "image_url": image_url,
                        }
                    )
                )

            except Exception as e:
                logger.warning("Failed to parse card: %s", e)
                continue

        return products

    async def get_product(self, product_id: str) -> ProductCreate | None:
        """Get detailed product information.

        Args:
            product_id: Ozon product ID.

        Returns:
            Product data or None if not found.
        """
        url = f"{self.base_url}/product/{product_id}"

        logger.info("Fetching Ozon product: %s", product_id)

        try:
            html = await self.fetch_js(
                url,
                wait_selector='[data-widget="webPrice"]',
                wait_timeout=15000,
            )
        except Exception as e:
            logger.error("Failed to fetch product page: %s", e)
            return None

        return self._parse_product_page(html, product_id)

    def _parse_product_page(self, html: str, product_id: str) -> ProductCreate | None:
        """Parse product detail page.

        Args:
            html: Raw HTML content.
            product_id: Product ID for fallback.

        Returns:
            Product data or None.
        """
        tree = HTMLParser(html)

        # Title
        title_el = tree.css_first('h1[data-widget="webProductHeading"], h1')
        title = title_el.text(strip=True) if title_el else None

        if not title:
            logger.warning("No title found for product %s", product_id)
            return None

        # Price
        price_el = tree.css_first('[data-widget="webPrice"] span, .price-number')
        price = self._parse_price(price_el.text() if price_el else None)

        if not price:
            # Try alternative price location
            price_el = tree.css_first(".c3015-a0, .c3015-a1")
            price = self._parse_price(price_el.text() if price_el else None)

        if not price:
            logger.warning("No price found for product %s", product_id)
            return None

        # Original price
        original_el = tree.css_first('[data-widget="webPrice"] del, .original-price')
        original_price = self._parse_price(original_el.text() if original_el else None)

        # Brand
        brand = None
        brand_el = tree.css_first('[data-widget="webBrand"] a, .brand-name')
        if brand_el:
            brand = brand_el.text(strip=True)

        # Rating
        rating = None
        rating_el = tree.css_first('[data-widget="webSingleProductScore"] span')
        if rating_el:
            try:
                rating = float(rating_el.text(strip=True))
            except ValueError:
                pass

        # Reviews count
        reviews_count = 0
        reviews_el = tree.css_first('[data-widget="webReviewProductScore"] span')
        if reviews_el:
            text = reviews_el.text(strip=True)
            match = re.search(r"(\d[\d\s]*)", text)
            if match:
                reviews_count = int(match.group(1).replace(" ", ""))

        # Description
        description = None
        desc_el = tree.css_first('[data-widget="webDescription"]')
        if desc_el:
            description = desc_el.text(strip=True)[:5000]  # Limit length

        # Images
        images = []
        for img in tree.css('[data-widget="webGallery"] img'):
            src = img.attributes.get("src", "")
            if src and "wc" in src:  # Filter thumbnails
                # Get full-size image URL
                full_url = re.sub(r"/wc\d+/", "/wc1000/", src)
                images.append(full_url)

        # Main image
        image_url = images[0] if images else None

        # Availability
        is_available = True
        out_of_stock = tree.css_first('[data-widget="webOutOfStock"]')
        if out_of_stock:
            is_available = False

        # Seller
        seller_name = None
        seller_el = tree.css_first('[data-widget="webCurrentSeller"] a')
        if seller_el:
            seller_name = seller_el.text(strip=True)

        # Specifications
        specs = {}
        for row in tree.css('[data-widget="webCharacteristics"] dl'):
            dt = row.css_first("dt")
            dd = row.css_first("dd")
            if dt and dd:
                key = dt.text(strip=True)
                value = dd.text(strip=True)
                if key and value:
                    specs[key] = value

        from app.schemas.product import ProductCreate

        return ProductCreate(
            external_id=product_id,
            marketplace_id=self._marketplace_id,
            title=title,
            description=description,
            brand=brand,
            current_price=price,
            original_price=original_price,
            url=f"{self.base_url}/product/{product_id}",
            image_url=image_url,
            images=images,
            rating=rating,
            reviews_count=reviews_count,
            is_available=is_available,
            seller_name=seller_name,
            specs=specs,
        )

    async def get_category(
        self,
        category_url: str,
        max_pages: int = 10,
    ) -> AsyncGenerator[ProductCreate, None]:
        """Iterate over products in a category.

        Args:
            category_url: URL of the category page.
            max_pages: Maximum number of pages to scrape.

        Yields:
            Product data for each product.

        Example:
            >>> async with OzonScraper() as scraper:
            ...     async for product in scraper.get_category(
            ...         "https://www.ozon.ru/category/smartfony-15502/"
            ...     ):
            ...         print(product.title)
        """
        logger.info("Scraping Ozon category: %s", category_url)

        for page in range(1, max_pages + 1):
            # Add page parameter
            separator = "&" if "?" in category_url else "?"
            url = f"{category_url}{separator}page={page}"

            try:
                html = await self.fetch_js(
                    url,
                    wait_selector='[data-widget="searchResultsV2"]',
                    wait_timeout=15000,
                )
            except Exception as e:
                logger.error("Failed to fetch category page %d: %s", page, e)
                break

            products = self._parse_search_results(html)

            if not products:
                logger.info("No products on page %d, stopping", page)
                break

            for product in products:
                yield product

            logger.info("Scraped page %d: %d products", page, len(products))
