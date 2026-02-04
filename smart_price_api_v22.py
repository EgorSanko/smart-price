# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import httpx
import re
import json
import time
from playwright.sync_api import sync_playwright

app = Flask(__name__)
CORS(app)

CACHE = {}
CACHE_TTL = 300

def get_cached(key):
    if key in CACHE:
        data, ts = CACHE[key]
        if time.time() - ts < CACHE_TTL:
            return data
    return None

def set_cache(key, data):
    CACHE[key] = (data, time.time())

NORMALIZE = {
    'айфон': 'iPhone', 'самсунг': 'Samsung', 'галакси': 'Galaxy', 
    'зфлип': 'Z Flip', 'зфолд': 'Z Fold', 'сяоми': 'Xiaomi', 'редми': 'Redmi', 
    'поко': 'Poco', 'посо': 'Poco', 'хонор': 'Honor',
    'эйрподс': 'AirPods', 'про': 'Pro', 'гб': 'GB', 'тб': 'TB',
}

def normalize_query(q):
    result = q.lower()
    for ru, en in NORMALIZE.items():
        result = re.sub(rf'\b{ru}\b', en, result, flags=re.IGNORECASE)
    return ' '.join(result.split())

def filter_products(products):
    exclude = {'чехол', 'кейс', 'стекло', 'пленка', 'кабель', 'зарядк', 'ремешок'}
    matching = [p for p in products if p.get('price_num', 0) > 0 and not any(w in p.get('title', '').lower() for w in exclude)]
    matching.sort(key=lambda x: x.get('price_num', 999999))
    return {"matching": matching, "best_price": matching[0] if matching else None, "summary": f"Найдено {len(matching)} товаров"}

def scrape_yandex(query):
    cached = get_cached(f"ya:{query}")
    if cached:
        return cached
    
    try:
        headers = {
            'Accept': 'text/html',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        with httpx.Client(timeout=15, headers=headers, follow_redirects=True) as client:
            r = client.get(f'https://market.yandex.ru/search?text={query}')
        
        items = []
        matches = re.findall(r'"title":"([^"]{5,80})".{0,500}?"price":\{"value":"?(\d+)"?', r.text)
        seen = set()
        for title, price in matches:
            if title not in seen and 500 < int(price) < 500000:
                seen.add(title)
                items.append({
                    'title': title,
                    'price_num': int(price),
                    'url': f'https://market.yandex.ru/search?text={query}',
                    'marketplace': 'yandex'
                })
            if len(items) >= 15:
                break
        print(f"Yandex: {len(items)}")
        set_cache(f"ya:{query}", items)
        return items
    except Exception as e:
        print(f"Yandex Error: {e}")
        return []

def scrape_wildberries(query):
    """WB через Playwright - медленно но работает"""
    cached = get_cached(f"wb:{query}")
    if cached:
        return cached
    
    items = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=['--window-position=-32000,-32000']
            )
            page = browser.new_page()
            page.goto(f'https://www.wildberries.ru/catalog/0/search.aspx?search={query}', timeout=30000)
            page.wait_for_selector('.product-card', timeout=15000)
            time.sleep(2)
            
            cards = page.query_selector_all('.product-card')[:15]
            
            for card in cards:
                try:
                    title_el = card.query_selector('.product-card__name')
                    price_el = card.query_selector('.price__lower-price') or card.query_selector('.product-card__price')
                    link_el = card.query_selector('a')
                    
                    if title_el and price_el:
                        title = title_el.inner_text().strip()
                        price_text = price_el.inner_text()
                        price_num = int(re.sub(r'[^\d]', '', price_text))
                        url = link_el.get_attribute('href') if link_el else ''
                        if not url.startswith('http'):
                            url = 'https://www.wildberries.ru' + url
                        
                        if 500 < price_num < 500000:
                            items.append({
                                'title': title,
                                'price_num': price_num,
                                'url': url,
                                'marketplace': 'wildberries'
                            })
                except:
                    continue
            
            browser.close()
        
        print(f"WB: {len(items)}")
        set_cache(f"wb:{query}", items)
    except Exception as e:
        print(f"WB Error: {e}")
    
    return items

PARSERS = {
    'yandex': {'name': 'Яндекс Маркет', 'fn': scrape_yandex, 'enabled': True, 'color': '#ffcc00'},
    'wildberries': {'name': 'Wildberries', 'fn': scrape_wildberries, 'enabled': True, 'color': '#cb11ab'},
}

@app.route('/api/parsers')
def get_parsers():
    return jsonify({k: {'name': v['name'], 'enabled': v['enabled'], 'color': v['color']} for k, v in PARSERS.items()})

@app.route('/api/search/stream')
def search_stream():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400

    def gen():
        yield f"data: {json.dumps({'step': 'start', 'message': 'Поиск...'}, ensure_ascii=False)}\n\n"
        sq = normalize_query(query)
        yield f"data: {json.dumps({'step': 'norm', 'message': 'Ищем: ' + sq}, ensure_ascii=False)}\n\n"

        all_p = []

        for key, parser in PARSERS.items():
            if not parser['enabled']:
                continue
            name = parser['name']
            yield f"data: {json.dumps({'step': key, 'message': name + '...'}, ensure_ascii=False)}\n\n"
            items = parser['fn'](sq)
            all_p.extend(items)
            yield f"data: {json.dumps({'step': key + '_done', 'message': name + ': ' + str(len(items))}, ensure_ascii=False)}\n\n"

        res = filter_products(all_p)
        result = {
            'query': query,
            'normalized_query': sq,
            'total_found': len(all_p),
            'matching_products': res['matching'],
            'best_price': res['best_price'],
            'summary': res['summary']
        }
        yield f"data: {json.dumps({'step': 'done', 'message': 'Готово!', 'result': result}, ensure_ascii=False)}\n\n"

    return Response(gen(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print('Smart Price API v22')
    print('Yandex: httpx (fast)')
    print('WB: Playwright (slow but works)')
    app.run(host='0.0.0.0', port=5000, threaded=False)