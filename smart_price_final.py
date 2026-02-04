from playwright.sync_api import sync_playwright
import time
import re
import json

def clean_number(s):
    return re.sub(r'\D', '', s)

def scrape_wildberries(browser, query):
    print(f'\n=== Wildberries ===')
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
        for p in products:
            c = clean_number(p['price'])
            p['price_num'] = int(c) if c else 0
        return products
    except Exception as e:
        print(f'  Error: {e}')
        return []
    finally:
        context.close()

def scrape_yandex(browser, query):
    print(f'\n=== Yandex Market ===')
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    try:
        page.goto(f'https://market.yandex.ru/search?text={query}')
        time.sleep(4)
        page.keyboard.press('Escape')
        time.sleep(0.5)
        page.keyboard.press('Escape')
        time.sleep(0.5)
        try:
            page.click('button:has-text("Allow all")', timeout=2000)
        except:
            pass
        time.sleep(1)
        
        products = page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('[data-auto="snippet-title"]').forEach(titleEl => {
                const card = titleEl.closest('article') || titleEl.closest('[data-apiary-widget-name]');
                const linkEl = card?.querySelector('a') || titleEl.closest('a');
                const priceEl = card?.querySelector('[data-auto="snippet-price-current"]');
                const title = titleEl.innerText?.trim();
                if (title) {
                    results.push({ title, price: priceEl?.innerText?.trim() || '', url: linkEl?.href || '', marketplace: 'yandex' });
                }
            });
            return results;
        }""")
        for p in products:
            c = clean_number(p['price'])
            p['price_num'] = int(c) if c else 0
        return products
    except Exception as e:
        print(f'  Error: {e}')
        return []
    finally:
        context.close()

def scrape_ozon(browser, query):
    print(f'\n=== Ozon ===')
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    try:
        page.goto(f'https://www.ozon.ru/search/?text={query}')
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
            return data;
        }""")
        products = []
        seen = set()
        for item in raw:
            lines = item['text'].split('\n')
            price = None
            title = None
            for line in lines:
                l = line.strip()
                if not price and l.endswith('₽'):
                    c = clean_number(l)
                    if c:
                        num = int(c)
                        if 5000 < num < 500000:
                            price = num
                if not title and 'iPhone' in l and len(l) > 25:
                    title = l[:100]
            if title and price and title not in seen:
                seen.add(title)
                products.append({'title': title, 'price': f'{price:,} ₽'.replace(',', ' '), 'price_num': price, 'url': item['url'], 'marketplace': 'ozon'})
        return products
    except Exception as e:
        print(f'  Error: {e}')
        return []
    finally:
        context.close()

def scrape_aliexpress(browser, query):
    print(f'\n=== AliExpress ===')
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    try:
        page.goto(f'https://aliexpress.ru/wholesale?SearchText={query}')
        time.sleep(6)
        page.evaluate('window.scrollBy(0, 800)')
        time.sleep(2)
        
        raw = page.evaluate("""() => {
            const data = [];
            const links = document.querySelectorAll('a[href*="/item/"]');
            const seen = new Set();
            links.forEach(link => {
                const url = link.href.split('?')[0];
                if (seen.has(url)) return;
                seen.add(url);
                let card = link.parentElement;
                for (let i = 0; i < 6; i++) {
                    if (card && card.parentElement) card = card.parentElement;
                }
                data.push({ url, text: card ? card.innerText : link.innerText });
            });
            return data;
        }""")
        
        products = []
        seen = set()
        for item in raw:
            text = item['text']
            price = None
            title = None
            
            # Ищем все цены
            for line in text.split('\n'):
                if '₽' in line and not price:
                    c = clean_number(line)
                    if c:
                        num = int(c)
                        if 15000 < num < 300000:
                            price = num
                            break
            
            # Название
            for line in text.split('\n'):
                l = line.strip()
                if len(l) > 30 and ('iphone' in l.lower() or 'смартфон' in l.lower()):
                    if '₽' not in l and 'СКИДКА' not in l and 'купон' not in l.lower():
                        title = l[:100]
                        break
            
            if title and price and title not in seen:
                seen.add(title)
                products.append({'title': title, 'price': f'{price:,} ₽'.replace(',', ' '), 'price_num': price, 'url': item['url'], 'marketplace': 'aliexpress'})
        
        return products
    except Exception as e:
        print(f'  Error: {e}')
        return []
    finally:
        context.close()

def search_all(query, max_per_market=15):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        all_products = []
        
        for scraper in [scrape_wildberries, scrape_yandex, scrape_ozon, scrape_aliexpress]:
            products = scraper(browser, query)[:max_per_market]
            print(f'  Found: {len(products)}')
            all_products.extend(products)
        
        browser.close()
        return all_products

if __name__ == '__main__':
    query = 'iphone 16 128gb'
    products = search_all(query)
    
    print(f'\n{"="*70}')
    print(f'ИТОГО: {len(products)} товаров "{query}"')
    print(f'{"="*70}')
    
    for mp in ['wildberries', 'yandex', 'ozon', 'aliexpress']:
        items = sorted([p for p in products if p['marketplace'] == mp and p.get('price_num', 0) > 0], key=lambda x: x['price_num'])
        print(f'\n[{mp.upper()}] - {len(items)} товаров:')
        for prod in items[:5]:
            print(f"  {prod['price_num']:>8,} ₽  {prod['title'][:42]}")
    
    with_price = [p for p in products if p.get('price_num', 0) > 30000]
    if with_price:
        best = min(with_price, key=lambda x: x['price_num'])
        print(f'\n{"="*70}')
        print(f'ЛУЧШАЯ ЦЕНА: {best["price_num"]:,} ₽ на {best["marketplace"].upper()}')
        print(f'   {best["title"]}')
        print(f'   {best["url"]}')
    
    with open('smart_price_results.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f'\nСохранено: smart_price_results.json')
