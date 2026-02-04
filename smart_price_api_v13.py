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

def scrape_wb(query):
    """WB API с правильными заголовками"""
    try:
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'ru-RU,ru;q=0.9',
            'Origin': 'https://www.wildberries.ru',
            'Referer': 'https://www.wildberries.ru/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
        }
        params = {
            'ab_testing': 'false',
            'appType': '1',
            'curr': 'rub',
            'dest': '-1257786',
            'query': query,
            'resultset': 'catalog',
            'sort': 'popular',
            'spp': '30',
            'suppressSpellcheck': 'false',
        }
        
        with httpx.Client(timeout=10, headers=headers) as client:
            r = client.get('https://search.wb.ru/exactmatch/ru/common/v4/search', params=params)
            data = r.json()
        
        items = []
        for p in data.get('data', {}).get('products', [])[:15]:
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

def scrape_ym(query):
    """Яндекс Маркет API"""
    try:
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        with httpx.Client(timeout=10, headers=headers, follow_redirects=True) as client:
            r = client.get(f'https://market.yandex.ru/search?text={query}')
        
        items = []
        # Ищем JSON данные в HTML
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
        print(f"YM: {len(items)}")
        return items
    except Exception as e:
        print(f"YM Error: {e}")
        return []

def scrape_oz(query):
    """Ozon - пробуем мобильный API"""
    try:
        headers = {
            'Accept': 'application/json',
            'User-Agent': 'ozonapp_android/17.5.1',
            'x-o3-app-name': 'ozonapp_android',
            'x-o3-app-version': '17.5.1',
        }
        
        # Мобильный API Ozon
        with httpx.Client(timeout=10, headers=headers) as client:
            r = client.get(f'https://api.ozon.ru/composer-api.bx/page/json/v2?url=/search/?text={query}')
            
            if r.status_code != 200:
                print(f"Ozon API: {r.status_code}")
                return []
            
            data = r.json()
            items = []
            
            # Парсим структуру ответа
            widgets = data.get('widgetStates', {})
            for key, val in widgets.items():
                if 'searchResultsV2' in key:
                    try:
                        parsed = json.loads(val)
                        for item in parsed.get('items', [])[:15]:
                            price = item.get('mainState', [{}])[0].get('price', {}).get('price', '')
                            title = item.get('title', '')
                            if price and title:
                                price_num = int(re.sub(r'\D', '', str(price)))
                                if 500 < price_num < 500000:
                                    items.append({
                                        'title': title,
                                        'price_num': price_num,
                                        'url': f"https://ozon.ru{item.get('link', '')}",
                                        'marketplace': 'ozon'
                                    })
                    except:
                        pass
            
            print(f"Ozon: {len(items)}")
            return items
    except Exception as e:
        print(f"Ozon Error: {e}")
        return []

@app.route('/api/search/stream')
def search_stream():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400

    def gen():
        yield f"data: {json.dumps({'step': 'start', 'message': 'Поиск...'}, ensure_ascii=False)}\n\n"
        sq = normalize_query(query)
        yield f"data: {json.dumps({'step': 'norm', 'message': f'Ищем: {sq}'}, ensure_ascii=False)}\n\n"

        all_p = []

        yield f"data: {json.dumps({'step': 'wb', 'message': 'Wildberries...'}, ensure_ascii=False)}\n\n"
        wb = scrape_wb(sq)
        all_p.extend(wb)
        yield f"data: {json.dumps({'step': 'wb_done', 'message': f'WB: {len(wb)}'}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'step': 'ym', 'message': 'Яндекс...'}, ensure_ascii=False)}\n\n"
        ym = scrape_ym(sq)
        all_p.extend(ym)
        yield f"data: {json.dumps({'step': 'ym_done', 'message': f'Яндекс: {len(ym)}'}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'step': 'oz', 'message': 'Ozon...'}, ensure_ascii=False)}\n\n"
        oz = scrape_oz(sq)
        all_p.extend(oz)
        yield f"data: {json.dumps({'step': 'oz_done', 'message': f'Ozon: {len(oz)}'}, ensure_ascii=False)}\n\n"

        res = filter_products(all_p)
        yield f"data: {json.dumps({'step': 'done', 'message': 'Готово!', 'result': {'query': query, 'normalized_query': sq, 'total_found': len(all_p), 'matching_products': res['matching'], 'best_price': res['best_price'], 'summary': res['summary']}}, ensure_ascii=False)}\n\n"

    return Response(gen(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400
    sq = normalize_query(query)
    all_p = scrape_wb(sq) + scrape_ym(sq) + scrape_oz(sq)
    res = filter_products(all_p)
    return jsonify({'query': query, 'normalized_query': sq, 'total_found': len(all_p), 'matching_products': res['matching'], 'best_price': res['best_price'], 'summary': res['summary']})

@app.route('/api/chat', methods=['POST'])
def chat():
    return jsonify({'response': 'Введи товар в поиск! '})

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print('Smart Price API v13 (Fast API-only)')
    print('http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, threaded=True)