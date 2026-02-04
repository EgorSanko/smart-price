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
    """WB через Playwright"""
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
            
            # Ждем загрузки - пробуем разные селекторы
            try:
                page.wait_for_selector('article[data-nm-id]', timeout=10000)
            except:
                try:
                    page.wait_for_selector('.product-card-list', timeout=5000)
                except:
                    page.wait_for_timeout(5000)
            
            # Парсим через JSON в странице
            content = page.content()
            
            # Ищем данные товаров
            matches = re.findall(r'"id":(\d+).*?"name":"([^"]+)".*?"priceU":(\d+)', content)
            if not matches:
                matches = re.findall(r'data-nm-id="(\d+)".*?<span[^>]*>([^<]+)</span>.*?(\d[\d\s]*)\s*₽', content, re.DOTALL)
            
            seen = set()
            for m in matches[:15]:
                try:
                    prod_id = m[0]
                    title = m[1].strip()
                    price_raw = m[2]
                    price_num = int(re.sub(r'[^\d]', '', str(price_raw)))
                    if price_num > 100000:
                        price_num = price_num // 100
                    
                    if prod_id not in seen and 500 < price_num < 500000:
                        seen.add(prod_id)
                        items.append({
                            'title': title,
                            'price_num': price_num,
                            'url': f'https://www.wildberries.ru/catalog/{prod_id}/detail.aspx',
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

def scrape_ozon(query):
    """Ozon через Playwright"""
    cached = get_cached(f"oz:{query}")
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
            page.goto(f'https://www.ozon.ru/search/?text={query}&from_global=true', timeout=30000)
            
            # Ждем загрузки товаров
            try:
                page.wait_for_selector('[data-widget="searchResultsV2"]', timeout=10000)
            except:
                page.wait_for_timeout(5000)
            
            page.wait_for_timeout(2000)
            content = page.content()
            
            # Парсим JSON данные из страницы
            # Ozon встраивает данные в HTML
            matches = re.findall(r'"title":"([^"]{5,100})".*?"price":"([^"]+)".*?"link":"(/product/[^"]+)"', content)
            
            if not matches:
                # Альтернативный паттерн
                matches = re.findall(r'href="(/product/[^"]+)"[^>]*>.*?<span[^>]*>([^<]{5,80})</span>.*?(\d[\d\s]*)\s*₽', content, re.DOTALL)
            
            seen = set()
            for m in matches[:15]:
                try:
                    if len(m) == 3:
                        if m[0].startswith('/'):
                            url, title, price_raw = m
                        else:
                            title, price_raw, url = m
                        
                        title = title.strip()
                        price_num = int(re.sub(r'[^\d]', '', price_raw))
                        
                        if title not in seen and 500 < price_num < 500000:
                            seen.add(title)
                            full_url = f'https://www.ozon.ru{url}' if url.startswith('/') else url
                            items.append({
                                'title': title,
                                'price_num': price_num,
                                'url': full_url,
                                'marketplace': 'ozon'
                            })
                except:
                    continue
            
            browser.close()
        
        print(f"Ozon: {len(items)}")
        set_cache(f"oz:{query}", items)
    except Exception as e:
        print(f"Ozon Error: {e}")
    
    return items

PARSERS = {
    'yandex': {'name': 'Яндекс Маркет', 'fn': scrape_yandex, 'enabled': True, 'color': '#ffcc00'},
    'wildberries': {'name': 'Wildberries', 'fn': scrape_wildberries, 'enabled': True, 'color': '#cb11ab'},
    'ozon': {'name': 'Ozon', 'fn': scrape_ozon, 'enabled': True, 'color': '#005bff'},
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
    print('Smart Price API v23')
    print('Yandex: httpx | WB + Ozon: Playwright')
    app.run(host='0.0.0.0', port=5000, threaded=False)