from playwright.sync_api import sync_playwright
import time
import json
import re

def parse_price(price_str):
    """Извлекает число из строки цены"""
    if not price_str:
        return None
    cleaned = re.sub(r'[^\d]', '', price_str)
    return int(cleaned) if cleaned else None

def scrape_wildberries(browser, query):
    print(f'\n=== Wildberries: {query} ===')
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    try:
        page.goto('https://www.wildberries.ru/')
        time.sleep(2)
        page.goto(f'https://www.wildberries.ru/catalog/0/search.aspx?search={query}')
        page.wait_for_selector('[data-nm-id]', timeout=10000)
        time.sleep(3)
        products = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('[data-nm-id]')).map(card => {
                const id = card.getAttribute('data-nm-id');
                const title = card.querySelector('.product-card__name')?.innerText?.trim() || '';
                const price = card.querySelector('.price__lower-price')?.innerText?.trim() || '';
                return { external_id: id, title, price, url: 'https://www.wildberries.ru/catalog/' + id + '/detail.aspx', marketplace: 'wildberries' };
            });
        }""")
        return products
    except Exception as e:
        print(f'  Error: {e}')
        return []
    finally:
        context.close()

def scrape_yandex_market(browser, query):
    print(f'\n=== Yandex Market: {query} ===')
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    try:
        page.goto(f'https://market.yandex.ru/search?text={query}')
        time.sleep(4)
        page.keyboard.press('Escape')
        time.sleep(1)
        page.keyboard.press('Escape')
        time.sleep(1)
        
        products = page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('[data-auto="snippet-title"]').forEach(titleEl => {
                const card = titleEl.closest('article') || titleEl.closest('[data-apiary-widget-name]');
                const linkEl = card?.querySelector('a') || titleEl.closest('a');
                const priceEl = card?.querySelector('[data-auto="price-value"]') || card?.querySelector('[data-auto="snippet-price-current"]');
                const title = titleEl.innerText?.trim();
                if (title) {
                    results.push({
                        title: title,
                        price: priceEl?.innerText?.trim() || '',
                        url: linkEl?.href || '',
                        marketplace: 'yandex'
                    });
                }
            });
            return results;
        }""")
        return products
    except Exception as e:
        print(f'  Error: {e}')
        return []
    finally:
        context.close()

def scrape_aliexpress(browser, query):
    print(f'\n=== AliExpress: {query} ===')
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    try:
        page.goto(f'https://aliexpress.ru/wholesale?SearchText={query}')
        time.sleep(5)
        products = page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('a[href*="/item/"]').forEach(a => {
                const card = a.closest('div[class*="card"]') || a.parentElement;
                const title = a.innerText?.trim()?.slice(0, 100) || '';
                const priceEl = card?.querySelector('[class*="price"]');
                if (title && title.length > 5) {
                    results.push({ title, price: priceEl?.innerText?.trim() || '', url: a.href, marketplace: 'aliexpress' });
                }
            });
            const seen = new Set();
            return results.filter(p => { if (seen.has(p.url)) return false; seen.add(p.url); return true; });
        }""")
        return products
    except Exception as e:
        print(f'  Error: {e}')
        return []
    finally:
        context.close()

def scrape_ozon(browser, query):
    print(f'\n=== Ozon: {query} ===')
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    try:
        page.goto(f'https://www.ozon.ru/search/?text={query}&from_global=true')
        time.sleep(6)
        page.evaluate('window.scrollBy(0, 800)')
        time.sleep(2)
        products = page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('a[href*="/product/"]').forEach(a => {
                const text = a.innerText?.trim();
                if (text && text.length > 15 && text.length < 200 && !text.includes('Ozon') && !text.includes('баллов')) {
                    results.push({ title: text.slice(0, 100), price: '', url: a.href, marketplace: 'ozon' });
                }
            });
            const seen = new Set();
            return results.filter(p => { const key = p.title.slice(0, 25); if (seen.has(key)) return false; seen.add(key); return true; });
        }""")
        return products
    except Exception as e:
        print(f'  Error: {e}')
        return []
    finally:
        context.close()

def search_all_marketplaces(query, max_per_market=10):
    """Поиск по всем маркетплейсам"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        
        all_products = []
        
        for scraper, name in [(scrape_wildberries, 'WB'), (scrape_yandex_market, 'YM'), (scrape_aliexpress, 'Ali'), (scrape_ozon, 'Ozon')]:
            products = scraper(browser, query)[:max_per_market]
            print(f'  Found: {len(products)} products')
            all_products.extend(products)
        
        browser.close()
        
        # Нормализуем цены
        for p in all_products:
            p['price_num'] = parse_price(p.get('price', ''))
        
        return all_products

# MAIN
if __name__ == '__main__':
    query = 'iphone 16 128gb'
    products = search_all_marketplaces(query, max_per_market=10)
    
    print(f'\n{"="*70}')
    print(f'ИТОГО: {len(products)} товаров по запросу "{query}"')
    print(f'{"="*70}')
    
    # Группируем и сортируем по цене
    for mp in ['wildberries', 'yandex', 'aliexpress', 'ozon']:
        items = sorted([p for p in products if p['marketplace'] == mp], key=lambda x: x['price_num'] or 999999)
        print(f'\n[{mp.upper()}] - {len(items)} товаров:')
        for prod in items[:5]:
            title = prod['title'][:45]
            price = f"{prod['price_num']:,} " if prod['price_num'] else prod['price'][:20]
            print(f"  {price:>12}  {title}")
    
    # Находим минимальную цену
    with_prices = [p for p in products if p['price_num']]
    if with_prices:
        cheapest = min(with_prices, key=lambda x: x['price_num'])
        print(f'\n ЛУЧШАЯ ЦЕНА: {cheapest["price_num"]:,}  на {cheapest["marketplace"].upper()}')
        print(f'   {cheapest["title"][:60]}')
        print(f'   {cheapest["url"]}')
    
    # Сохраняем
    with open('search_results.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f'\nСохранено в search_results.json')
