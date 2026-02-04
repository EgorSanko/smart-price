from playwright.sync_api import sync_playwright
import time
import re

def clean_number(s):
    return re.sub(r'\D', '', s)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    
    print('=== YANDEX FIX ===')
    page = browser.new_page()
    page.goto('https://market.yandex.ru/search?text=iphone%2016%20128gb')
    time.sleep(4)
    
    # Закрываем попапы
    page.keyboard.press('Escape')
    time.sleep(0.5)
    page.keyboard.press('Escape')
    time.sleep(0.5)
    
    # Принимаем cookies
    try:
        page.click('button:has-text("Allow all")', timeout=2000)
    except:
        pass
    time.sleep(1)
    
    products = page.evaluate("""() => {
        const results = [];
        document.querySelectorAll('[data-auto="snippet-title"]').forEach(titleEl => {
            const card = titleEl.closest('article') || titleEl.closest('[data-apiary-widget-name]');
            const linkEl = card?.querySelector('a') || titleEl.closest('a');
            
            // Используем правильный селектор для цены
            const priceEl = card?.querySelector('[data-auto="snippet-price-current"]');
            
            const title = titleEl.innerText?.trim();
            const price = priceEl?.innerText?.trim() || '';
            
            if (title) {
                results.push({ 
                    title, 
                    price,
                    url: linkEl?.href || '',
                    marketplace: 'yandex'
                });
            }
        });
        return results;
    }""")
    
    print(f'Found: {len(products)}')
    for p in products[:5]:
        cleaned = clean_number(p['price'])
        price_num = int(cleaned) if cleaned else 0
        print(f'  {price_num:>8,} ₽  {p["title"][:45]}')
    
    browser.close()
