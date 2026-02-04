#!/usr/bin/env python3
"""Test script for browserless integration.

Run this after starting docker-compose:
    docker compose -f docker/docker-compose.dev.yml up -d
    docker compose -f docker/docker-compose.dev.yml exec backend python /app/tests/test_browserless.py

Or standalone:
    python test_browserless.py
"""

import asyncio
import os
import sys

# Set browserless endpoint if not set
os.environ.setdefault("PLAYWRIGHT_WS_ENDPOINT", "ws://browserless:3000")
os.environ.setdefault("USE_BROWSERLESS", "true")


async def test_browserless_connection():
    """Test basic connection to browserless."""
    print("=" * 60)
    print("TEST 1: Browserless Connection")
    print("=" * 60)
    
    try:
        from playwright.async_api import async_playwright
        
        ws_endpoint = os.environ.get("PLAYWRIGHT_WS_ENDPOINT", "ws://browserless:3000")
        print(f"Connecting to: {ws_endpoint}")
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(ws_endpoint)
        
        print("✅ Connected to browserless!")
        
        # Get browser info
        contexts = browser.contexts
        print(f"   Browser contexts: {len(contexts)}")
        
        # Create a page
        context = await browser.new_context()
        page = await context.new_page()
        
        # Test simple navigation
        print("   Navigating to example.com...")
        await page.goto("https://example.com", timeout=30000)
        title = await page.title()
        print(f"   Page title: {title}")
        
        await page.close()
        await context.close()
        await browser.close()
        await playwright.stop()
        
        print("✅ Browserless is working correctly!\n")
        return True
        
    except Exception as e:
        print(f"❌ Browserless connection failed: {e}\n")
        return False


async def test_wildberries_menu():
    """Test fetching WB menu (CDN - should always work)."""
    print("=" * 60)
    print("TEST 2: Wildberries Menu (CDN)")
    print("=" * 60)
    
    import httpx
    
    url = "https://static-basket-01.wbbasket.ru/vol0/data/main-menu-ru-ru-v3.json"
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(url)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   Categories: {len(data)}")
                if data:
                    print(f"   First category: {data[0].get('name', 'Unknown')}")
                print("✅ CDN is accessible!\n")
                return True
            else:
                print(f"❌ Unexpected status: {response.status_code}\n")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False


async def test_wildberries_search_httpx():
    """Test WB search without browserless (likely to fail)."""
    print("=" * 60)
    print("TEST 3: Wildberries Search (httpx only)")
    print("=" * 60)
    
    import httpx
    
    url = "https://search.wb.ru/exactmatch/ru/common/v9/search"
    params = {
        "appType": "1",
        "curr": "rub",
        "dest": "-1257786",
        "page": "1",
        "query": "iphone",
        "resultset": "catalog",
        "sort": "popular",
        "spp": "30",
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "*/*",
        "Origin": "https://www.wildberries.ru",
        "Referer": "https://www.wildberries.ru/",
    }
    
    try:
        async with httpx.AsyncClient(timeout=15, headers=headers) as client:
            response = await client.get(url, params=params)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("data", {}).get("products", [])
                print(f"   Products found: {len(products)}")
                
                if products:
                    p = products[0]
                    print(f"   First: {p.get('name', 'Unknown')[:50]}...")
                    print("✅ Direct HTTP works! (may not last)\n")
                    return True
                else:
                    print("⚠️  Empty response (possible soft block)\n")
                    return False
            else:
                print(f"❌ Blocked with status {response.status_code}\n")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False


