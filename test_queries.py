from playwright.sync_api import sync_playwright
import urllib.parse
import time

queries = [
    "айфон 16 128",
    "iphone 16 128gb", 
    "эпл телефон 16",
    "самсунг галакси с24",
    "samsung s24 ultra",
    "ксяоми 14",
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    page = browser.new_page()
    
    for query in queries:
        url = f'https://www.wildberries.ru/catalog/0/search.aspx?search={urllib.parse.quote(query)}'
        print(f'\n=== Query: "{query}" ===')
        page.goto(url)
        time.sleep(4)
        
        count = page.query_selector_all('[data-nm-id]')
        title = page.title()
        
        # Первый товар
        first = page.query_selector('[data-nm-id] .product-card__name')
        first_name = first.inner_text() if first else 'N/A'
        
        print(f'Results: {len(count)} products')
        print(f'First: {first_name[:50]}')
    
    browser.close()
