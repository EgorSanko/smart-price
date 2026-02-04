# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import time
import re
import json

app = Flask(__name__)
CORS(app)

browser = None
pw = None

# Словарь нормализации
NORMALIZE = {
    'айфон': 'iPhone', 'айпад': 'iPad', 'макбук': 'MacBook', 'эпл': 'Apple',
    'самсунг': 'Samsung', 'галакси': 'Galaxy', 'зфлип': 'Z Flip', 'зфолд': 'Z Fold',
    'сяоми': 'Xiaomi', 'ксяоми': 'Xiaomi', 'редми': 'Redmi', 'поко': 'Poco', 'посо': 'Poco',
    'хуавей': 'Huawei', 'хонор': 'Honor', 'реалми': 'Realme', 'ван плас': 'OnePlus',
    'дрими': 'Dreame', 'дайсон': 'Dyson', 'робот пылесос': 'робот-пылесос',
    'эйрподс': 'AirPods', 'аирподс': 'AirPods', 'наушники': 'наушники',
    'про': 'Pro', 'макс': 'Max', 'ультра': 'Ultra', 'плюс': 'Plus', 'мини': 'Mini',
    'гб': 'GB', 'тб': 'TB',
}

def clean_number(s):
    return re.sub(r'\D', '', s)

def normalize_query(q):
    """Локальная нормализация без AI"""
    result = q.lower()
    for ru, en in NORMALIZE.items():
        result = re.sub(rf'\b{ru}\b', en, result, flags=re.IGNORECASE)
    # Убираем лишние пробелы
    result = ' '.join(result.split())
    print(f"Normalize: '{q}' -> '{result}'")
    return result

def filter_products(query, products):
    """Локальная фильтрация без AI"""
    if not products:
        return {"matching": [], "excluded": [], "best_price": None, "summary": "Ничего не найдено"}
    
    query_lower = query.lower()
    query_words = set(re.findall(r'\w+', query_lower))
    
    # Слова-исключения (аксессуары)
    exclude_words = {'чехол', 'кейс', 'case', 'cover', 'стекло', 'пленка', 'защитн', 
                     'кабель', 'зарядк', 'адаптер', 'салфетк', 'щетк', 'фильтр',
                     'ремешок', 'strap', 'band', 'амбушюр', 'накладк'}
    
    matching = []
    excluded = []
    
    for p in products:
        title_lower = (p.get('title') or '').lower()
        price = p.get('price_num', 0)
        
        # Пропускаем товары без цены
        if price <= 0:
            excluded.append({"title": p.get('title', ''), "reason": "нет цены"})
            continue
        
        # Проверяем на аксессуары
        is_accessory = any(word in title_lower for word in exclude_words)
        if is_accessory:
            excluded.append({"title": p.get('title', ''), "reason": "аксессуар"})
            continue
        
        matching.append(p)
    
    # Сортируем по цене
    matching.sort(key=lambda x: x.get('price_num', 999999))
    
    best = matching[0] if matching else None
    summary = f"Найдено {len(matching)} товаров." if matching else "Ничего не найдено"
    if best:
        summary += f" Лучшая цена: {best.get('price_num', 0):,} руб.".replace(',', ' ')
    
    return {"matching": matching, "excluded": excluded, "best_price": best, "summary": summary}

def get_browser():
    global browser, pw
    if browser is None:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--window-position=-32000,-32000']
        )
    return browser

def scrape_wb(query):
    b = get_browser()
    ctx = b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = ctx.new_page()
    try:
        page.goto(f'https://www.wildberries.ru/catalog/0/search.aspx?search={query}', timeout=20000)
        page.wait_for_selector('[data-nm-id]', timeout=10000)
        time.sleep(2)
        items = page.evaluate('''() => Array.from(document.querySelectorAll('[data-nm-id]')).slice(0,12).map(c => ({
            title: c.querySelector('.product-card__name')?.innerText?.trim() || '',
            price: c.querySelector('.price__lower-price')?.innerText?.trim() || '',
            url: 'https://www.wildberries.ru/catalog/' + c.getAttribute('data-nm-id') + '/detail.aspx',
            marketplace: 'wildberries'
        }))''')
        for p in items:
            n = clean_number(p['price'])
            p['price_num'] = int(n) if n else 0
        return items
    except Exception as e:
        print(f"WB: {e}")
        return []
    finally:
        ctx.close()

