from flask import Flask, jsonify, request
from flask_cors import CORS
from playwright.sync_api import sync_playwright
from groq import Groq
import time
import re
import json

app = Flask(__name__)
CORS(app)

# Groq клиент
groq_client = Groq(api_key="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")

# Браузер
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
        print(f"WB Error: {e}")
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
        print(f"Yandex Error: {e}")
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
                    if c and 5000 < int(c) < 500000:
                        price = int(c)
                if not title and len(l) > 20 and '₽' not in l:
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
        print(f"Ozon Error: {e}")
        return []
    finally:
        context.close()

# ============ AI FUNCTIONS ============

def ai_filter_products(query, products):
    """AI фильтрация товаров"""
    if not products:
        return {"matching": [], "excluded": [], "best_price": None, "summary": "Ничего не найдено"}
    
    prompt = f"""Пользователь ищет: "{query}"

Список товаров:
{json.dumps(products[:30], ensure_ascii=False, indent=2)}

Задача  определи какие товары ТОЧНО соответствуют запросу:
- iPhone 16e  iPhone 16 (это разные модели!)
- iPhone 16 Pro/Plus  iPhone 16
- 128GB  256GB
- Учитывай бренд, модель, память

Верни ТОЛЬКО JSON (без markdown):
{{"matching": [список подходящих товаров], "excluded": [{{"title": "...", "reason": "..."}}], "best_price": {{лучший товар}}, "summary": "вывод"}}"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        text = response.choices[0].message.content
        # Убираем markdown если есть
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        return json.loads(text)
    except Exception as e:
        print(f"AI Error: {e}")
        # Fallback - возвращаем всё
        return {
            "matching": products,
            "excluded": [],
            "best_price": min(products, key=lambda x: x.get('price_num', 999999)) if products else None,
            "summary": "AI недоступен, показаны все результаты"
        }

def ai_chat(message, context=None):
    """AI ассистент - Фиксик-помогатор"""
    system_prompt = """Ты  Фиксик-помогатор, AI-ассистент для умного шоппинга в Smart Price.

Твои возможности:
- Помогаешь выбрать товар (сравниваешь характеристики)
- Объясняешь разницу между моделями
- Даёшь советы что лучше купить
- Отвечаешь на вопросы о технике

Стиль общения:
- Дружелюбный и полезный
- Кратко и по делу
- Используй эмодзи иногда
- На русском языке

Если пользователь хочет найти товар  скажи что нужно использовать поиск (ты не можешь искать сам)."""

    messages = [{"role": "system", "content": system_prompt}]
    
    if context:
        messages.append({"role": "user", "content": f"Контекст последнего поиска:\n{context}"})
        messages.append({"role": "assistant", "content": "Понял, учту это в ответе."})
    
    messages.append({"role": "user", "content": message})
    
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Ошибка AI: {e}"

# ============ API ROUTES ============

@app.route('/api/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    use_ai = request.args.get('ai', 'true').lower() == 'true'
    
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    print(f"\n Поиск: {query}")
    
    all_products = []
    
    # Скрейпинг
    print("   Wildberries...")
    wb = scrape_wildberries(query)
    print(f"    Найдено: {len(wb)}")
    all_products.extend(wb)
    
    print("   Яндекс.Маркет...")
    ym = scrape_yandex(query)
    print(f"    Найдено: {len(ym)}")
    all_products.extend(ym)
    
    print("   Ozon...")
    oz = scrape_ozon(query)
    print(f"    Найдено: {len(oz)}")
    all_products.extend(oz)
    
    print(f" Всего: {len(all_products)}")
    
    # AI фильтрация
    if use_ai and all_products:
        print(" AI анализ...")
        ai_result = ai_filter_products(query, all_products)
        return jsonify({
            'query': query,
            'total_found': len(all_products),
            'total_matching': len(ai_result.get('matching', [])),
            'matching_products': ai_result.get('matching', []),
            'excluded': ai_result.get('excluded', []),
            'best_price': ai_result.get('best_price'),
            'summary': ai_result.get('summary', ''),
            'all_products': all_products
        })
    else:
        # Без AI - просто сортировка по цене
        all_products.sort(key=lambda x: x.get('price_num') or 999999)
        valid = [p for p in all_products if p.get('price_num', 0) > 1000]
        return jsonify({
            'query': query,
            'total_found': len(all_products),
            'products': all_products,
            'best_price': valid[0] if valid else None
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
    return jsonify({'status': 'ok', 'ai': 'groq', 'browser': browser is not None})

if __name__ == '__main__':
    print(" Smart Price API + AI")
    print(" http://localhost:5000")
    print("=" * 40)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=False)
