from playwright.sync_api import sync_playwright
import urllib.parse
import time

with sync_playwright() as p:
    # Аргументы против детекции headless
    browser = p.chromium.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
        ]
    )
    
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        locale='ru-RU',
    )
    
    page = context.new_page()
    
    # Скрываем webdriver
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = {runtime: {}};
    """)
    
    print('Testing headless WB...')
    page.goto('https://www.wildberries.ru/catalog/0/search.aspx?search=iphone%2016')
    time.sleep(5)
    
    title = page.title()
    print(f'Title: {title}')
    
    cards = page.query_selector_all('[data-nm-id]')
    print(f'Products: {len(cards)}')
    
    if cards:
        first = page.query_selector('[data-nm-id] .product-card__name')
        if first:
            print(f'First: {first.inner_text()[:50]}')
    
    browser.close()
