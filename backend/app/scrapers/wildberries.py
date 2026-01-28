"""Wildberries marketplace scraper.

Scraper for wildberries.ru using their public API endpoints.
Unlike Ozon, Wildberries exposes public APIs that can be used directly.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, AsyncGenerator

from app.scrapers.base import BaseScraper, ScraperError

if TYPE_CHECKING:
    from app.schemas.product import ProductCreate

logger = logging.getLogger(__name__)


class WildberriesAPIError(ScraperError):
    """Error from Wildberries API."""

    pass


class WildberriesScraper(BaseScraper):
    """Scraper for Wildberries marketplace.

    Wildberries has public API endpoints for search and product data,
    making scraping much simpler than with Ozon. No browser automation needed.

    Attributes:
        marketplace_name: "wildberries"
        base_url: "https://www.wildberries.ru"
        rate_limit: 2.0 requests per second
    """

    marketplace_name: str = "wildberries"
    base_url: str = "https://www.wildberries.ru"
    rate_limit: float = 2.0

    # API endpoints
    _search_api: str = "https://search.wb.ru/exactmatch/ru/common/v7/search"
    _card_api: str = "https://card.wb.ru/cards/v2/detail"
    _seller_api: str = "https://www.wildberries.ru/webapi/seller/data/short"

    # Default destination (Moscow region)
    _default_dest: int = -1257786

    def __init__(
        self,
        marketplace_id: int = 2,
        proxy_url: str | None = None,
        dest: int | None = None,
    ) -> None:
        """Initialize Wildberries scraper.

        Args:
            marketplace_id: Database ID for Wildberries marketplace.
            proxy_url: Optional proxy URL.
            dest: Destination region ID (default: Moscow).
        """
        super().__init__(proxy_url=proxy_url)
        self._marketplace_id = marketplace_id
        self._dest = dest or self._default_dest

    def _get_headers(self) -> dict[str, str]:
        """Override headers for WB API compatibility."""
        headers = super()._get_headers()
        headers.update(
            {
                "Accept": "application/json",
                "Origin": self.base_url,
                "Referer": f"{self.base_url}/",
            }
        )
        return headers

    @staticmethod
    def _get_basket_host(vol: int) -> str:
        """Determine CDN basket host based on volume number.

        Wildberries uses multiple CDN hosts based on product ID ranges.

        Args:
            vol: Volume number (product_id // 100000).

        Returns:
            Basket host number as string.
        """
        if vol <= 143:
            return "01"
        elif vol <= 287:
            return "02"
        elif vol <= 431:
            return "03"
        elif vol <= 719:
            return "04"
        elif vol <= 1007:
            return "05"
        elif vol <= 1061:
            return "06"
        elif vol <= 1115:
            return "07"
        elif vol <= 1169:
            return "08"
        elif vol <= 1313:
            return "09"
        elif vol <= 1601:
            return "10"
        elif vol <= 1655:
            return "11"
        elif vol <= 1919:
            return "12"
        elif vol <= 2045:
            return "13"
        elif vol <= 2189:
            return "14"
        elif vol <= 2405:
            return "15"
        elif vol <= 2621:
            return "16"
        else:
            return "17"

    def _build_image_url(
        self,
        product_id: int,
        photo_number: int = 1,
        size: str = "big",
    ) -> str:
        """Build image URL for a product.

        Args:
            product_id: Product ID.
            photo_number: Photo number (1-indexed).
            size: Image size ('big', 'c516x688', etc.).

        Returns:
            Full image URL.
        """
        vol = product_id // 100000
        part = product_id // 1000
        basket = self._get_basket_host(vol)

        return (
            f"https://basket-{basket}.wbbasket.ru/"
            f"vol{vol}/part{part}/{product_id}/images/{size}/{photo_number}.webp"
        )

    def _parse_api_product(self, item: dict[str, Any]) -> dict[str, Any]:
        """Parse product data from API response.

        Args:
            item: Raw product data from API.

        Returns:
            Normalized product data.
        """
        product_id = item.get("id", 0)

        # WB stores prices in kopecks
        sale_price = item.get("sizes", [{}])[0].get("price", {}).get("product", 0) / 100
        original_price = item.get("sizes", [{}])[0].get("price", {}).get("basic", 0) / 100

        # Fallback to old price fields
        if not sale_price:
            sale_price = item.get("salePriceU", 0) / 100
        if not original_price:
            original_price = item.get("priceU", 0) / 100

        # Check availability
        is_available = any(
            size.get("stocks", []) for size in item.get("sizes", [])
        )

        # Rating
        rating = item.get("reviewRating", item.get("rating"))

        # Reviews count
        reviews_count = item.get("feedbacks", item.get("feedbackCount", 0))

        # Build image URLs
        image_url = self._build_image_url(product_id)
        images = [self._build_image_url(product_id, i) for i in range(1, 11)]

        return {
            "external_id": str(product_id),
            "title": item.get("name", ""),
            "brand": item.get("brand", ""),
            "price": sale_price,
            "original_price": original_price if original_price > sale_price else None,
            "url": f"{self.base_url}/catalog/{product_id}/detail.aspx",
            "image_url": image_url,
            "images": images,
            "rating": rating,
            "reviews_count": reviews_count,
            "is_available": is_available,
            "seller_id": item.get("supplierId"),
            "seller_name": item.get("supplier"),
            "category_id": item.get("subjectId"),
            "category_name": item.get("subjectParentName"),
            "colors": [c.get("name") for c in item.get("colors", [])],
        }

    def _create_product(self, data: dict[str, Any]) -> ProductCreate:
        """Create ProductCreate schema from parsed data.

        Args:
            data: Normalized product data.

        Returns:
            ProductCreate instance.
        """
        from app.schemas.product import ProductCreate

        return ProductCreate(
            external_id=data["external_id"],
            marketplace_id=self._marketplace_id,
            title=data["title"],
            brand=data.get("brand"),
            current_price=data["price"],
            original_price=data.get("original_price"),
            url=data["url"],
            image_url=data.get("image_url"),
            images=data.get("images", []),
            rating=data.get("rating"),
            reviews_count=data.get("reviews_count", 0),
            is_available=data.get("is_available", True),
            seller_name=data.get("seller_name"),
        )

    async def search(
        self,
        query: str,
        page: int = 1,
        sort: str = "popular",
        **kwargs,
    ) -> list[ProductCreate]:
        """Search for products on Wildberries.

        Args:
            query: Search query string.
            page: Page number (1-indexed).
            sort: Sort order ('popular', 'rate', 'priceup', 'pricedown', 'newly').
            **kwargs: Additional parameters.

        Returns:
            List of found products.

        Example:
            >>> async with WildberriesScraper() as scraper:
            ...     products = await scraper.search("iphone 15")
            ...     print(f"Found {len(products)} products")
        """
        params = {
            "ab_testing": "false",
            "appType": "1",
            "curr": "rub",
            "dest": self._dest,
            "page": page,
            "query": query,
            "resultset": "catalog",
            "sort": sort,
            "spp": "30",
            "suppressSpellcheck": "false",
        }

        logger.info("Searching Wildberries: query=%s, page=%d", query, page)

        try:
            data = await self.fetch_json(self._search_api, params=params)
        except Exception as e:
            logger.error("Search API error: %s", e)
            return []

        products: list[ProductCreate] = []
        items = data.get("data", {}).get("products", [])

        for item in items:
            try:
                parsed = self._parse_api_product(item)
                if parsed["price"] > 0:
                    products.append(self._create_product(parsed))
            except Exception as e:
                logger.warning("Failed to parse product: %s", e)
                continue

        logger.info("Found %d products for query '%s'", len(products), query)
        return products

    async def get_product(self, product_id: str) -> ProductCreate | None:
        """Get detailed product information.

        Args:
            product_id: Wildberries product ID (nm).

        Returns:
            Product data or None if not found.
        """
        params = {
            "appType": "1",
            "curr": "rub",
            "dest": self._dest,
            "nm": product_id,
        }

        logger.info("Fetching Wildberries product: %s", product_id)

        try:
            data = await self.fetch_json(self._card_api, params=params)
        except Exception as e:
            logger.error("Card API error: %s", e)
            return None

        products = data.get("data", {}).get("products", [])
        if not products:
            logger.warning("Product not found: %s", product_id)
            return None

        item = products[0]
        parsed = self._parse_api_product(item)

        # Fetch additional details if available
        try:
            detail = await self._fetch_product_detail(int(product_id))
            if detail:
                parsed.update(detail)
        except Exception as e:
            logger.warning("Failed to fetch product detail: %s", e)

        return self._create_product(parsed)

    async def _fetch_product_detail(self, product_id: int) -> dict[str, Any] | None:
        """Fetch additional product details.

        Args:
            product_id: Product ID.

        Returns:
            Additional product data or None.
        """
        vol = product_id // 100000
        part = product_id // 1000
        basket = self._get_basket_host(vol)

        # Card detail JSON
        detail_url = (
            f"https://basket-{basket}.wbbasket.ru/"
            f"vol{vol}/part{part}/{product_id}/info/ru/card.json"
        )

        try:
            data = await self.fetch_json(detail_url)

            result = {}

            # Description
            if "description" in data:
                result["description"] = data["description"]

            # Specifications
            if "options" in data:
                result["specs"] = {
                    opt.get("name", ""): opt.get("value", "")
                    for opt in data.get("options", [])
                    if opt.get("name") and opt.get("value")
                }

            # Composition
            if "compositions" in data:
                compositions = data.get("compositions", [])
                if compositions:
                    result["composition"] = compositions[0].get("name", "")

            return result

        except Exception:
            return None

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
        """
        # Extract subject ID from URL
        # URL format: https://www.wildberries.ru/catalog/elektronika/smartfony-i-telefony/vse-smartfony
        # or with shard: https://www.wildberries.ru/catalog/0/search.aspx?subject=515

        import re

        subject_match = re.search(r"subject[=:](\d+)", category_url)
        if subject_match:
            subject_id = subject_match.group(1)
        else:
            # Need to fetch the category page to get subject ID
            logger.warning(
                "Could not extract subject ID from URL, "
                "using URL as search query"
            )
            # Extract last path segment as query
            path_parts = category_url.rstrip("/").split("/")
            query = path_parts[-1].replace("-", " ")

            async for product in self._search_pages(query, max_pages):
                yield product
            return

        logger.info("Scraping Wildberries category: subject=%s", subject_id)

        async for product in self._search_by_subject(subject_id, max_pages):
            yield product

    async def _search_by_subject(
        self,
        subject_id: str,
        max_pages: int,
    ) -> AsyncGenerator[ProductCreate, None]:
        """Search products by subject (category) ID.

        Args:
            subject_id: WB subject ID.
            max_pages: Maximum pages to fetch.

        Yields:
            Products in the category.
        """
        for page in range(1, max_pages + 1):
            params = {
                "ab_testing": "false",
                "appType": "1",
                "curr": "rub",
                "dest": self._dest,
                "page": page,
                "subject": subject_id,
                "resultset": "catalog",
                "sort": "popular",
                "spp": "30",
            }

            try:
                data = await self.fetch_json(self._search_api, params=params)
            except Exception as e:
                logger.error("Category API error on page %d: %s", page, e)
                break

            items = data.get("data", {}).get("products", [])

            if not items:
                logger.info("No products on page %d, stopping", page)
                break

            for item in items:
                try:
                    parsed = self._parse_api_product(item)
                    if parsed["price"] > 0:
                        yield self._create_product(parsed)
                except Exception as e:
                    logger.warning("Failed to parse product: %s", e)
                    continue

            logger.info("Scraped page %d: %d products", page, len(items))

    async def _search_pages(
        self,
        query: str,
        max_pages: int,
    ) -> AsyncGenerator[ProductCreate, None]:
        """Search multiple pages.

        Args:
            query: Search query.
            max_pages: Maximum pages.

        Yields:
            Products from search.
        """
        for page in range(1, max_pages + 1):
            products = await self.search(query, page=page)

            if not products:
                break

            for product in products:
                yield product

    async def get_seller_info(self, seller_id: int) -> dict[str, Any] | None:
        """Get seller information.

        Args:
            seller_id: Wildberries seller/supplier ID.

        Returns:
            Seller data or None.
        """
        params = {"supplierId": seller_id}

        try:
            data = await self.fetch_json(self._seller_api, params=params)
            return {
                "id": data.get("id"),
                "name": data.get("name"),
                "trade_mark": data.get("trademark"),
                "legal_address": data.get("legalAddress"),
                "ogrn": data.get("ogrn"),
            }
        except Exception as e:
            logger.warning("Failed to fetch seller info: %s", e)
            return None

    async def get_similar_products(
        self,
        product_id: str,
        limit: int = 20,
    ) -> list[ProductCreate]:
        """Get similar products.

        Args:
            product_id: Product ID.
            limit: Maximum number of similar products.

        Returns:
            List of similar products.
        """
        params = {
            "appType": "1",
            "curr": "rub",
            "dest": self._dest,
            "nm": product_id,
        }

        similar_api = "https://similar-products.wildberries.ru/api/v1/similar"

        try:
            data = await self.fetch_json(similar_api, params=params)
        except Exception as e:
            logger.warning("Similar products API error: %s", e)
            return []

        products: list[ProductCreate] = []
        items = data.get("data", {}).get("products", [])[:limit]

        for item in items:
            try:
                parsed = self._parse_api_product(item)
                if parsed["price"] > 0:
                    products.append(self._create_product(parsed))
            except Exception as e:
                logger.warning("Failed to parse similar product: %s", e)
                continue

        return products
