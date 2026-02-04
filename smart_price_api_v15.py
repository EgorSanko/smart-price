# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import httpx
import re
import json

app = Flask(__name__)
CORS(app)

NORMALIZE = {
    'айфон': 'iPhone', 'самсунг': 'Samsung', 'галакси': 'Galaxy', 
    'зфлип': 'Z Flip', 'сяоми': 'Xiaomi', 'редми': 'Redmi', 
    'поко': 'Poco', 'посо': 'Poco', 'хонор': 'Honor',
    'дрими': 'Dreame', 'эйрподс': 'AirPods', 'про': 'Pro', 'гб': 'GB',
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

def scrape_wildberries(query):
    try:
        headers = {
            'Accept': '*/*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        url = "https://search.wb.ru/exactmatch/ru/common/v9/search"
        params = {
            'appType': '1',
            'curr': 'rub',
            'dest': '-1257786',
            'query': query,
            'resultset': 'catalog',
            'sort': 'popular',
            'spp': '30',
        }
        
        with httpx.Client(timeout=15, headers=headers) as client:
            r = client.get(url, params=params)
            if r.status_code != 200:
                print(f"WB status: {r.status_code}")
                return []
            data = r.json()
        
        items = []
        for p in data.get('data', {}).get('products', [])[:20]:
            price = p.get('salePriceU', 0) // 100
            if price > 0:
                items.append({
                    'title': p.get('name', ''),
                    'price_num': price,
                    'url': f"https://www.wildberries.ru/catalog/{p.get('id')}/detail.aspx",
                    'marketplace': 'wildberries'
                })
        print(f"WB: {len(items)}")
        return items
    except Exception as e:
        print(f"WB Error: {e}")
        return []

def scrape_yandex(query):
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
            if len(items) >= 20:
                break
        print(f"Yandex: {len(items)}")
        return items
    except Exception as e:
        print(f"Yandex Error: {e}")
        return []

def scrape_ozon(query):
    print("Ozon: disabled")
    return []

PARSERS = {
    'wildberries': {'name': 'Wildberries', 'fn': scrape_wildberries, 'enabled': True, 'color': '#cb11ab'},
    'yandex': {'name': 'Яндекс Маркет', 'fn': scrape_yandex, 'enabled': True, 'color': '#ffcc00'},
    'ozon': {'name': 'Ozon', 'fn': scrape_ozon, 'enabled': False, 'color': '#005bff'},
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
        yield 'data: ' + json.dumps({'step': 'start', 'message': 'Поиск...'}, ensure_ascii=False) + '\n\n'
        sq = normalize_query(query)
        yield 'data: ' + json.dumps({'step': 'norm', 'message': 'Ищем: ' + sq}, ensure_ascii=False) + '\n\n'

        all_p = []

        for key, parser in PARSERS.items():
            if not parser['enabled']:
                continue
            if sources and key not in sources:
                continue
            
            name = parser['name']
            yield 'data: ' + json.dumps({'step': key, 'message': name + '...'}, ensure_ascii=False) + '\n\n'
            items = parser['fn'](sq)
            all_p.extend(items)
            yield 'data: ' + json.dumps({'step': key + '_done', 'message': name + ': ' + str(len(items))}, ensure_ascii=False) + '\n\n'

        res = filter_products(all_p)
        result = {
            'query': query,
            'normalized_query': sq,
            'total_found': len(all_p),
            'matching_products': res['matching'],
            'best_price': res['best_price'],
            'summary': res['summary']
        }
        yield 'data: ' + json.dumps({'step': 'done', 'message': 'Готово!', 'result': result}, ensure_ascii=False) + '\n\n'

    return Response(gen(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    sources = request.args.get('sources', '').split(',') if request.args.get('sources') else None
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    sq = normalize_query(query)
    all_p = []
    
    for key, parser in PARSERS.items():
        if not parser['enabled']:
            continue
        if sources and key not in sources:
            continue
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

@app.route('/api/chat', methods=['POST'])
def chat():
    return jsonify({'response': 'Введи товар в поиск!'})

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print('Smart Price API v15')
    print('WB + Yandex enabled')
    print('http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, threaded=True)