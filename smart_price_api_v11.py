# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import httpx
import time
import re
import json

app = Flask(__name__)
CORS(app)

# WB API endpoints (как в wildsearch-crawler)
WB_SEARCH_URL = "https://search.wb.ru/exactmatch/ru/common/v4/search"
YM_API_URL = "https://market.yandex.ru/api/search"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'ru-RU,ru;q=0.9',
}

# Нормализация
NORMALIZE = {
    'айфон': 'iPhone', 'айпад': 'iPad', 'макбук': 'MacBook',
    'самсунг': 'Samsung', 'галакси': 'Galaxy', 'зфлип': 'Z Flip', 'зфолд': 'Z Fold',
    'сяоми': 'Xiaomi', 'ксяоми': 'Xiaomi', 'редми': 'Redmi', 'поко': 'Poco', 'посо': 'Poco',
    'хуавей': 'Huawei', 'хонор': 'Honor', 'реалми': 'Realme',
    'дрими': 'Dreame', 'дайсон': 'Dyson',
    'эйрподс': 'AirPods', 'аирподс': 'AirPods',
    'про': 'Pro', 'макс': 'Max', 'ультра': 'Ultra',
    'гб': 'GB', 'тб': 'TB',
}

def clean_number(s):
    return re.sub(r'\D', '', str(s))

def normalize_query(q):
    result = q.lower()
    for ru, en in NORMALIZE.items():
        result = re.sub(rf'\b{ru}\b', en, result, flags=re.IGNORECASE)
    return ' '.join(result.split())

def filter_products(query, products):
    if not products:
        return {"matching": [], "excluded": [], "best_price": None, "summary": "Ничего не найдено"}
    
    exclude_words = {'чехол', 'кейс', 'case', 'cover', 'стекло', 'пленка', 
                     'кабель', 'зарядк', 'адаптер', 'салфетк', 'щетк', 'фильтр', 'ремешок'}
    
    matching = []
    excluded = []
    
    for p in products:
        title_lower = (p.get('title') or '').lower()
        price = p.get('price_num', 0)
        
        if price <= 0:
            continue
        
        is_accessory = any(word in title_lower for word in exclude_words)
        if is_accessory:
            excluded.append({"title": p.get('title', ''), "reason": "аксессуар"})
            continue
        
        matching.append(p)
    
    matching.sort(key=lambda x: x.get('price_num', 999999))
    best = matching[0] if matching else None
    summary = f"Найдено {len(matching)} товаров."
    if best:
        summary += f" Лучшая цена: {best.get('price_num', 0):,} ₽".replace(',', ' ')
    
    return {"matching": matching, "excluded": excluded, "best_price": best, "summary": summary}

def scrape_wb_api(query):
    """WB через API (как wildsearch-crawler)"""
    try:
        params = {
            'query': query,
            'resultset': 'catalog',
            'limit': 100,
            'sort': 'popular',
            'page': 1,
            'appType': 1,
            'curr': 'rub',
            'dest': -1257786,
            'spp': 30,
        }
        
        with httpx.Client(timeout=15, headers=HEADERS) as client:
            r = client.get(WB_SEARCH_URL, params=params)
            
            if r.status_code == 429:
                print("WB API: Rate limited")
                return []
            
            data = r.json()
            products = data.get('data', {}).get('products', [])
            
            items = []
            for p in products[:15]:
                price = p.get('salePriceU', 0) // 100  # Цена в копейках
                items.append({
                    'title': p.get('name', ''),
                    'price_num': price,
                    'price': f"{price:,} ₽".replace(',', ' '),
                    'url': f"https://www.wildberries.ru/catalog/{p.get('id')}/detail.aspx",
                    'marketplace': 'wildberries',
                    'rating': p.get('rating', 0),
                    'feedbacks': p.get('feedbacks', 0),
                })
            
            print(f"WB API: {len(items)} products")
            return items
    except Exception as e:
        print(f"WB API Error: {e}")
        return []

