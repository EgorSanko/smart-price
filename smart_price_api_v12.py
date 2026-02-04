# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import httpx
import time
import re
import json

app = Flask(__name__)
CORS(app)

# WB API
WB_SEARCH_URL = "https://search.wb.ru/exactmatch/ru/common/v4/search"

browser = None
pw = None

NORMALIZE = {
    'айфон': 'iPhone', 'самсунг': 'Samsung', 'галакси': 'Galaxy', 
    'зфлип': 'Z Flip', 'зфолд': 'Z Fold', 'сяоми': 'Xiaomi', 
    'редми': 'Redmi', 'поко': 'Poco', 'посо': 'Poco',
    'хуавей': 'Huawei', 'хонор': 'Honor', 'дрими': 'Dreame',
    'эйрподс': 'AirPods', 'про': 'Pro', 'ультра': 'Ultra', 'гб': 'GB',
}

def normalize_query(q):
    result = q.lower()
    for ru, en in NORMALIZE.items():
        result = re.sub(rf'\b{ru}\b', en, result, flags=re.IGNORECASE)
    return ' '.join(result.split())

def filter_products(products):
    exclude = {'чехол', 'кейс', 'стекло', 'пленка', 'кабель', 'зарядк', 'ремешок', 'адаптер'}
    matching = [p for p in products if p.get('price_num', 0) > 0 and not any(w in p.get('title', '').lower() for w in exclude)]
    matching.sort(key=lambda x: x.get('price_num', 999999))
    return {"matching": matching, "excluded": [], "best_price": matching[0] if matching else None, "summary": f"Найдено {len(matching)} товаров"}

def get_browser():
    global browser, pw
    if browser is None:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled', '--window-position=-32000,-32000'])
    return browser

def scrape_wb_api(query):
    """WB через API - быстро!"""
    try:
        params = {'query': query, 'resultset': 'catalog', 'limit': 100, 'sort': 'popular', 'page': 1, 'appType': 1, 'curr': 'rub', 'dest': -1257786, 'spp': 30}
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Accept': '*/*', 'Origin': 'https://www.wildberries.ru', 'Referer': 'https://www.wildberries.ru/'}
        
        r = httpx.get(WB_SEARCH_URL, params=params, headers=headers, timeout=10)
        data = r.json()
        
        items = []
        for p in data.get('data', {}).get('products', [])[:15]:
            price = p.get('salePriceU', 0) // 100
            if price > 0:
                items.append({'title': p.get('name', ''), 'price_num': price, 'price': f"{price} ₽", 'url': f"https://www.wildberries.ru/catalog/{p.get('id')}/detail.aspx", 'marketplace': 'wildberries'})
        print(f"WB API: {len(items)}")
        return items
    except Exception as e:
        print(f"WB API fail: {e}, trying browser...")
        return scrape_wb_browser(query)

def scrape_wb_browser(query):
    """WB через браузер - fallback"""
    try:
        b = get_browser()
        ctx = b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        page = ctx.new_page()
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
            n = re.sub(r'\D', '', p['price'])
            p['price_num'] = int(n) if n else 0
        ctx.close()
        print(f"WB Browser: {len(items)}")
        return items
    except Exception as e:
        print(f"WB Browser: {e}")
        return []

def scrape_ym(query):
    """Яндекс через браузер"""
    try:
        b = get_browser()
        ctx = b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        page = ctx.new_page()
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
            n = re.sub(r'\D', '', p['price'])
            p['price_num'] = int(n) if n else 0
        ctx.close()
        print(f"YM: {len(items)}")
        return items
    except Exception as e:
        print(f"YM: {e}")
        return []

def scrape_oz(query):
    """Ozon через браузер"""
    try:
        b = get_browser()
        ctx = b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        page = ctx.new_page()
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
                if not price and '₽' in l:
                    n = re.sub(r'\D', '', l)
                    if n and 500 < int(n) < 500000: price = int(n)
                if not title and len(l) > 15 and '₽' not in l: title = l[:100]
            if title and price and title not in seen:
                seen.add(title)
                items.append({'title': title, 'price_num': price, 'price': f'{price} ₽', 'url': x['url'], 'marketplace': 'ozon'})
        ctx.close()
        print(f"Ozon: {len(items)}")
        return items[:12]
    except Exception as e:
        print(f"Ozon: {e}")
        return []

@app.route('/api/search/stream')
def search_stream():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400

    def gen():
        yield f"data: {json.dumps({'step': 'start', 'message': 'Ищем...'}, ensure_ascii=False)}\n\n"
        sq = normalize_query(query)
        yield f"data: {json.dumps({'step': 'norm', 'message': f'Запрос: {sq}'}, ensure_ascii=False)}\n\n"

        all_p = []

        yield f"data: {json.dumps({'step': 'wb', 'message': 'WB API...'}, ensure_ascii=False)}\n\n"
        wb = scrape_wb_api(sq)
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
        yield f"data: {json.dumps({'step': 'done', 'message': 'Готово!', 'result': {'query': query, 'normalized_query': sq, 'total_found': len(all_p), 'matching_products': res['matching'], 'excluded': res['excluded'], 'best_price': res['best_price'], 'summary': res['summary']}}, ensure_ascii=False)}\n\n"

    return Response(gen(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400
    sq = normalize_query(query)
    all_p = scrape_wb_api(sq) + scrape_ym(sq) + scrape_oz(sq)
    res = filter_products(all_p)
    return jsonify({'query': query, 'normalized_query': sq, 'total_found': len(all_p), 'matching_products': res['matching'], 'excluded': res['excluded'], 'best_price': res['best_price'], 'summary': res['summary']})

@app.route('/api/chat', methods=['POST'])
def chat():
    return jsonify({'response': 'Введи товар в поиск! '})

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print('Smart Price API v12 (WB API + Browser fallback)')
    print('http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, threaded=False)