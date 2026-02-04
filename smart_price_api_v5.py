# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from playwright.sync_api import sync_playwright
from groq import Groq
import time
import re
import json

app = Flask(__name__)
CORS(app)

groq_client = Groq(api_key="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")

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
        r = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": f'Fix typos, transliterate: "{q}". Examples: "airpods pro 2" -> "AirPods Pro 2", "ayfon 16" -> "iPhone 16". Return JSON: {{"normalized_query": "..."}}'} ],
            temperature=0.1
        )
        text = re.sub(r'^```json\s*|\s*```$', '', r.choices[0].message.content.strip())
        return json.loads(text)
    except:
        return {"normalized_query": q}

def ai_filter(query, products):
    if not products:
        return {"matching": [], "excluded": [], "best_price": None, "summary": "Nothing found"}
    try:
        r = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": f'Query: "{query}". Products: {json.dumps(products[:25], ensure_ascii=False)}. Keep ONLY matching products (no accessories). Return JSON: {{"matching": [products with title,price_num,marketplace,url], "excluded": [{{"title":"...", "reason":"..."}}], "best_price": {{cheapest matching}}, "summary": "short summary in Russian"}}'}],
            temperature=0.1
        )
        text = re.sub(r'^```json\s*|\s*```$', '', r.choices[0].message.content.strip())
        return json.loads(text)
    except Exception as e:
        return {"matching": products, "excluded": [], "best_price": products[0] if products else None, "summary": str(e)}

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
    except:
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
    except:
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
                if not price and l.endswith('\u20bd'):
                    n = clean_number(l)
                    if n and 500 < int(n) < 500000: price = int(n)
                if not title and len(l) > 15 and '\u20bd' not in l: title = l[:100]
            if title and price and title not in seen:
                seen.add(title)
                items.append({'title': title, 'price_num': price, 'price': f'{price} rub', 'url': x['url'], 'marketplace': 'ozon'})
        return items[:12]
    except:
        return []
    finally:
        ctx.close()

@app.route('/api/search/stream')
def search_stream():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400

    def gen():
        yield f"data: {json.dumps({'step': 'ai', 'message': 'AI analyzing...'})}\n\n"
        norm = ai_normalize(query)
        sq = norm.get('normalized_query', query)
        yield f"data: {json.dumps({'step': 'ai', 'message': f'Searching: {sq}'})}\n\n"

        all_p = []

        yield f"data: {json.dumps({'step': 'wb', 'message': 'Wildberries...'})}\n\n"
        wb = scrape_wb(sq)
        all_p.extend(wb)
        yield f"data: {json.dumps({'step': 'wb', 'message': f'WB: {len(wb)} items'})}\n\n"

        yield f"data: {json.dumps({'step': 'ym', 'message': 'Yandex Market...'})}\n\n"
        ym = scrape_ym(sq)
        all_p.extend(ym)
        yield f"data: {json.dumps({'step': 'ym', 'message': f'YM: {len(ym)} items'})}\n\n"

        yield f"data: {json.dumps({'step': 'oz', 'message': 'Ozon...'})}\n\n"
        oz = scrape_oz(sq)
        all_p.extend(oz)
        yield f"data: {json.dumps({'step': 'oz', 'message': f'Ozon: {len(oz)} items'})}\n\n"

        yield f"data: {json.dumps({'step': 'filter', 'message': 'AI filtering...'})}\n\n"
        res = ai_filter(query, all_p)

        yield f"data: {json.dumps({'step': 'done', 'message': 'Done!', 'result': {'query': query, 'normalized_query': sq, 'total_found': len(all_p), 'matching_products': res.get('matching', []), 'excluded': res.get('excluded', []), 'best_price': res.get('best_price'), 'summary': res.get('summary', '')}})}\n\n"

    return Response(gen(), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

@app.route('/api/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400
    norm = ai_normalize(query)
    sq = norm.get('normalized_query', query)
    all_p = scrape_wb(sq) + scrape_ym(sq) + scrape_oz(sq)
    res = ai_filter(query, all_p) if all_p else {"matching": [], "excluded": [], "best_price": None, "summary": ""}
    return jsonify({'query': query, 'normalized_query': sq, 'total_found': len(all_p), 'matching_products': res.get('matching', []), 'excluded': res.get('excluded', []), 'best_price': res.get('best_price'), 'summary': res.get('summary', '')})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    msg = data.get('message', '')
    if not msg:
        return jsonify({'error': 'Message required'}), 400
    try:
        r = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are Fixik-helper, a friendly shopping AI assistant. Answer in Russian, be brief."},
                {"role": "user", "content": msg}
            ],
            temperature=0.7
        )
        return jsonify({'response': r.choices[0].message.content})
    except Exception as e:
        return jsonify({'response': f'Error: {e}'})

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print('Smart Price API v5')
    print('http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, threaded=False)