def scrape_ozon_web(query):
    """Ozon через веб (API закрыт)"""
    try:
        url = f"https://www.ozon.ru/search/?text={query}&from_global=true"
        
        with httpx.Client(timeout=15, headers=HEADERS, follow_redirects=True) as client:
            r = client.get(url)
            
            # Парсим JSON из HTML (Ozon вставляет данные в script)
            match = re.search(r'"products"\s*:\s*(\[.+?\])\s*,\s*"searchResultsCount"', r.text)
            if not match:
                # Альтернативный паттерн
                match = re.search(r'window\.__NUXT__\s*=\s*(.+?);</script>', r.text)
            
            if not match:
                print("Ozon: No data found")
                return []
            
            # Простой парсинг цен из HTML
            items = []
            # Ищем цены и названия в тексте
            prices = re.findall(r'(\d[\d\s]*)\s*₽', r.text)
            titles = re.findall(r'"name"\s*:\s*"([^"]+)"', r.text)
            
            for i, (title, price) in enumerate(zip(titles[:15], prices[:15])):
                price_num = int(re.sub(r'\D', '', price))
                if 500 < price_num < 500000:
                    items.append({
                        'title': title,
                        'price_num': price_num,
                        'price': f"{price_num:,} ₽".replace(',', ' '),
                        'url': f"https://www.ozon.ru/search/?text={query}",
                        'marketplace': 'ozon'
                    })
            
            print(f"Ozon: {len(items)} products")
            return items
    except Exception as e:
        print(f"Ozon Error: {e}")
        return []

def scrape_ym_web(query):
    """Яндекс.Маркет через веб"""
    try:
        url = f"https://market.yandex.ru/search?text={query}"
        
        with httpx.Client(timeout=15, headers=HEADERS, follow_redirects=True) as client:
            r = client.get(url)
            
            # Ищем данные товаров
            items = []
            
            # Паттерн для цен
            prices = re.findall(r'"price"\s*:\s*{\s*"value"\s*:\s*"?(\d+)"?', r.text)
            titles = re.findall(r'"title"\s*:\s*"([^"]{10,100})"', r.text)
            
            seen = set()
            for title, price in zip(titles, prices):
                if title in seen:
                    continue
                seen.add(title)
                
                price_num = int(price)
                if 500 < price_num < 500000:
                    items.append({
                        'title': title,
                        'price_num': price_num,
                        'price': f"{price_num:,} ₽".replace(',', ' '),
                        'url': f"https://market.yandex.ru/search?text={query}",
                        'marketplace': 'yandex'
                    })
                
                if len(items) >= 15:
                    break
            
            print(f"Yandex: {len(items)} products")
            return items
    except Exception as e:
        print(f"Yandex Error: {e}")
        return []

@app.route('/api/search/stream')
def search_stream():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400

    def gen():
        yield f"data: {json.dumps({'step': 'start', 'message': 'Обрабатываем запрос...'}, ensure_ascii=False)}\n\n"
        sq = normalize_query(query)
        yield f"data: {json.dumps({'step': 'normalized', 'message': f'Ищем: {sq}'}, ensure_ascii=False)}\n\n"

        all_p = []

        yield f"data: {json.dumps({'step': 'wb', 'message': 'Wildberries API...'}, ensure_ascii=False)}\n\n"
        wb = scrape_wb_api(sq)
        all_p.extend(wb)
        yield f"data: {json.dumps({'step': 'wb_done', 'message': f'WB: {len(wb)} товаров'}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'step': 'ym', 'message': 'Яндекс Маркет...'}, ensure_ascii=False)}\n\n"
        ym = scrape_ym_web(sq)
        all_p.extend(ym)
        yield f"data: {json.dumps({'step': 'ym_done', 'message': f'Яндекс: {len(ym)} товаров'}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'step': 'oz', 'message': 'Ozon...'}, ensure_ascii=False)}\n\n"
        oz = scrape_ozon_web(sq)
        all_p.extend(oz)
        yield f"data: {json.dumps({'step': 'oz_done', 'message': f'Ozon: {len(oz)} товаров'}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'step': 'filter', 'message': 'Фильтруем...'}, ensure_ascii=False)}\n\n"
        res = filter_products(query, all_p)

        yield f"data: {json.dumps({'step': 'done', 'message': 'Готово!', 'result': {'query': query, 'normalized_query': sq, 'total_found': len(all_p), 'matching_products': res['matching'], 'excluded': res['excluded'], 'best_price': res['best_price'], 'summary': res['summary']}}, ensure_ascii=False)}\n\n"

    return Response(gen(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    sq = normalize_query(query)
    all_p = scrape_wb_api(sq) + scrape_ym_web(sq) + scrape_ozon_web(sq)
    res = filter_products(query, all_p)
    
    return jsonify({
        'query': query,
        'normalized_query': sq,
        'total_found': len(all_p),
        'matching_products': res['matching'],
        'excluded': res['excluded'],
        'best_price': res['best_price'],
        'summary': res['summary']
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    return jsonify({'response': 'Введи товар в поиск  найду лучшие цены! '})

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'mode': 'API-based'})

if __name__ == '__main__':
    print('='*50)
    print('Smart Price API v11 (API-based, no browser)')
    print('Based on wildsearch-crawler approach')
    print('='*50)
    print('http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, threaded=True)