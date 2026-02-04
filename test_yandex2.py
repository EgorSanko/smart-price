from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    page = browser.new_page()
    
    page.goto('https://market.yandex.ru/search?text=iphone%2016')
    time.sleep(4)
    
    page.keyboard.press('Escape')
    time.sleep(1)
    page.keyboard.press('Escape')
    time.sleep(1)
    
    products = page.evaluate("""() => {
        const results = [];
        
        // Используем найденные селекторы
        document.querySelectorAll('[data-auto="snippet-title"]').forEach(titleEl => {
            const card = titleEl.closest('article') || titleEl.closest('[data-apiary-widget-name]');
            const linkEl = card?.querySelector('a') || titleEl.closest('a');
            const priceEl = card?.querySelector('[data-auto="price-value"]') || card?.querySelector('[data-auto="snippet-price-current"]');
            
            const title = titleEl.innerText?.trim();
            const price = priceEl?.innerText?.trim() || '';
            const url = linkEl?.href || '';
            
            if (title) {
                results.push({ title, price, url, marketplace: 'yandex' });
            }
        });
        
        return results;
    }""")
    
    print(f'Found: {len(products)} products\n')
    for p in products:
        print(f"Title: {p['title'][:50]}")
        print(f"Price: {p['price']}")
        print(f"URL: {p['url'][:60]}...")
        print()
    
    browser.close()
