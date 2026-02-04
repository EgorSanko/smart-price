from playwright.sync_api import sync_playwright
import urllib.parse
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    page = browser.new_page()
    
    # Сначала главная для cookies
    page.goto('https://www.wildberries.ru/')
    time.sleep(3)
    
    # Теперь поиск
    query = "iphone 16 128"
    url = f'https://www.wildberries.ru/catalog/0/search.aspx?search={urllib.parse.quote(query)}'
    print(f'Searching: {query}')
    page.goto(url)
    time.sleep(6)
    
    count = page.query_selector_all('[data-nm-id]')
    print(f'Results: {len(count)}')
    
    if count:
        first = page.query_selector('[data-nm-id] .product-card__name')
        print(f'First: {first.inner_text().strip()[:50] if first else "N/A"}')
    
    input("Press Enter to close...")
    browser.close()
