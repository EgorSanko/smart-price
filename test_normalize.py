from playwright.sync_api import sync_playwright
import urllib.parse
import time
import re

# Простая нормализация
NORMALIZE_MAP = {
    "айфон": "iphone",
    "айпад": "ipad", 
    "макбук": "macbook",
    "эпл": "apple",
    "самсунг": "samsung",
    "ксяоми": "xiaomi",
    "сяоми": "xiaomi",
    "хуавей": "huawei",
    "хонор": "honor",
    "редми": "redmi",
    "реалми": "realme",
    "вайлдберриз": "",
    "озон": "",
}

def normalize_query(query: str) -> str:
    """Нормализует запрос для лучшего поиска."""
    q = query.lower().strip()
    for ru, en in NORMALIZE_MAP.items():
        q = q.replace(ru, en)
    # Убираем лишние пробелы
    q = re.sub(r'\s+', ' ', q).strip()
    return q

# Тест
queries = [
    "айфон 16 128",
    "АЙФОН про макс",
    "ксяоми редми ноут 13",
]

print("=== Normalization Test ===\n")
for q in queries:
    normalized = normalize_query(q)
    print(f'"{q}" -> "{normalized}"')

print("\n=== Live Search Test ===\n")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    page = browser.new_page()
    
    for query in queries:
        normalized = normalize_query(query)
        url = f'https://www.wildberries.ru/catalog/0/search.aspx?search={urllib.parse.quote(normalized)}'
        print(f'Query: "{query}" -> "{normalized}"')
        page.goto(url)
        time.sleep(4)
        
        count = page.query_selector_all('[data-nm-id]')
        first = page.query_selector('[data-nm-id] .product-card__name')
        first_name = first.inner_text().strip() if first else 'N/A'
        
        print(f'  Results: {len(count)}, First: {first_name[:40]}')
        print()
    
    browser.close()
