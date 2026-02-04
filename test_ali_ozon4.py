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
    
    ozon = page.evaluate("""() => {
        const results = [];
        const links = document.querySelectorAll('a[href*="/product/"]');
        const seen = new Set();
        
        links.forEach(link => {
            const href = link.href;
            if (seen.has(href)) return;
            
            let card = link.parentElement;
            for (let i = 0; i < 6; i++) {
                if (card && card.parentElement) card = card.parentElement;
            }
            
            const text = card ? card.innerText : '';
            
            // Ищем все числа перед 
            const priceMatches = text.match(/([0-9][0-9 ]{2,})\s*/g);
            let price = '';
            if (priceMatches) {
                for (const pm of priceMatches) {
                    const num = parseInt(pm.replace(/[^0-9]/g, ''));
                    // Цена айфона > 30000, пропускаем "1000 баллов"
                    if (num > 30000 && num < 500000) {
                        price = num.toString();
                        break;
                    }
                }
            }
            
            // Название
            let title = '';
            const lines = text.split('\\n');
            for (const line of lines) {
                const l = line.trim();
                if (l.length > 30 && l.length < 150 && (l.includes('iPhone') || l.includes('Смартфон Apple'))) {
                    title = l;
                    break;
                }
            }
            
            if (title && price) {
                seen.add(href);
                results.push({ 
                    title: title.slice(0, 100), 
                    price: price + ' ',
                    price_num: parseInt(price),
                    url: href, 
                    marketplace: 'ozon' 
                });
            }
        });
        
        return results.slice(0, 15);
    }""")
    
    print(f'Found: {len(ozon)} products')
    for prod in sorted(ozon, key=lambda x: x.get('price_num', 0))[:5]:
        print(f"  {prod['price']:>12}  {prod['title'][:45]}")
    
    page.close()
    time.sleep(2)
    
    # === ALIEXPRESS ===
    print('\n=== ALIEXPRESS ===')
    page = browser.new_page()
    page.goto('https://aliexpress.ru/wholesale?SearchText=iphone%2016')
    time.sleep(5)
    
    ali = page.evaluate("""() => {
        const results = [];
        const links = document.querySelectorAll('a[href*="/item/"]');
        const seen = new Set();
        
        links.forEach(link => {
            const href = link.href.split('?')[0];
            if (seen.has(href)) return;
            
            let card = link.parentElement;
            for (let i = 0; i < 6; i++) {
                if (card && card.parentElement) card = card.parentElement;
            }
            
            const text = card ? card.innerText : '';
            
            // Цена
            const priceMatches = text.match(/([0-9][0-9 ]{2,})\s*/g);
            let price = '';
            if (priceMatches) {
                for (const pm of priceMatches) {
                    const num = parseInt(pm.replace(/[^0-9]/g, ''));
                    if (num > 10000 && num < 500000) {
                        price = num.toString();
                        break;
                    }
                }
            }
            
            // Название - ищем строку с iPhone
            let title = '';
            const lines = text.split('\\n');
            for (const line of lines) {
                const l = line.trim();
                if (l.length > 20 && (l.toLowerCase().includes('iphone') || l.includes('смартфон'))) {
                    if (!l.includes('') && !l.includes('СКИДКА') && !l.includes('купон')) {
                        title = l;
                        break;
                    }
                }
            }
            
            if (title && price) {
                seen.add(href);
                results.push({ 
                    title: title.slice(0, 100), 
                    price: price + ' ',
                    price_num: parseInt(price),
                    url: href, 
                    marketplace: 'aliexpress' 
                });
            }
        });
        
        return results.slice(0, 15);
    }""")
    
    print(f'Found: {len(ali)} products')
    for prod in sorted(ali, key=lambda x: x.get('price_num', 0))[:5]:
        print(f"  {prod['price']:>12}  {prod['title'][:45]}")
    
    browser.close()
