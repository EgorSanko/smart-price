from playwright.sync_api import sync_playwright
import time
import re

def parse_ozon_card(text):
    """Парсим текст карточки Ozon"""
    lines = text.split('\n')
    
    # Ищем цену > 30000
    price = None
    for line in lines:
        matches = re.findall(r'(\d[\d\s]*)\s*', line)
        for m in matches:
            num = int(m.replace(' ', '').replace('\xa0', ''))
            if 30000 < num < 500000:
                price = num
                break
        if price:
            break
    
    # Ищем название
    title = None
    for line in lines:
        l = line.strip()
        if len(l) > 30 and ('iPhone' in l or 'Смартфон' in l) and '' not in l:
            title = l[:100]
            break
    
    return title, price

def parse_ali_card(text):
    """Парсим текст карточки AliExpress"""
    lines = text.split('\n')
    
    # Ищем цену
    price = None
    for line in lines:
        matches = re.findall(r'(\d[\d\s]*)\s*', line)
        for m in matches:
            num = int(m.replace(' ', '').replace('\xa0', ''))
            if 10000 < num < 500000:
                price = num
                break
        if price:
            break
    
    # Ищем название
    title = None
    for line in lines:
        l = line.strip()
        if len(l) > 30 and ('iphone' in l.lower() or 'смартфон' in l.lower()):
            if '' not in l and 'СКИДКА' not in l and 'купон' not in l.lower():
                title = l[:100]
                break
    
    return title, price

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    
    # === OZON ===
    print('\n=== OZON ===')
    page = browser.new_page()
    page.goto('https://www.ozon.ru/search/?text=iphone%2016')
    time.sleep(6)
    
    # Получаем сырые данные
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
            
            data.push({
                url: link.href,
                text: card ? card.innerText : ''
            });
        });
        return data.slice(0, 20);
    }""")
    
    ozon = []
    seen_titles = set()
    for item in raw:
        title, price = parse_ozon_card(item['text'])
        if title and price and title not in seen_titles:
            seen_titles.add(title)
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
            
            let card = link.parentElement;
            for (let i = 0; i < 6; i++) {
                if (card && card.parentElement) card = card.parentElement;
            }
            
            data.push({
                url: url,
                text: card ? card.innerText : ''
            });
        });
        return data.slice(0, 30);
    }""")
    
    ali = []
    seen_titles = set()
    for item in raw:
        title, price = parse_ali_card(item['text'])
        if title and price and title not in seen_titles:
            seen_titles.add(title)
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
