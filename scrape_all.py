from playwright.sync_api import sync_playwright
import time
import json

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
            return Array.from(document.querySelectorAll('[data-nm-id]')).slice(0, 10).map(card => {
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
        page.goto(f'https://market.yandex.ru/search?text={query}', wait_until='domcontentloaded')
        time.sleep(3)
        
        # Закрываем модалку если есть
        try:
            close_btn = page.query_selector('button[aria-label="Закрыть"]') or page.query_selector('[data-auto="close-popup"]') or page.query_selector('.modal-close') or page.query_selector('[class*="CloseButton"]')
            if close_btn:
                close_btn.click()
                time.sleep(1)
        except:
            pass
        
        # Кликаем ESC чтобы закрыть любые попапы
        page.keyboard.press('Escape')
        time.sleep(1)
        
        # Скроллим
        page.evaluate('window.scrollBy(0, 500)')
        time.sleep(2)
        
        products = page.evaluate("""() => {
            const results = [];
            
            // Ищем все ссылки на товары
            document.querySelectorAll('a[href*="/product--"]').forEach(a => {
                const card = a.closest('article') || a.closest('[data-apiary-widget-name]') || a.parentElement?.parentElement;
                const title = a.querySelector('span')?.innerText || a.innerText?.trim();
                
                // Ищем цену рядом
                let price = '';
                if (card) {
                    const priceEl = card.querySelector('[data-auto="price-value"]') || card.querySelector('[data-auto="snippet-price-current"]');
                    price = priceEl?.innerText?.trim() || '';
                }
                
                if (title && title.length > 10 && title.length < 200) {
                    results.push({
                        title: title.slice(0, 100),
                        price: price,
                        url: a.href,
                        marketplace: 'yandex'
                    });
                }
            });
            
            const seen = new Set();
            return results.filter(p => {
                const key = p.url;
                if (seen.has(key)) return false;
                seen.add(key);
                return true;
            }).slice(0, 10);
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
            return results.filter(p => { if (seen.has(p.url)) return false; seen.add(p.url); return true; }).slice(0, 10);
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
            return results.filter(p => { const key = p.title.slice(0, 25); if (seen.has(key)) return false; seen.add(key); return true; }).slice(0, 10);
        }""")
        return products
    except Exception as e:
        print(f'  Error: {e}')
        return []
    finally:
        context.close()

# MAIN
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    
    query = 'iphone 16'
    all_products = []
    
    wb = scrape_wildberries(browser, query)
    print(f'  Found: {len(wb)} products')
    all_products.extend(wb)
    
    ym = scrape_yandex_market(browser, query)
    print(f'  Found: {len(ym)} products')
    all_products.extend(ym)
    
    ali = scrape_aliexpress(browser, query)
    print(f'  Found: {len(ali)} products')
    all_products.extend(ali)
    
    ozon = scrape_ozon(browser, query)
    print(f'  Found: {len(ozon)} products')
    all_products.extend(ozon)
    
    browser.close()
    
    print(f'\n{"="*60}')
    print(f'TOTAL: {len(all_products)} products')
    print(f'{"="*60}')
    
    for mp in ['wildberries', 'yandex', 'aliexpress', 'ozon']:
        items = [p for p in all_products if p['marketplace'] == mp]
        print(f'\n[{mp.upper()}] - {len(items)} products:')
        for prod in items[:3]:
            title = prod['title'][:50] if prod['title'] else 'N/A'
            print(f"  {title} - {prod['price']}")
    
    with open('all_products.json', 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)
    print(f'\nSaved to all_products.json')
