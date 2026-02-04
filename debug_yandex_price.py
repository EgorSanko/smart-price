from playwright.sync_api import sync_playwright
import time
import re

def clean_number(s):
    return re.sub(r'\D', '', s)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    
    print('=== YANDEX DEBUG ===')
    page = browser.new_page()
    page.goto('https://market.yandex.ru/search?text=iphone%2016%20128gb')
    time.sleep(4)
    page.keyboard.press('Escape')
    time.sleep(1)
    
    products = page.evaluate("""() => {
        const results = [];
        document.querySelectorAll('[data-auto="snippet-title"]').forEach(titleEl => {
            const card = titleEl.closest('article') || titleEl.closest('[data-apiary-widget-name]');
            const linkEl = card?.querySelector('a') || titleEl.closest('a');
            const priceEl = card?.querySelector('[data-auto="price-value"]');
            const title = titleEl.innerText?.trim();
            if (title) {
                results.push({ 
                    title, 
                    price_raw: priceEl?.innerText || 'NOT FOUND',
                    price_html: priceEl?.outerHTML?.slice(0, 100) || 'NO ELEMENT'
                });
            }
        });
        return results;
    }""")
    
    print(f'Found: {len(products)}')
    for p in products[:3]:
        print(f'\nTitle: {p["title"][:50]}')
        print(f'Price raw: "{p["price_raw"]}"')
        print(f'Price HTML: {p["price_html"]}')
    
    # Попробуем другие селекторы для цены
    print('\n=== Other price selectors ===')
    selectors = page.evaluate("""() => {
        return {
            'price-value': document.querySelectorAll('[data-auto="price-value"]').length,
            'snippet-price': document.querySelectorAll('[data-auto="snippet-price-current"]').length,
            'mainPrice': document.querySelectorAll('[data-auto="mainPrice"]').length,
            'price class': document.querySelectorAll('[class*="price"]').length,
        };
    }""")
    for k, v in selectors.items():
        print(f'  {k}: {v}')
    
    browser.close()
