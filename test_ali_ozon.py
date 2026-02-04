from playwright.sync_api import sync_playwright
import time
import re

def parse_price(price_str):
    """Извлекает число из строки цены"""
    if not price_str:
        return None
    # Берём первое число из строки
    match = re.search(r'[\d\s]+', price_str.replace(' ', ''))
    if match:
        cleaned = re.sub(r'\s', '', match.group())
        return int(cleaned) if cleaned else None
    return None

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    
    # === OZON ===
    print('\n=== Testing Ozon ===')
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    page.goto('https://www.ozon.ru/search/?text=iphone%2016&from_global=true')
    time.sleep(6)
    page.evaluate('window.scrollBy(0, 500)')
    time.sleep(2)
    
    ozon_products = page.evaluate("""() => {
        const results = [];
        
        // Находим все карточки товаров
        const cards = document.querySelectorAll('[data-widget="searchResultsV2"] > div > div');
        
        cards.forEach(card => {
            // Ищем ссылку на товар
            const linkEl = card.querySelector('a[href*="/product/"]');
            if (!linkEl) return;
            
            // Название - ищем в span внутри ссылки
            const titleEl = linkEl.querySelector('span') || linkEl;
            let title = '';
            
            // Пробуем найти нормальное название
            const spans = card.querySelectorAll('span');
            for (const span of spans) {
                const text = span.innerText?.trim();
                if (text && text.length > 20 && text.length < 150 && !text.includes('') && !text.includes('баллов')) {
                    title = text;
                    break;
                }
            }
            
            // Цена - ищем элемент с 
            let price = '';
            const allText = card.innerText || '';
            const priceMatch = allText.match(/(\d[\d\s]*)\s*/);
            if (priceMatch) {
                price = priceMatch[1].replace(/\s/g, '') + ' ';
            }
            
            if (title && title.length > 10) {
                results.push({
                    title: title.slice(0, 100),
                    price: price,
                    url: linkEl.href,
                    marketplace: 'ozon'
                });
            }
        });
        
        // Убираем дубли
        const seen = new Set();
        return results.filter(p => {
            const key = p.title.slice(0, 30);
            if (seen.has(key)) return false;
            seen.add(key);
            return true;
        });
    }""")
    
    print(f'Ozon: {len(ozon_products)} products')
    for p in ozon_products[:5]:
        print(f"  {p['price']:>12}  {p['title'][:45]}")
    
    context.close()
    time.sleep(2)
    
    # === ALIEXPRESS ===
    print('\n=== Testing AliExpress ===')
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    page.goto('https://aliexpress.ru/wholesale?SearchText=iphone%2016')
    time.sleep(5)
    page.evaluate('window.scrollBy(0, 500)')
    time.sleep(2)
    
    ali_products = page.evaluate("""() => {
        const results = [];
        
        // Ищем карточки товаров
        const cards = document.querySelectorAll('[class*="SearchProductFeed"] > div, [class*="product-snippet"], [data-widget-cid]');
        
        // Если не нашли карточки, пробуем по ссылкам
        const items = cards.length > 0 ? cards : document.querySelectorAll('a[href*="/item/"]');
        
        items.forEach(item => {
            let card = item;
            let linkEl = item.tagName === 'A' ? item : item.querySelector('a[href*="/item/"]');
            
            if (!linkEl) return;
            
            // Название
            let title = '';
            const titleEl = card.querySelector('[class*="title"]') || card.querySelector('h3') || card.querySelector('h2');
            if (titleEl) {
                title = titleEl.innerText?.trim();
            }
            if (!title || title.length < 10) {
                // Fallback - текст ссылки
                title = linkEl.innerText?.trim()?.slice(0, 100);
            }
            
            // Цена - ищем элемент с ценой
            let price = '';
            const priceEl = card.querySelector('[class*="price"]') || card.querySelector('[class*="Price"]');
            if (priceEl) {
                const priceText = priceEl.innerText?.trim();
                // Берём первую цену (до скидки может быть вторая)
                const match = priceText?.match(/([\d\s]+)\s*/);
                if (match) {
                    price = match[1].replace(/\s/g, '') + ' ';
                }
            }
            
            // Фильтруем мусор
            if (title && title.length > 10 && !title.includes('СКИДКА') && !title.includes('купон')) {
                results.push({
                    title: title.slice(0, 100),
                    price: price,
                    url: linkEl.href,
                    marketplace: 'aliexpress'
                });
            }
        });
        
        // Убираем дубли
        const seen = new Set();
        return results.filter(p => {
            if (seen.has(p.url)) return false;
            seen.add(p.url);
            return true;
        });
    }""")
    
    print(f'AliExpress: {len(ali_products)} products')
    for p in ali_products[:5]:
        print(f"  {p['price']:>12}  {p['title'][:45]}")
    
    context.close()
    browser.close()
