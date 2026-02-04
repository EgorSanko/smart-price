from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    page = browser.new_page()
    
    page.goto('https://market.yandex.ru/search?text=iphone%2016')
    time.sleep(4)
    
    # Закрываем попапы
    page.keyboard.press('Escape')
    time.sleep(1)
    page.keyboard.press('Escape')
    time.sleep(1)
    
    # Кликаем Allow all cookies если есть
    try:
        page.click('button:has-text("Allow all")', timeout=2000)
    except:
        pass
    
    time.sleep(2)
    
    # Детальная информация
    info = page.evaluate("""() => {
        const data = {
            url: window.location.href,
            title: document.title,
            selectors: {}
        };
        
        // Проверяем разные селекторы
        data.selectors['article'] = document.querySelectorAll('article').length;
        data.selectors['[data-apiary-widget-name]'] = document.querySelectorAll('[data-apiary-widget-name]').length;
        data.selectors['a[href*="/product"]'] = document.querySelectorAll('a[href*="/product"]').length;
        data.selectors['[data-auto="snippet-title"]'] = document.querySelectorAll('[data-auto="snippet-title"]').length;
        data.selectors['[data-zone-name="snippetList"]'] = document.querySelectorAll('[data-zone-name="snippetList"]').length;
        data.selectors['[data-baobab-name="title"]'] = document.querySelectorAll('[data-baobab-name="title"]').length;
        
        // Первые 3 ссылки на продукты
        const links = Array.from(document.querySelectorAll('a[href*="/product"]')).slice(0, 3);
        data.sample_links = links.map(a => ({
            href: a.href.slice(0, 80),
            text: a.innerText?.slice(0, 50)
        }));
        
        return data;
    }""")
    
    print(f"URL: {info['url'][:80]}")
    print(f"Title: {info['title']}")
    print(f"\nSelectors found:")
    for sel, count in info['selectors'].items():
        print(f"  {sel}: {count}")
    
    print(f"\nSample links:")
    for link in info.get('sample_links', []):
        print(f"  {link['text']} -> {link['href']}")
    
    input('\nPress Enter to close...')
    browser.close()
