from playwright.sync_api import sync_playwright
import time
import re

def clean_number(s):
    return re.sub(r'\D', '', s)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    
    # === OZON ===
    print('\n=== OZON ===')
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
        return data.slice(0, 30);
    }""")
    
    ozon = []
    seen = set()
    for item in raw:
        lines = item['text'].split('\n')
        
        price = None
        title = None
        
        for line in lines:
            l = line.strip()
            
            # Цена: строка вида "54 936 "
            if not price and l.endswith(''):
                cleaned = clean_number(l)
                if cleaned:
                    num = int(cleaned)
                    if 30000 < num < 300000:
                        price = num
            
            # Название: содержит iPhone, длина > 30
            if not title and 'iPhone' in l and len(l) > 30:
                title = l[:100]
        
        if title and price and title not in seen:
            seen.add(title)
            ozon.append({
                'title': title,
                'price': f'{price:,} '.replace(',', ' '),
                'price_num': price,
                'url': item['url'],
                'marketplace': 'ozon'
            })
    
    print(f'Found: {len(ozon)} products')
    for prod in sorted(ozon, key=lambda x: x['price_num'])[:7]:
        print(f"  {prod['price']:>12}  {prod['title'][:45]}")
    
    page.close()
    time.sleep(2)
    
    # === ALIEXPRESS ===
    print('\n=== ALIEXPRESS ===')
    page = browser.new_page()
    page.goto('https://aliexpress.ru/wholesale?SearchText=iphone%2016')
    time.sleep(5)
    
    raw = page.evaluate("""() => {
        const data = [];
        const links = document.querySelectorAll('a[href*="/item/"]');
        const seen = new Set();
        links.forEach(link => {
            const url = link.href.split('?')[0];
            if (seen.has(url)) return;
            seen.add(url);
            const card = link.closest('div[class]');
            data.push({ url: url, text: card ? card.innerText : link.innerText });
        });
        return data.slice(0, 30);
    }""")
    
    ali = []
    seen = set()
    for item in raw:
        lines = item['text'].split('\n')
        
        price = None
        title = None
        
        for line in lines:
            l = line.strip()
            
            # Цена
            if not price and '' in l and 'купон' not in l.lower():
                cleaned = clean_number(l)
                if cleaned:
                    num = int(cleaned)
                    if 15000 < num < 300000:
                        price = num
            
            # Название
            if not title and 'iphone' in l.lower() and len(l) > 30 and 'СКИДКА' not in l:
                title = l[:100]
        
        if title and price and title not in seen:
            seen.add(title)
            ali.append({
                'title': title,
                'price': f'{price:,} '.replace(',', ' '),
                'price_num': price,
                'url': item['url'],
                'marketplace': 'aliexpress'
            })
    
    print(f'Found: {len(ali)} products')
    for prod in sorted(ali, key=lambda x: x['price_num'])[:7]:
        print(f"  {prod['price']:>12}  {prod['title'][:45]}")
    
    browser.close()
