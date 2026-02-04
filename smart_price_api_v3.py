from flask import Flask, jsonify, request
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
playwright_instance = None

def clean_number(s):
    return re.sub(r'\D', '', s)

def get_browser():
    global browser, playwright_instance
    if browser is None:
        playwright_instance = sync_playwright().start()
        browser = playwright_instance.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
    return browser

# ============ AI QUERY NORMALIZER ============

def ai_normalize_query(user_query):
    """AI нормализует запрос пользователя"""
    prompt = f"""Пользователь хочет найти товар: "{user_query}"

Задача:
1. Исправь опечатки и транслитерацию
2. Определи правильное название бренда и модели
3. Добавь тип товара если понятно из контекста

Примеры:
- "дрими л10с ультра"  "Dreame L10s Ultra робот-пылесос"
- "айфон 16 про 256"  "iPhone 16 Pro 256GB"
- "самсунг с24 ультра"  "Samsung Galaxy S24 Ultra"
- "сяоми редми ноут 13"  "Xiaomi Redmi Note 13"
- "макбук эир м2"  "MacBook Air M2"
- "сони хм5"  "Sony WH-1000XM5 наушники"
- "дайсон в15"  "Dyson V15 пылесос"

Верни ТОЛЬКО JSON:
{{"normalized_query": "исправленный запрос", "brand": "бренд", "model": "модель", "category": "категория товара", "confidence": 0.9}}

Если не уверен - верни оригинальный запрос с confidence < 0.5"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        text = response.choices[0].message.content
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        result = json.loads(text)
        print(f"   AI нормализация: '{user_query}'  '{result.get('normalized_query')}'")
        return result
    except Exception as e:
        print(f"  AI Normalize Error: {e}")
        return {"normalized_query": user_query, "confidence": 0}

# ============ AI FILTER ============

def ai_filter_products(original_query, normalized_info, products):
    """AI фильтрует товары по релевантности"""
    if not products:
        return {"matching": [], "excluded": [], "best_price": None, "summary": "Ничего не найдено"}
    
    prompt = f"""Пользователь искал: "{original_query}"
Мы поняли это как: {json.dumps(normalized_info, ensure_ascii=False)}

Найденные товары:
{json.dumps(products[:30], ensure_ascii=False, indent=2)}

Задача  оставь ТОЛЬКО товары которые соответствуют запросу:
- Салфетки, щётки, аксессуары  это НЕ сам пылесос!
- Чехлы, плёнки  это НЕ сам телефон!
- Проверяй бренд и модель

Верни ТОЛЬКО JSON:
{{"matching": [подходящие товары с полями title, price_num, marketplace, url], "excluded": [{{"title": "...", "reason": "..."}}], "best_price": {{лучший товар}}, "summary": "краткий вывод для пользователя"}}"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        text = response.choices[0].message.content
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        return json.loads(text)
    except Exception as e:
        print(f"  AI Filter Error: {e}")
        products_sorted = sorted(products, key=lambda x: x.get('price_num') or 999999)
        return {
            "matching": products_sorted,
            "excluded": [],
            "best_price": products_sorted[0] if products_sorted else None,
            "summary": "AI фильтрация недоступна"
        }

# ============ SCRAPERS ============

def scrape_wildberries(query):
    b = get_browser()
    context = b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    try:
        page.goto('https://www.wildberries.ru/', timeout=15000)
        time.sleep(2)
        page.goto(f'https://www.wildberries.ru/catalog/0/search.aspx?search={query}', timeout=15000)
        page.wait_for_selector('[data-nm-id]', timeout=10000)
        time.sleep(2)
        products = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('[data-nm-id]')).slice(0, 15).map(card => {
                const id = card.getAttribute('data-nm-id');
                return {
                    external_id: id,
                    title: card.querySelector('.product-card__name')?.innerText?.trim() || '',
                    price: card.querySelector('.price__lower-price')?.innerText?.trim() || '',
                    url: 'https://www.wildberries.ru/catalog/' + id + '/detail.aspx',
                    marketplace: 'wildberries'
                };
            });
        }""")
        for p in products:
            c = clean_number(p['price'])
            p['price_num'] = int(c) if c else 0
        return products
    except Exception as e:
        print(f"  WB Error: {e}")
        return []
    finally:
        context.close()

def scrape_yandex(query):
    b = get_browser()
    context = b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    try:
        page.goto(f'https://market.yandex.ru/search?text={query}', timeout=15000)
        time.sleep(4)
        page.keyboard.press('Escape')
        time.sleep(1)
        products = page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('[data-auto="snippet-title"]').forEach(titleEl => {
                const card = titleEl.closest('article') || titleEl.closest('[data-apiary-widget-name]');
                const linkEl = card?.querySelector('a') || titleEl.closest('a');
                const priceEl = card?.querySelector('[data-auto="snippet-price-current"]');
                if (titleEl.innerText?.trim()) {
                    results.push({
                        title: titleEl.innerText.trim(),
                        price: priceEl?.innerText?.trim() || '',
                        url: linkEl?.href || '',
                        marketplace: 'yandex'
                    });
                }
            });
            return results.slice(0, 15);
        }""")
        for p in products:
            c = clean_number(p['price'])
            p['price_num'] = int(c) if c else 0
        return products
    except Exception as e:
        print(f"  Yandex Error: {e}")
        return []
    finally:
        context.close()

