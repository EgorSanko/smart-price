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
            for (let i = 0; i < 5; i++) {
                if (card && card.parentElement) card = card.parentElement;
            }
            
            const text = card ? card.innerText : '';
            const lines = text.split('\\n');
            
            let price = '';
            let title = '';
            
            for (const line of lines) {
                const l = line.trim();
                if (!price && l.includes('$RUB$')) {
                    price = l.replace(/[^0-9]/g, '');
                }
                if (!title && l.length > 30 && l.length < 150 && (l.includes('iPhone') || l.includes('Apple'))) {
                    title = l;
                }
            }
            
            // Price fallback
            if (!price) {
                const m = text.match(/([0-9][0-9 ]+)[^0-9]*\\u20BD/);
                if (m) price = m[1].replace(/ /g, '');
            }
            
            if (title) {
                seen.add(href);
                results.push({ title: title.slice(0, 100), price: price, url: href, marketplace: 'ozon' });
            }
        });
        
        return results.slice(0, 15);
    }""".replace('$RUB$', ''))
    
    print(f'Found: {len(ozon)} products')
    for prod in ozon[:5]:
        price = prod['price'] + ' P' if prod['price'] else 'N/A'
        print(f"  {price:>12}  {prod['title'][:45]}")
    
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
            for (let i = 0; i < 5; i++) {
                if (card && card.parentElement) card = card.parentElement;
            }
            
            const text = card ? card.innerText : '';
            const lines = text.split('\\n');
            
            let price = '';
            let title = '';
            
            for (const line of lines) {
                const l = line.trim();
                if (!price && l.includes('$RUB$')) {
                    const m = l.match(/([0-9][0-9 ]+)/);
                    if (m) price = m[1].replace(/ /g, '');
                }
                if (!title && l.length > 40 && l.length < 200 && !l.includes('$RUB$') && !l.includes('СКИДКА')) {
                    title = l;
                }
            }
            
            if (title) {
                seen.add(href);
                results.push({ title: title.slice(0, 100), price: price, url: href, marketplace: 'aliexpress' });
            }
        });
        
        return results.slice(0, 15);
    }""".replace('$RUB$', ''))
    
    print(f'Found: {len(ali)} products')
    for prod in ali[:5]:
        price = prod['price'] + ' P' if prod['price'] else 'N/A'
        print(f"  {price:>12}  {prod['title'][:45]}")
    
    browser.close()