async def test_wildberries_search_browserless():
    """Test WB search with browserless."""
    print("=" * 60)
    print("TEST 4: Wildberries Search (browserless)")
    print("=" * 60)
    
    try:
        from playwright.async_api import async_playwright
        import json
        
        ws_endpoint = os.environ.get("PLAYWRIGHT_WS_ENDPOINT", "ws://browserless:3000")
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(ws_endpoint)
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
        )
        page = await context.new_page()
        
        # Block images for speed
        await page.route("**/*.{png,jpg,jpeg,gif,webp}", lambda r: r.abort())
        
        # Build URL
        url = "https://search.wb.ru/exactmatch/ru/common/v9/search?appType=1&curr=rub&dest=-1257786&page=1&query=iphone&resultset=catalog&sort=popular&spp=30"
        
        print(f"   Fetching: {url[:60]}...")
        
        # Navigate
        response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        
        if response:
            print(f"   Status: {response.status}")
            
            if response.status == 200:
                # Get response body
                body = await page.inner_text("body")
                data = json.loads(body)
                
                products = data.get("data", {}).get("products", [])
                print(f"   Products found: {len(products)}")
                
                if products:
                    p = products[0]
                    name = p.get("name", "Unknown")[:50]
                    price = p.get("salePriceU", 0) / 100
                    print(f"   First: {name}... - {price}₽")
                    print("✅ Browserless scraping works!\n")
                    
                    await page.close()
                    await context.close()
                    await browser.close()
                    await playwright.stop()
                    return True
                    
        print("❌ Failed to get products\n")
        await page.close()
        await context.close()
        await browser.close()
        await playwright.stop()
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False


async def test_wildberries_catalog():
    """Test WB catalog endpoint (may work better)."""
    print("=" * 60)
    print("TEST 5: Wildberries Catalog API")
    print("=" * 60)
    
    import httpx
    
    # Catalog endpoint - sometimes less blocked
    url = "https://catalog.wb.ru/catalog/electronic14/catalog"
    params = {
        "appType": "1",
        "curr": "rub",
        "dest": "-1257786",
        "page": "1",
        "sort": "popular",
        "spp": "30",
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Accept": "*/*",
        "Accept-Language": "ru-RU,ru;q=0.9",
        "Origin": "https://www.wildberries.ru",
        "Referer": "https://www.wildberries.ru/",
    }
    
    try:
        await asyncio.sleep(2)  # Rate limit
        
        async with httpx.AsyncClient(timeout=15, headers=headers) as client:
            response = await client.get(url, params=params)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                products = data.get("data", {}).get("products", [])
                print(f"   Products found: {len(products)}")
                
                if products:
                    p = products[0]
                    name = p.get("name", "Unknown")[:40]
                    print(f"   First: {name}...")
                    print("✅ Catalog API works!\n")
                    return True
                else:
                    print("⚠️  Empty response\n")
                    return False
            else:
                print(f"❌ Status {response.status_code}\n")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SMART PRICE - BROWSERLESS INTEGRATION TEST")
    print("=" * 60 + "\n")
    
    results = {}
    
    # Test 1: Browserless connection
    results["browserless"] = await test_browserless_connection()
    
    # Test 2: WB Menu (CDN)
    results["wb_menu"] = await test_wildberries_menu()
    
    # Test 3: WB Search (httpx)
    results["wb_search_http"] = await test_wildberries_search_httpx()
    
    # Test 4: WB Search (browserless)
    if results["browserless"]:
        results["wb_search_browser"] = await test_wildberries_search_browserless()
    else:
        print("⏭️  Skipping browserless search test (no connection)\n")
        results["wb_search_browser"] = None
    
    # Test 5: WB Catalog
    results["wb_catalog"] = await test_wildberries_catalog()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for test, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⏭️  SKIP"
        print(f"   {test}: {status}")
    
    print()
    
    # Recommendations
    if results["wb_search_browser"]:
        print("🎉 Browserless is working! You can scrape Wildberries.")
    elif results["wb_catalog"]:
        print("💡 Catalog API works. Use it instead of search.")
    elif results["wb_search_http"]:
        print("⚠️  HTTP works now but may get blocked. Consider browserless.")
    else:
        print("❌ All scraping methods blocked. Need proxy (BrightData).")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())
