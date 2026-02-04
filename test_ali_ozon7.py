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
            // Берём ТОЛЬКО родителя ссылки, не поднимаемся высоко
            const card = link.closest('div[class]');
            data.push({ url: link.href, text: card ? card.innerText : link.innerText });
        });
        return data.slice(0, 30);
    }""")
    
    print(f'Raw items: {len(raw)}')
    
    ozon = []
    seen = set()
    for item in raw:
        text = item['text']
        lines = text.split('\n')
        
        # Ищем первую цену > 30000
        price = None
        for line in lines:
            if '' in line and 'баллов' not in line:
                cleaned = clean_number(line)
                if cleaned:
                    num = int(cleaned)
                    if 30000 < num < 300000:
                        price = num
                        break
        
        # Ищем название
        title = None
        for line in lines:
            l = line.strip()
            if ('iPhone' in l or 'Смартфон' in l) and '' not in l and len(l) > 20:
                title = l[:100]
                break
        
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
    for prod in sorted(ozon, key=lambda x: x['price_num'])[:5]:
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
    
    print(f'Raw items: {len(raw)}')
    
    ali = []
    seen = set()
    for item in raw:
        text = item['text']
        lines = text.split('\n')
        
        price = None
        for line in lines:
            if '' in line and 'купон' not in line.lower():
                cleaned = clean_number(line)
                if cleaned:
                    num = int(cleaned)
                    if 15000 < num < 300000:
                        price = num
                        break
        
        title = None
        for line in lines:
            l = line.strip()
            if ('iphone' in l.lower() or 'смартфон' in l.lower()) and '' not in l and 'СКИДКА' not in l:
                if len(l) > 20:
                    title = l[:100]
                    break
        
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
    for prod in sorted(ali, key=lambda x: x['price_num'])[:5]:
        print(f"  {prod['price']:>12}  {prod['title'][:45]}")
    
    browser.close()
