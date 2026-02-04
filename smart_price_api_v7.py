# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from playwright.sync_api import sync_playwright
from gigachat import GigaChat
import time
import re
import json

app = Flask(__name__)
CORS(app)

GIGACHAT_KEY = "019b489a-39a3-7393-aeb1-095d8dfa01ac"

browser = None
pw = None

def clean_number(s):
    return re.sub(r'\D', '', s)

def get_browser():
    global browser, pw
    if browser is None:
        pw = sync_playwright().start()
        browser = pw.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--window-position=-32000,-32000']
        )
    return browser

def ai_normalize(q):
    try:
        with GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False) as giga:
            prompt = f'''Ты помощник интернет-магазина. Исправь запрос пользователя, убери опечатки и транслит.

ВАЖНЫЕ ПРИМЕРЫ:
- "посо фб на 256" -> "Poco F6 256GB" (смартфон)
- "посо ф6" -> "Poco F6" (смартфон)
- "редми ноут 13" -> "Redmi Note 13" (смартфон)
- "айфон 16 про" -> "iPhone 16 Pro" (смартфон)
- "самсунг с24" -> "Samsung Galaxy S24" (смартфон)
- "дрими л10с ультра" -> "Dreame L10s Ultra" (робот-пылесос)
- "эйрподс про 2" -> "AirPods Pro 2" (наушники)
- "макбук эйр м2" -> "MacBook Air M2" (ноутбук)
- "сяоми 14" -> "Xiaomi 14" (смартфон)
- "хуавей п60" -> "Huawei P60" (смартфон)
- "ван плас 12" -> "OnePlus 12" (смартфон)
- "гелакси бадс" -> "Galaxy Buds" (наушники)

Запрос: "{q}"

Верни ТОЛЬКО JSON без пояснений: {{"normalized_query": "исправленный запрос"}}'''
            response = giga.chat(prompt)
            text = response.choices[0].message.content
            text = re.sub(r'^```json\s*|\s*```$', '', text.strip())
            text = re.sub(r'^```\s*|\s*```$', '', text.strip())
            result = json.loads(text)
            print(f"AI: '{q}' -> '{result.get('normalized_query')}'")
            return result
    except Exception as e:
        print(f"AI Normalize Error: {e}")
        return {"normalized_query": q}

def ai_filter(query, norm_query, products):
    if not products:
        return {"matching": [], "excluded": [], "best_price": None, "summary": "Ничего не найдено"}
    try:
        with GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False) as giga:
            prompt = f'''Ты фильтруешь товары для покупателя.

Запрос: "{query}" (нормализован как "{norm_query}")

Товары:
{json.dumps(products[:20], ensure_ascii=False, indent=2)}

ПРАВИЛА:
1. Оставь ТОЛЬКО товары которые соответствуют запросу
2. Если ищут смартфон - убери чехлы, стекла, аксессуары
3. Если ищут наушники - убери чехлы, амбушюры
4. Если ищут пылесос - убери салфетки, щетки, фильтры
5. Проверяй модель - "Poco F6" это НЕ "Poco F5" и НЕ "Poco X6"

Верни ТОЛЬКО JSON:
{{"matching": [подходящие товары с title, price_num, marketplace, url], "excluded": [{{"title": "...", "reason": "..."}}], "best_price": {{самый дешевый из matching}}, "summary": "Найдено X товаров Poco F6 256GB. Лучшая цена: Y руб."}}'''
            response = giga.chat(prompt)
            text = response.choices[0].message.content
            text = re.sub(r'^```json\s*|\s*```$', '', text.strip())
            text = re.sub(r'^```\s*|\s*```$', '', text.strip())
            return json.loads(text)
    except Exception as e:
        print(f"AI Filter Error: {e}")
        products.sort(key=lambda x: x.get('price_num', 999999))
        return {"matching": products, "excluded": [], "best_price": products[0] if products else None, "summary": ""}

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
        print(f"WB Error: {e}")
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
        print(f"YM Error: {e}")
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
                items.append({'title': title, 'price_num': price, 'price': f'{price} rub', 'url': x['url'], 'marketplace': 'ozon'})
        return items[:12]
    except Exception as e:
        print(f"Ozon Error: {e}")
        return []
    finally:
        ctx.close()

@app.route('/api/search/stream')
def search_stream():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400

    def gen():
        yield f"data: {json.dumps({'step': 'ai', 'message': 'GigaChat анализирует запрос...'}, ensure_ascii=False)}\n\n"
        norm = ai_normalize(query)
        sq = norm.get('normalized_query', query)
        yield f"data: {json.dumps({'step': 'ai', 'message': f'Ищем: {sq}'}, ensure_ascii=False)}\n\n"

        all_p = []

        yield f"data: {json.dumps({'step': 'wb', 'message': 'Wildberries...'}, ensure_ascii=False)}\n\n"
        wb = scrape_wb(sq)
        all_p.extend(wb)
        yield f"data: {json.dumps({'step': 'wb', 'message': f'WB: {len(wb)} товаров'}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'step': 'ym', 'message': 'Яндекс Маркет...'}, ensure_ascii=False)}\n\n"
        ym = scrape_ym(sq)
        all_p.extend(ym)
        yield f"data: {json.dumps({'step': 'ym', 'message': f'Яндекс: {len(ym)} товаров'}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'step': 'oz', 'message': 'Ozon...'}, ensure_ascii=False)}\n\n"
        oz = scrape_oz(sq)
        all_p.extend(oz)
        yield f"data: {json.dumps({'step': 'oz', 'message': f'Ozon: {len(oz)} товаров'}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'step': 'filter', 'message': 'GigaChat фильтрует результаты...'}, ensure_ascii=False)}\n\n"
        res = ai_filter(query, sq, all_p)

        yield f"data: {json.dumps({'step': 'done', 'message': 'Готово!', 'result': {'query': query, 'normalized_query': sq, 'total_found': len(all_p), 'matching_products': res.get('matching', []), 'excluded': res.get('excluded', []), 'best_price': res.get('best_price'), 'summary': res.get('summary', '')}}, ensure_ascii=False)}\n\n"

    return Response(gen(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400
    norm = ai_normalize(query)
    sq = norm.get('normalized_query', query)
    all_p = scrape_wb(sq) + scrape_ym(sq) + scrape_oz(sq)
    res = ai_filter(query, sq, all_p) if all_p else {"matching": [], "excluded": [], "best_price": None, "summary": ""}
    return jsonify({'query': query, 'normalized_query': sq, 'total_found': len(all_p), 'matching_products': res.get('matching', []), 'excluded': res.get('excluded', []), 'best_price': res.get('best_price'), 'summary': res.get('summary', '')})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    msg = data.get('message', '')
    if not msg:
        return jsonify({'error': 'Message required'}), 400
    try:
        with GigaChat(credentials=GIGACHAT_KEY, verify_ssl_certs=False) as giga:
            prompt = f"Ты Фиксик-помогатор, дружелюбный AI-ассистент для шоппинга. Помогаешь выбрать товар, сравниваешь характеристики. Отвечай кратко на русском.\n\nВопрос: {msg}"
            response = giga.chat(prompt)
            return jsonify({'response': response.choices[0].message.content})
    except Exception as e:
        return jsonify({'response': f'Ошибка: {e}'})

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'ai': 'GigaChat'})

if __name__ == '__main__':
    print('Smart Price API v7 (GigaChat improved)')
    print('http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, threaded=False)