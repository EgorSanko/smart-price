from playwright.sync_api import sync_playwright
import time

def scrape_yandex_market(browser, query):
    print(f'\n=== Yandex Market: {query} ===')
    context = browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    page = context.new_page()
    try:
        page.goto(f'https://market.yandex.ru/search?text={query}')
        time.sleep(3)
        
        # 1. Закрываем cookie popup
        try:
            cookie_btn = page.query_selector('button:has-text("Allow all")')
            if cookie_btn:
                cookie_btn.click()
                print('  Closed cookie popup')
                time.sleep(1)
        except:
            pass
        
        # 2. Закрываем модалку входа - кликаем вне её
        try:
            # Клик по оверлею или Escape
            page.keyboard.press('Escape')
            time.sleep(0.5)
            page.keyboard.press('Escape')
            time.sleep(1)
        except:
            pass
        
        # Скроллим
        page.evaluate('window.scrollBy(0, 300)')
        time.sleep(2)
        
        products = page.evaluate("""() => {
            const results = [];
            
            // Ищем карточки товаров
            document.querySelectorAll('[data-apiary-widget-name="@marketfront/SerpEntity"]').forEach(card => {
                const linkEl = card.querySelector('a[href*="/product"]');
                const titleEl = card.querySelector('[data-auto="snippet-title"]') || card.querySelector('h3 span');
                const priceEl = card.querySelector('[data-auto="price-value"]') || card.querySelector('[data-auto="snippet-price-current"]');
                
                if (linkEl) {
                    results.push({
                        title: titleEl?.innerText?.trim() || '',
                        price: priceEl?.innerText?.trim() || '',
                        url: linkEl.href,
                        marketplace: 'yandex'
                    });
                }
            });
            
            // Fallback - по ссылкам
            if (results.length === 0) {
                document.querySelectorAll('a[href*="/product--"]').forEach(a => {
                    const parent = a.closest('article') || a.closest('div[data-zone-name]') || a.parentElement;
                    const title = a.innerText?.trim();
                    const priceEl = parent?.querySelector('[data-auto="price-value"]');
                    
                    if (title && title.length > 10 && title.length < 150) {
                        results.push({
                            title: title,
                            price: priceEl?.innerText?.trim() || '',
                            url: a.href,
                            marketplace: 'yandex'
                        });
                    }
                });
            }
            
            const seen = new Set();
            return results.filter(p => {
                if (seen.has(p.url)) return false;
                seen.add(p.url);
                return true;
            }).slice(0, 10);
        }""")
        
        return products
    except Exception as e:
        print(f'  Error: {e}')
        return []
    finally:
        context.close()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    
    products = scrape_yandex_market(browser, 'iphone 16')
    print(f'  Found: {len(products)} products')
    
    for prod in products[:5]:
        print(f"  {prod['title'][:50]} - {prod['price']}")
    
    browser.close()
