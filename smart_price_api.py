from flask import Flask, jsonify, request
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import time
import re
import threading

app = Flask(__name__)
CORS(app)  # Разрешаем запросы с других доменов

# Глобальный браузер (держим открытым)
browser = None
playwright_instance = None

def clean_number(s):
    return re.sub(r'\D', '', s)

def get_browser():
    global browser, playwright_instance
    if browser is None:
        playwright_instance = sync_playwright().start()
        browser = playwright_instance.chromium.launch(
            headless=False, 
            args=['--disable-blink-features=AutomationControlled']
        )
    return browser

def scrape_wildberries(query):
    b = get_browser()
    context = b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    try:
        page.goto('https://www.wildberries.ru/', timeout=15000)
        time.sleep(2)
        page.goto(f'https://www.wildberries.ru/catalog/0/search.aspx?search={query}', timeout=15000)
        page.wait_for_selector('[data-nm-id]', timeout=10000)
        time.sleep(2)
        products = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('[data-nm-id]')).slice(0, 15).map(card => {
                const id = card.getAttribute('data-nm-id');
                return {
                    external_id: id,
                    title: card.querySelector('.product-card__name')?.innerText?.trim() || '',
                    price: card.querySelector('.price__lower-price')?.innerText?.trim() || '',
                    url: 'https://www.wildberries.ru/catalog/' + id + '/detail.aspx',
                    marketplace: 'wildberries'
                };
            });
        }""")
        for p in products:
            c = clean_number(p['price'])
            p['price_num'] = int(c) if c else 0
        return products
    except Exception as e:
        print(f"WB Error: {e}")
        return []
    finally:
        context.close()

def scrape_yandex(query):
    b = get_browser()
    context = b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    try:
        page.goto(f'https://market.yandex.ru/search?text={query}', timeout=15000)
        time.sleep(4)
        page.keyboard.press('Escape')
        time.sleep(1)
        products = page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('[data-auto="snippet-title"]').forEach(titleEl => {
                const card = titleEl.closest('article') || titleEl.closest('[data-apiary-widget-name]');
                const linkEl = card?.querySelector('a') || titleEl.closest('a');
                const priceEl = card?.querySelector('[data-auto="snippet-price-current"]');
                if (titleEl.innerText?.trim()) {
                    results.push({
                        title: titleEl.innerText.trim(),
                        price: priceEl?.innerText?.trim() || '',
                        url: linkEl?.href || '',
                        marketplace: 'yandex'
                    });
                }
            });
            return results.slice(0, 15);
        }""")
        for p in products:
            c = clean_number(p['price'])
            p['price_num'] = int(c) if c else 0
        return products
    except Exception as e:
        print(f"Yandex Error: {e}")
        return []
    finally:
        context.close()

def scrape_ozon(query):
    b = get_browser()
    context = b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    try:
        page.goto(f'https://www.ozon.ru/search/?text={query}', timeout=20000)
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
            return data.slice(0, 20);
        }""")
        products = []
        seen = set()
        for item in raw:
            lines = item['text'].split('\n')
            price, title = None, None
            for line in lines:
                l = line.strip()
                if not price and l.endswith('₽'):
                    c = clean_number(l)
                    if c and 5000 < int(c) < 500000:
                        price = int(c)
                if not title and 'iPhone' in l and len(l) > 25:
                    title = l[:100]
            if title and price and title not in seen:
                seen.add(title)
                products.append({
                    'title': title,
                    'price': f'{price:,} ₽'.replace(',', ' '),
                    'price_num': price,
                    'url': item['url'],
                    'marketplace': 'ozon'
                })
        return products[:15]
    except Exception as e:
        print(f"Ozon Error: {e}")
        return []
    finally:
        context.close()

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    print(f"\n Searching: {query}")
    
    all_products = []
    
    # WB
    print("   Wildberries...")
    wb = scrape_wildberries(query)
    print(f"    Found: {len(wb)}")
    all_products.extend(wb)
    
    # Yandex
    print("   Yandex Market...")
    ym = scrape_yandex(query)
    print(f"    Found: {len(ym)}")
    all_products.extend(ym)
    
    # Ozon
    print("   Ozon...")
    oz = scrape_ozon(query)
    print(f"    Found: {len(oz)}")
    all_products.extend(oz)
    
    # Сортируем по цене
    all_products.sort(key=lambda x: x.get('price_num') or 999999)
    
    # Лучшая цена
    best = None
    valid = [p for p in all_products if p.get('price_num', 0) > 1000]
    if valid:
        best = min(valid, key=lambda x: x['price_num'])
    
    print(f" Total: {len(all_products)} products")
    
    return jsonify({
        'query': query,
        'total': len(all_products),
        'best_price': best,
        'products': all_products
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'browser': browser is not None})

if __name__ == '__main__':
    print(" Smart Price API starting...")
    print(" http://localhost:5000/api/search?q=iphone+16")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=False)