def scrape_ym(query):
    b = get_browser()
    ctx = b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = ctx.new_page()
    try:
        page.goto(f'https://market.yandex.ru/search?text={query}', timeout=20000)
        time.sleep(3)
        page.keyboard.press('Escape')
        time.sleep(1)
        items = page.evaluate('''() => {
            const r = [];
            document.querySelectorAll('[data-auto="snippet-title"]').forEach(t => {
                const card = t.closest('article') || t.closest('[data-apiary-widget-name]');
                const price = card?.querySelector('[data-auto="snippet-price-current"]');
                const link = card?.querySelector('a') || t.closest('a');
                if (t.innerText) r.push({ title: t.innerText.trim(), price: price?.innerText?.trim() || '', url: link?.href || '', marketplace: 'yandex' });
            });
            return r.slice(0,12);
        }''')
        for p in items:
            n = clean_number(p['price'])
            p['price_num'] = int(n) if n else 0
        return items
    except Exception as e:
        print(f"YM: {e}")
        return []
    finally:
        ctx.close()

def scrape_oz(query):
    b = get_browser()
    ctx = b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = ctx.new_page()
    try:
        page.goto(f'https://www.ozon.ru/search/?text={query}', timeout=25000)
        time.sleep(5)
        raw = page.evaluate('''() => {
            const d = [], seen = new Set();
            document.querySelectorAll('a[href*="/product/"]').forEach(l => {
                if (!seen.has(l.href)) { seen.add(l.href); d.push({ url: l.href, text: l.closest('div')?.innerText || '' }); }
            });
            return d.slice(0,15);
        }''')
        items = []
        seen = set()
        for x in raw:
            lines = x['text'].split('\n')
            price, title = None, None
            for l in lines:
                l = l.strip()
                if not price and '\u20bd' in l:
                    n = clean_number(l)
                    if n and 500 < int(n) < 500000: price = int(n)
                if not title and len(l) > 15 and '\u20bd' not in l: title = l[:100]
            if title and price and title not in seen:
                seen.add(title)
                items.append({'title': title, 'price_num': price, 'price': f'{price}', 'url': x['url'], 'marketplace': 'ozon'})
        return items[:12]
    except Exception as e:
        print(f"Ozon: {e}")
        return []
    finally:
        ctx.close()

@app.route('/api/search/stream')
def search_stream():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400

    def gen():
        yield f"data: {json.dumps({'step': 'normalize', 'message': 'Обрабатываем запрос...'}, ensure_ascii=False)}\n\n"
        sq = normalize_query(query)
        yield f"data: {json.dumps({'step': 'normalized', 'message': f'Ищем: {sq}'}, ensure_ascii=False)}\n\n"

        all_p = []

        yield f"data: {json.dumps({'step': 'wb', 'message': 'Wildberries...'}, ensure_ascii=False)}\n\n"
        wb = scrape_wb(sq)
        all_p.extend(wb)
        yield f"data: {json.dumps({'step': 'wb_done', 'message': f'WB: {len(wb)} товаров'}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'step': 'ym', 'message': 'Яндекс Маркет...'}, ensure_ascii=False)}\n\n"
        ym = scrape_ym(sq)
        all_p.extend(ym)
        yield f"data: {json.dumps({'step': 'ym_done', 'message': f'Яндекс: {len(ym)} товаров'}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'step': 'oz', 'message': 'Ozon...'}, ensure_ascii=False)}\n\n"
        oz = scrape_oz(sq)
        all_p.extend(oz)
        yield f"data: {json.dumps({'step': 'oz_done', 'message': f'Ozon: {len(oz)} товаров'}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'step': 'filter', 'message': 'Фильтруем результаты...'}, ensure_ascii=False)}\n\n"
        res = filter_products(query, all_p)

        yield f"data: {json.dumps({'step': 'done', 'message': 'Готово!', 'result': {'query': query, 'normalized_query': sq, 'total_found': len(all_p), 'matching_products': res.get('matching', []), 'excluded': res.get('excluded', []), 'best_price': res.get('best_price'), 'summary': res.get('summary', '')}}, ensure_ascii=False)}\n\n"

    return Response(gen(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400
    sq = normalize_query(query)
    all_p = scrape_wb(sq) + scrape_ym(sq) + scrape_oz(sq)
    res = filter_products(query, all_p)
    return jsonify({'query': query, 'normalized_query': sq, 'total_found': len(all_p), 'matching_products': res.get('matching', []), 'excluded': res.get('excluded', []), 'best_price': res.get('best_price'), 'summary': res.get('summary', '')})

@app.route('/api/chat', methods=['POST'])
def chat():
    # Простой чат без AI
    data = request.json or {}
    msg = data.get('message', '').lower()
    
    responses = {
        'привет': 'Привет! Я помогу найти лучшие цены. Просто введи название товара в поиск!',
        'как': 'Введи название товара в строку поиска, и я найду лучшие цены на WB, Яндекс и Ozon!',
        'спасибо': 'Пожалуйста! Рад помочь ',
    }
    
    for key, resp in responses.items():
        if key in msg:
            return jsonify({'response': resp})
    
    return jsonify({'response': 'Я ищу лучшие цены на товары. Введи запрос в строку поиска!'})

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print('Smart Price API v10 (No AI limits)')
    print('http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, threaded=False)