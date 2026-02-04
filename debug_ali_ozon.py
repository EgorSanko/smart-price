from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    
    # === OZON ===
    print('\n=== OZON DEBUG ===')
    page = browser.new_page()
    page.goto('https://www.ozon.ru/search/?text=iphone%2016')
    time.sleep(6)
    
    info = page.evaluate("""() => {
        return {
            links: document.querySelectorAll('a[href*="/product/"]').length,
            widgets: document.querySelectorAll('[data-widget]').length,
            spans: document.querySelectorAll('span').length,
            divs_with_price: Array.from(document.querySelectorAll('*')).filter(el => el.innerText?.includes('')).length,
        };
    }""")
    print(f"Links /product/: {info['links']}")
    print(f"Widgets: {info['widgets']}")
    print(f"Elements with : {info['divs_with_price']}")
    
    # Берём первую карточку
    sample = page.evaluate("""() => {
        const link = document.querySelector('a[href*="/product/"]');
        if (!link) return null;
        const card = link.closest('div');
        return {
            href: link.href?.slice(0, 80),
            linkText: link.innerText?.slice(0, 100),
            cardText: card?.innerText?.slice(0, 300)
        };
    }""")
    if sample:
        print(f"\nSample card:")
        print(f"  URL: {sample['href']}")
        print(f"  Text: {sample['cardText'][:200]}")
    
    page.close()
    time.sleep(2)
    
    # === ALIEXPRESS ===
    print('\n=== ALIEXPRESS DEBUG ===')
    page = browser.new_page()
    page.goto('https://aliexpress.ru/wholesale?SearchText=iphone%2016')
    time.sleep(5)
    
    info = page.evaluate("""() => {
        return {
            links_item: document.querySelectorAll('a[href*="/item/"]').length,
            links_product: document.querySelectorAll('a[href*="product"]').length,
            price_elements: document.querySelectorAll('[class*="price"]').length,
        };
    }""")
    print(f"Links /item/: {info['links_item']}")
    print(f"Links product: {info['links_product']}")
    print(f"Price elements: {info['price_elements']}")
    
    sample = page.evaluate("""() => {
        const link = document.querySelector('a[href*="/item/"]');
        if (!link) return null;
        const card = link.closest('div')?.closest('div');
        return {
            href: link.href?.slice(0, 80),
            linkText: link.innerText?.slice(0, 100),
            cardText: card?.innerText?.slice(0, 300)
        };
    }""")
    if sample:
        print(f"\nSample card:")
        print(f"  URL: {sample['href']}")
        print(f"  Text: {sample['cardText'][:200]}")
    
    browser.close()
