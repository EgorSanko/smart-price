from playwright.sync_api import sync_playwright
import time
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    
    # === OZON ===
    print('\n=== OZON ===')
    page = browser.new_page()
    page.goto('https://www.ozon.ru/search/?text=iphone%2016')
    time.sleep(6)
    page.evaluate('window.scrollBy(0, 500)')
    time.sleep(2)
    
    ozon = page.evaluate("""() => {
        const results = [];
        const links = document.querySelectorAll('a[href*="/product/"]');
        const seen = new Set();
        
        links.forEach(link => {
            const href = link.href;
            if (seen.has(href)) return;
            
            // Поднимаемся к карточке
            let card = link.parentElement;
            for (let i = 0; i < 5; i++) {
                if (card.parentElement) card = card.parentElement;
            }
            
            const text = card.innerText || '';
            
            // Ищем цену - первое число перед 
            const priceMatch = text.match(/([\d\s]+)\s*/);
            const price = priceMatch ? priceMatch[1].replace(/\s/g, '') : '';
            
            // Ищем название - строка с "iPhone" или "Смартфон"
            const lines = text.split('\n').filter(l => l.trim().length > 20);
            let title = '';
            for (const line of lines) {
                if ((line.includes('iPhone') || line.includes('Смартфон') || line.includes('Apple')) 
                    && !line.includes('') && line.length < 150) {
                    title = line.trim();
                    break;
                }
            }
            
            if (title && price) {
                seen.add(href);
                results.push({
                    title: title.slice(0, 100),
                    price: price + ' ',
                    price_num: parseInt(price) || 0,
                    url: href,
                    marketplace: 'ozon'
                });
            }
        });
        
        return results.slice(0, 15);
    }""")
    
    print(f'Found: {len(ozon)} products')
    for p in ozon[:5]:
        print(f"  {p['price']:>12}  {p['title'][:45]}")
    
    page.close()
    time.sleep(2)
    
    # === ALIEXPRESS ===
    print('\n=== ALIEXPRESS ===')
    page = browser.new_page()
    page.goto('https://aliexpress.ru/wholesale?SearchText=iphone%2016')
    time.sleep(5)
    page.evaluate('window.scrollBy(0, 500)')
    time.sleep(2)
    
    ali = page.evaluate("""() => {
        const results = [];
        const links = document.querySelectorAll('a[href*="/item/"]');
        const seen = new Set();
        
        links.forEach(link => {
            const href = link.href.split('?')[0]; // Убираем параметры
            if (seen.has(href)) return;
            
            // Поднимаемся к карточке
            let card = link.parentElement;
            for (let i = 0; i < 5; i++) {
                if (card.parentElement) card = card.parentElement;
            }
            
            const text = card.innerText || '';
            
            // Ищем цену - число перед  (берём цену со скидкой, если есть "с купоном")
            let price = '';
            const priceMatches = text.match(/([\d\s]+)\s*/g);
            if (priceMatches && priceMatches.length > 0) {
                // Берём первую цену
                const match = priceMatches[0].match(/([\d\s]+)/);
                if (match) price = match[1].replace(/\s/g, '');
            }
            
            // Ищем название - строка с описанием товара
            const lines = text.split('\n').filter(l => l.trim().length > 30);
            let title = '';
            for (const line of lines) {
                const l = line.trim();
                if ((l.includes('iPhone') || l.includes('Смартфон') || l.includes('телефон')) 
                    && !l.includes('') && !l.includes('СКИДКА') && l.length > 30 && l.length < 200) {
                    title = l;
                    break;
                }
            }
            
            if (title && price) {
                seen.add(href);
                results.push({
                    title: title.slice(0, 100),
                    price: price + ' ',
                    price_num: parseInt(price) || 0,
                    url: href,
                    marketplace: 'aliexpress'
                });
            }
        });
        
        return results.slice(0, 15);
    }""")
    
    print(f'Found: {len(ali)} products')
    for p in ali[:5]:
        print(f"  {p['price']:>12}  {p['title'][:45]}")
    
    browser.close()
