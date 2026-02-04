from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    page = browser.new_page()
    
    page.goto('https://market.yandex.ru/search?text=iphone%2016')
    time.sleep(5)
    
    # Закрываем всё что можно
    page.keyboard.press('Escape')
    time.sleep(1)
    
    # Скриншот
    page.screenshot(path='yandex_debug.png', full_page=True)
    print('Screenshot saved: yandex_debug.png')
    
    # Смотрим HTML
    html = page.content()
    with open('yandex_debug.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('HTML saved: yandex_debug.html')
    
    # Что есть на странице
    links = page.query_selector_all('a[href*="/product"]')
    print(f'Links with /product: {len(links)}')
    
    articles = page.query_selector_all('article')
    print(f'Articles: {len(articles)}')
    
    browser.close()