def scrape_ozon(query):
    b = get_browser()
    context = b.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    try:
        page.goto(f'https://www.ozon.ru/search/?text={query}', timeout=20000)
        time.sleep(6)
        raw = page.evaluate("""() => {
            const data = [];
            const links = document.querySelectorAll('a[href*="/product/"]');
            const seen = new Set();
            links.forEach(link => {
                if (seen.has(link.href)) return;
                seen.add(link.href);
                const card = link.closest('div[class]');
                data.push({ url: link.href, text: card ? card.innerText : link.innerText });
            });
            return data.slice(0, 20);
        }""")
        products = []
        seen = set()
        for item in raw:
            lines = item['text'].split('\n')
            price, title = None, None
            for line in lines:
                l = line.strip()
                if not price and l.endswith('₽'):
                    c = clean_number(l)
                    if c and 500 < int(c) < 500000:
                        price = int(c)
                if not title and len(l) > 15 and '₽' not in l and 'доставк' not in l.lower():
                    title = l[:100]
            if title and price and title not in seen:
                seen.add(title)
                products.append({
                    'title': title,
                    'price': f'{price:,} ₽'.replace(',', ' '),
                    'price_num': price,
                    'url': item['url'],
                    'marketplace': 'ozon'
                })
        return products[:15]
    except Exception as e:
        print(f"  Ozon Error: {e}")
        return []
    finally:
        context.close()

# ============ AI CHAT ============

def ai_chat(message, context=None):
    system_prompt = """Ты  Фиксик-помогатор, AI-ассистент для умного шоппинга.

Возможности:
- Помогаешь выбрать товар
- Сравниваешь характеристики
- Даёшь советы что лучше купить
- Объясняешь разницу между моделями

Если пользователь хочет найти товар  предложи использовать поиск на сайте.
Отвечай кратко, дружелюбно, на русском."""

    messages = [{"role": "system", "content": system_prompt}]
    if context:
        messages.append({"role": "user", "content": f"Контекст: {context}"})
        messages.append({"role": "assistant", "content": "Понял, учту."})
    messages.append({"role": "user", "content": message})
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка: {e}"

# ============ API ROUTES ============

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    use_ai = request.args.get('ai', 'true').lower() == 'true'
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    print(f"\n{'='*50}")
    print(f" Запрос: {query}")
    
    # Шаг 1: AI нормализация запроса
    normalized_info = {"normalized_query": query}
    search_query = query
    
    if use_ai:
        print(" Нормализация запроса...")
        normalized_info = ai_normalize_query(query)
        search_query = normalized_info.get('normalized_query', query)
    
    print(f" Ищем: {search_query}")
    
    # Шаг 2: Скрейпинг
    all_products = []
    
    print("   Wildberries...")
    wb = scrape_wildberries(search_query)
    print(f"    Найдено: {len(wb)}")
    all_products.extend(wb)
    
    print("   Яндекс.Маркет...")
    ym = scrape_yandex(search_query)
    print(f"    Найдено: {len(ym)}")
    all_products.extend(ym)
    
    print("   Ozon...")
    oz = scrape_ozon(search_query)
    print(f"    Найдено: {len(oz)}")
    all_products.extend(oz)
    
    print(f" Всего: {len(all_products)}")
    
    # Шаг 3: AI фильтрация
    if use_ai and all_products:
        print(" Фильтрация результатов...")
        ai_result = ai_filter_products(query, normalized_info, all_products)
        
        return jsonify({
            'query': query,
            'normalized_query': search_query,
            'normalized_info': normalized_info,
            'total_found': len(all_products),
            'total_matching': len(ai_result.get('matching', [])),
            'matching_products': ai_result.get('matching', []),
            'excluded': ai_result.get('excluded', []),
            'best_price': ai_result.get('best_price'),
            'summary': ai_result.get('summary', ''),
            'all_products': all_products
        })
    else:
        all_products.sort(key=lambda x: x.get('price_num') or 999999)
        return jsonify({
            'query': query,
            'total_found': len(all_products),
            'products': all_products,
            'best_price': all_products[0] if all_products else None
        })

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    message = data.get('message', '')
    context = data.get('context', '')
    
    if not message:
        return jsonify({'error': 'Message required'}), 400
    
    print(f"\n Чат: {message[:50]}...")
    response = ai_chat(message, context)
    return jsonify({'response': response})

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print(" Smart Price API v3 (с AI нормализацией)")
    print(" http://localhost:5000")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=False)
