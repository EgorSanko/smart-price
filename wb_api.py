from playwright.sync_api import sync_playwright
from flask import Flask, request, jsonify
import urllib.parse
import time

app = Flask(__name__)

@app.route('/scrape/wb', methods=['GET'])
def scrape_wb():
    query = request.args.get('query', 'iphone')
    limit = int(request.args.get('limit', 20))
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        page = browser.new_page()
        
        url = f'https://www.wildberries.ru/catalog/0/search.aspx?search={urllib.parse.quote(query)}'
        page.goto(url)
        page.wait_for_selector('[data-nm-id]', timeout=15000)
        time.sleep(3)
        
        products = page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('[data-nm-id]').forEach(card => {
                const id = card.getAttribute('data-nm-id');
                const nameEl = card.querySelector('.product-card__name');
                const priceEl = card.querySelector('.price__lower-price');
                const img = card.querySelector('img');
                results.push({
                    external_id: id,
                    title: nameEl ? nameEl.innerText.trim() : '',
                    price: priceEl ? priceEl.innerText.trim() : '',
                    url: 'https://www.wildberries.ru/catalog/' + id + '/detail.aspx',
                    image_url: img ? img.src : ''
                });
            });
            return results;
        }""")
        
        browser.close()
    
    return jsonify(products[:limit])

if __name__ == '__main__':
    print('Starting WB Scraper API on http://localhost:5001')
    app.run(host='0.0.0.0', port=5001)
