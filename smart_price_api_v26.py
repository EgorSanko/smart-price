# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import httpx
import re
import json
import time
from urllib.parse import quote_plus
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
    exclude = {'чехол', 'кейс', 'стекло', 'пленка', 'кабель', 'зарядк', 'ремешок', 'адаптер', 'подставк'}
    matching = [p for p in products if p.get('price_num', 0) > 0 and not any(w in p.get('title', '').lower() for w in exclude)]
    matching.sort(key=lambda x: x.get('price_num', 999999))
    return {"matching": matching, "best_price": matching[0] if matching else None, "summary": f"Найдено {len(matching)} товаров"}


# ============ DuckDuckGo universal scraper ============

def scrape_via_ddg(query, site_domain, marketplace_name, cache_prefix):
    """Универсальный парсер через DuckDuckGo site: оператор"""
    cached = get_cached(f"{cache_prefix}:{query}")
    if cached:
        return cached

    items = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9',
        }

        search_q = f'{query} {site_domain} цена'
        url = f'https://html.duckduckgo.com/html/?q={quote_plus(search_q)}'

        with httpx.Client(timeout=15, headers=headers, follow_redirects=True) as client:
            r = client.get(url)

        print(f"{marketplace_name} DDG status: {r.status_code}, len: {len(r.text)}")

        # DuckDuckGo HTML results: <a class="result__a"> and <a class="result__snippet">
        # Extract links containing target domain
        domain_clean = site_domain.replace('site:', '')

        # Pattern: find all result blocks
        results = re.findall(
            r'<a[^>]+class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
            r.text, re.DOTALL
        )

        if not results:
            # Fallback pattern
            results = re.findall(
                r'href="([^"]*' + re.escape(domain_clean) + r'[^"]*)"[^>]*>(.*?)</a>.*?'
                r'class="result__snippet"[^>]*>(.*?)</a>',
                r.text, re.DOTALL
            )

        seen = set()
        for link, title_html, snippet in results[:15]:
            try:
                # Check domain
                if domain_clean not in link:
                    continue

                # Clean title
                title = re.sub(r'<[^>]+>', '', title_html).strip()
                title = title[:100]

                # Extract price from snippet
                snippet_clean = re.sub(r'<[^>]+>', '', snippet)
                price_match = re.search(r'(\d[\d\s]*)\s*₽', snippet_clean)
                if not price_match:
                    price_match = re.search(r'(\d[\d\s]*)\s*руб', snippet_clean, re.IGNORECASE)
                if not price_match:
                    # Try just numbers after "цена" or "от"
                    price_match = re.search(r'(?:цена|от|стоимость)[:\s]*(\d[\d\s]*)', snippet_clean, re.IGNORECASE)

                price_num = 0
                if price_match:
                    price_num = int(re.sub(r'\s', '', price_match.group(1)))

                # Skip if no price but still add with URL
                if title and title not in seen:
                    seen.add(title)
                    if price_num > 500 and price_num < 500000:
                        items.append({
                            'title': title,
                            'price_num': price_num,
                            'url': link,
                            'marketplace': marketplace_name
                        })
            except:
                continue

        print(f"{marketplace_name}: {len(items)}")
        set_cache(f"{cache_prefix}:{query}", items)
    except Exception as e:
        print(f"{marketplace_name} Error: {e}")

    return items


# ============ Individual parsers ============

def scrape_yandex(query):
    """Яндекс Маркет - httpx + regex"""
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
            browser = p.chromium.launch(headless=False, args=['--window-position=-32000,-32000'])
            page = browser.new_page()
            page.goto(f'https://www.wildberries.ru/catalog/0/search.aspx?search={query}', timeout=30000)

            try:
                page.wait_for_selector('article[data-nm-id]', timeout=10000)
            except:
                try:
                    page.wait_for_selector('.product-card-list', timeout=5000)
                except:
                    page.wait_for_timeout(5000)

            content = page.content()

            matches = re.findall(r'data-nm-id="(\d+)"', content)
            prices = re.findall(r'(\d[\d\s]*)&nbsp;₽|(\d[\d\s]*)\s*₽', content)
            titles = re.findall(r'class="[^"]*product-card__name[^"]*"[^>]*>([^<]+)<', content)

            if not titles:
                titles = re.findall(r'<span[^>]*>([^<]{10,80})</span>', content)

            price_list = []
            for pr in prices:
                val = pr[0] if pr[0] else pr[1]
                price_list.append(val)

            seen = set()
            for i, prod_id in enumerate(matches[:15]):
                try:
                    title = titles[i].strip() if i < len(titles) else f"Товар {prod_id}"
                    price_raw = price_list[i] if i < len(price_list) else "0"
                    price_num = int(re.sub(r'[^\d]', '', price_raw))
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
    return scrape_via_ddg(query, 'ozon.ru', 'ozon', 'oz')

def scrape_dns(query):
    return scrape_via_ddg(query, 'dns-shop.ru', 'dns', 'dns')

def scrape_citilink(query):
    return scrape_via_ddg(query, 'citilink.ru', 'citilink', 'cl')

def scrape_mvideo(query):
    return scrape_via_ddg(query, 'mvideo.ru', 'mvideo', 'mv')


PARSERS = {
    'yandex':      {'name': 'Яндекс Маркет', 'fn': scrape_yandex,      'enabled': True, 'color': '#ffcc00'},
    'wildberries': {'name': 'Wildberries',    'fn': scrape_wildberries, 'enabled': True, 'color': '#cb11ab'},
    'ozon':        {'name': 'Ozon',           'fn': scrape_ozon,        'enabled': True, 'color': '#005bff'},
    'dns':         {'name': 'DNS',            'fn': scrape_dns,         'enabled': True, 'color': '#ff6600'},
    'citilink':    {'name': 'Ситилинк',       'fn': scrape_citilink,    'enabled': True, 'color': '#00a046'},
    'mvideo':      {'name': 'МВидео',         'fn': scrape_mvideo,      'enabled': True, 'color': '#e40051'},
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


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'cache_size': len(CACHE), 'parsers': len([p for p in PARSERS.values() if p['enabled']])})


if __name__ == '__main__':
    print('Smart Price API v26')
    print('6 marketplaces:')
    for k, v in PARSERS.items():
        method = 'httpx' if k == 'yandex' else 'Playwright' if k == 'wildberries' else 'DuckDuckGo'
        print(f'  {v["name"]}: {method}')
    print('http://localhost:5000')
    app.run(host='0.0.0.0', port=5000, threaded=False)