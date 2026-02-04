from playwright.sync_api import sync_playwright
import time
import re

def clean_number(s):
    return re.sub(r'\D', '', s)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    
    # === OZON ===
    print('\n=== OZON DEBUG ===')
    page = browser.new_page()
    page.goto('https://www.ozon.ru/search/?text=iphone%2016')
    time.sleep(6)
    
    raw = page.evaluate("""() => {
        const data = [];
        const links = document.querySelectorAll('a[href*="/product/"]');
        const seen = new Set();
        links.forEach(link => {
            if (seen.has(link.href)) return;
            seen.add(link.href);
            let card = link.parentElement;
            for (let i = 0; i < 6; i++) {
                if (card && card.parentElement) card = card.parentElement;
            }
            data.push({ url: link.href, text: card ? card.innerText : '' });
        });
        return data.slice(0, 5);
    }""")
    
    print(f'Raw cards: {len(raw)}')
    
    for i, item in enumerate(raw[:2]):
        print(f'\n--- Card {i+1} ---')
        print(f'URL: {item["url"][:60]}...')
        text = item['text']
        print(f'Text length: {len(text)}')
        
        # Показываем строки с 
        lines = text.split('\n')
        print('Lines with price:')
        for line in lines:
            if '' in line:
                print(f'  "{line[:60]}"')
        
        # Показываем строки с iPhone
        print('Lines with iPhone:')
        for line in lines:
            if 'iPhone' in line or 'Смартфон' in line:
                print(f'  "{line[:60]}"')
    
    page.close()
    browser.close()
