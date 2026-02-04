from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    page = browser.new_page()
    
    print('Opening WB main page...')
    page.goto('https://www.wildberries.ru/')
    
    print('Waiting 10 sec for cookies...')
    time.sleep(10)
    
    print('Searching...')
    page.fill('input[id="searchInput"]', 'iphone')
    page.keyboard.press('Enter')
    time.sleep(7)
    
    title = page.title()
    print(f'Title: {title}')
    
    products = page.query_selector_all('[data-nm-id]')
    print(f'Found {len(products)} products')
    
    if products:
        for card in products[:3]:
            nm_id = card.get_attribute('data-nm-id')
            print(f'  ID: {nm_id}')
    
    input('Press Enter to close browser...')
    browser.close()
