Test a marketplace scraper with a real HTTP request.

Usage: /test-scraper [marketplace] [query]

Run this Python test against the specified scraper:

```python
import asyncio

async def test():
    marketplace = "$ARGUMENTS".split()[0] if "$ARGUMENTS" else "onliner"
    query = " ".join("$ARGUMENTS".split()[1:]) if len("$ARGUMENTS".split()) > 1 else "iPhone 16 Pro"

    if marketplace == "onliner":
        from app.scrapers.onliner import OnlinerScraper
        scraper = OnlinerScraper()
    elif marketplace == "yandex":
        from app.scrapers.yandex_market import YandexMarketScraper
        scraper = YandexMarketScraper()
    elif marketplace in ("wb", "wildberries"):
        from app.scrapers.wildberries import WildberriesScraper
        scraper = WildberriesScraper()
    else:
        print(f"Unknown marketplace: {marketplace}")
        return

    results = await scraper.search(query)
    print(f"\n{'='*60}")
    print(f"  {scraper.marketplace_name}: '{query}' → {len(results)} results")
    print(f"{'='*60}")
    for i, r in enumerate(results[:10]):
        print(f"  {i+1}. {r['title'][:60]}")
        print(f"     {r['price']} | {r['shop']} | {'🖼️' if r.get('image') else '❌'} img")
        print(f"     {r['url'][:70]}")

    if not results:
        print("  ❌ No results — scraper may be blocked or broken")
    else:
        # Validation
        assert all(r["price_num"] > 0 for r in results), "Invalid prices!"
        assert all(r["url"].startswith("http") for r in results), "Invalid URLs!"
        print(f"\n  ✅ All {len(results)} products valid")

asyncio.run(test())
```

Run from: backend/ directory
Example: /test-scraper onliner Samsung Galaxy S25
