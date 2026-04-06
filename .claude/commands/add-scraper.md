Create a new marketplace scraper for Smart Price.

Arguments: $ARGUMENTS (marketplace name, e.g. "dns", "avito", "21vek")

Steps:
1. Create `backend/app/scrapers/{marketplace}.py` following this template:

```python
"""[Marketplace] scraper."""
import httpx
import structlog

logger = structlog.get_logger()

class [Marketplace]Scraper:
    marketplace_name = "[marketplace]"
    region = "[RU or BY]"
    currency = "[RUB or BYN]"

    async def search(self, query: str) -> list[dict]:
        results = []
        # ... implementation ...
        return results
```

2. Each result dict MUST have these keys:
   - title (str), price (str formatted), price_num (float), url (str)
   - marketplace (str), image (str), shop (str), specs (str)
   - category (str), onliner_key (str)

3. Register in `backend/app/scrapers/manager.py`:
   - Add to `_register_default_parsers()`
   - Add to `_safe_search()` with lazy import

4. Add to `backend/app/api/v1/endpoints/search_stream.py`:
   - Add to `_scrape_one()` function
   - Add to `MP_DISPLAY` dict

5. Add to `frontend/src/app/page.tsx`:
   - Add to `MP_META` dict with label, color, badge class

6. Add badge CSS class to `frontend/src/globals.css` if needed

7. Test: `python -c "import asyncio; from app.scrapers.{mp} import {Mp}Scraper; print(asyncio.run({Mp}Scraper().search('iPhone 16'))[:2])"`

Reference: Look at `backend/app/scrapers/onliner.py` as the best example of a working scraper.
