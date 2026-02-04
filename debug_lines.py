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
            const card = link.closest('div[class]');
            data.push({ url: link.href, text: card ? card.innerText : link.innerText });
        });
        return data.slice(0, 5);
    }""")
    
    for i, item in enumerate(raw[:2]):
        text = item['text']
        lines = text.split('\n')
        print(f'\n--- Item {i+1}, lines: {len(lines)} ---')
        for j, line in enumerate(lines[:15]):
            has_rub = '' in line
            has_iphone = 'iPhone' in line
            cleaned = clean_number(line) if has_rub else ''
            print(f'  {j}: [{has_rub}][{has_iphone}] "{line[:50]}" -> {cleaned}')
    
    browser.close()
