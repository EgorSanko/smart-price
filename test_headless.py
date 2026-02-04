import asyncio
from undetected_playwright import async_playwright
import urllib.parse

async def test_headless():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = 'https://www.wildberries.ru/catalog/0/search.aspx?search=iphone'
        print(f'Opening: {url}')
        await page.goto(url)
        await page.wait_for_timeout(5000)
        
        cards = await page.query_selector_all('[data-nm-id]')
        print(f'Found: {len(cards)} products')
        
        await browser.close()

asyncio.run(test_headless())
