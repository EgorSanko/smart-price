# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import httpx
import re
import json
import time
from functools import lru_cache

app = Flask(__name__)
CORS(app)

# Простой кэш на 5 минут
CACHE = {}
CACHE_TTL = 300

def get_cached(key):
    if key in CACHE:
        data, ts = CACHE[key]
        if time.time() - ts < CACHE_TTL:
            print(f"Cache hit: {key}")
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
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'ru-RU,ru;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        with httpx.Client(timeout=15, headers=headers, follow_redirects=True) as client:
            r = client.get(f'https://market.yandex.ru/search?text={query}')
        
        print(f"Yandex status: {r.status_code}")
        
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
            if len(items) >= 20:
                break
        print(f"Yandex: {len(items)}")
        set_cache(f"ya:{query}", items)
        return items
    except Exception as e:
        print(f"Yandex Error: {e}")
        return []

def scrape_wildberries(query):
    cached = get_cached(f"wb:{query}")
    if cached:
        return cached
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
        }
        
        params = {
            "appType": "1",
            "curr": "rub",
            "dest": "-1255987",
            "query": query,
            "resultset": "catalog",
            "sort": "popular",
            "spp": "30",
        }
        
        # Один запрос!
        with httpx.Client(timeout=15, headers=headers) as client:
            r = client.get("https://search.wb.ru/exactmatch/ru/common/v9/search", params=params)
        
        print(f"WB status: {r.status_code}")
        
        if r.status_code == 429:
            return []
        
        if r.status_code != 200:
            return []
        
        data = r.json()
        items = []
        
        for p in data.get('data', {}).get('products', [])[:20]:
            price = None
            if 'sizes' in p and len(p['sizes']) > 0:
                price_info = p['sizes'][0].get('price', {})
                price = price_info.get('product')
                if price:
                    price = int(price / 100)
            
            if not price:
                price = p.get('salePriceU', 0) // 100
            
            if price and price > 0:
                items.append({
                    'title': p.get('name', ''),
                    'price_num': price,
                    'url': f"https://www.wildberries.ru/catalog/{p.get('id')}/detail.aspx",
                    'marketplace': 'wildberries'
                })
        
        print(f"WB: {len(items)}")
        set_cache(f"wb:{query}", items)
        return items
    except Exception as e:
        print(f"WB Error: {e}")
        return []

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
    sources = request.args.get('sources', '').split(',') if request.args.get('sources') else None
    
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
            if sources and key not in sources:
                continue
            
            name = parser['name']
            yield f"data: {json.dumps({'step': key, 'message': name + '...'}, ensure_ascii=False)}\n\n"
            items = parser['fn'](sq)
            all_p.extend(items)
            cnt = str(len(items))
            if not items and key == 'wildberries':
                cnt = "0 (подождите 5 мин)"
            yield f"data: {json.dumps({'step': key + '_done', 'message': name + ': ' + cnt}, ensure_ascii=False)}\n\n"

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

@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    sq = normalize_query(query)
    all_p = []
    
    for key, parser in PARSERS.items():
        if parser['enabled']:
            all_p.extend(parser['fn'](sq))
    
    res = filter_products(all_p)
    return jsonify({
        'query': query,
        'normalized_query': sq,
        'total_found': len(all_p),
        'matching_products': res['matching'],
        'best_price': res['best_price'],
        'summary': res['summary']
    })

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'cache_size': len(CACHE)})

if __name__ == '__main__':
    print('Smart Price API v20')
    print('http://localhost:5000')
    print('Cache: 5 min, 1 request per search')
    app.run(host='0.0.0.0', port=5000, threaded=True)