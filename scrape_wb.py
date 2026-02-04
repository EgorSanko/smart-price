from playwright.sync_api import sync_playwright
import json
import time
import urllib.parse

def scrape_wb(query, max_products=20):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        page = browser.new_page()
        
        search_url = f'https://www.wildberries.ru/catalog/0/search.aspx?search={urllib.parse.quote(query)}'
        print(f'Opening: {search_url}')
        page.goto(search_url)
        
        print('Waiting for results...')
        try:
            page.wait_for_selector('[data-nm-id]', timeout=15000)
        except:
            print('Timeout')
        
        time.sleep(3)
        page.evaluate('window.scrollBy(0, 500)')
        time.sleep(2)
        
        products = page.evaluate("""() => {
            const results = [];
            const cards = document.querySelectorAll('[data-nm-id]');
            
            cards.forEach(card => {
                const id = card.getAttribute('data-nm-id');
                if (!id) return;
                
                // Берём весь текст и парсим
                const allText = card.innerText;
                const lines = allText.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                
                // Ищем цену и название
                let price = '';
                let brand = '';
                let title = '';
                
                for (const line of lines) {
                    if (line.includes('₽') && !price) {
                        price = line;
                    } else if (line.endsWith('/') || line === 'Apple' || line === 'Samsung' || line === 'Xiaomi') {
                        brand = line.replace('/', '').trim();
                    } else if (line.length > 15 && !title && !line.includes('₽') && !line.includes('%')) {
                        title = line;
                    }
                }
                
                // Альтернативный поиск названия через селекторы
                const nameEl = card.querySelector('.product-card__name');
                if (nameEl && !title) {
                    title = nameEl.innerText.trim();
                }
                
                const img = card.querySelector('img');
                
                results.push({
                    external_id: id,
                    brand: brand,
                    title: title || 'iPhone',
                    price: price,
                    url: 'https://www.wildberries.ru/catalog/' + id + '/detail.aspx',
                    image_url: img ? img.src : ''
                });
            });
            return results;
        }""")
        
        print(f'Found {len(products)} products')
        browser.close()
        return products[:max_products]

if __name__ == '__main__':
    products = scrape_wb('iphone 16', max_products=15)
    print(f'\n=== Results: {len(products)} products ===\n')
    
    for p in products[:10]:
        print(f"ID: {p['external_id']}")
        print(f"  Brand: {p['brand']}")
        print(f"  Title: {p['title'][:60]}")
        print(f"  Price: {p['price']}")
        print(f"  URL: {p['url']}")
        print()
    
    with open('wb_products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print('Saved to wb_products.json')
