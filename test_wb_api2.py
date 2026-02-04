import httpx
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Origin": "https://www.wildberries.ru",
    "Referer": "https://www.wildberries.ru/"
}

# 1. Статический endpoint (не блокируется)
print("=== WB Static Menu (always works) ===")
r = httpx.get("https://static-basket-01.wbbasket.ru/vol0/data/main-menu-ru-ru-v3.json", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print("OK - WB доступен\n")

# 2. Card API - данные о конкретном товаре
print("=== WB Card API ===")
# ID товара с WB (iPhone)
product_id = 482257006
url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&nm={product_id}"
r = httpx.get(url, headers=headers, timeout=10)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    products = data.get("data", {}).get("products", [])
    if products:
        p = products[0]
        print(f"Name: {p.get('name')}")
        print(f"Brand: {p.get('brand')}")
        print(f"Price: {p.get('salePriceU', 0) // 100:,} ₽")
        print(f"Rating: {p.get('rating')}")
else:
    print(f"Error: {r.text[:200]}")

# 3. Попробуем search с задержкой и другим dest
print("\n=== WB Search API (attempt 2) ===")
import time
time.sleep(2)

url = "https://search.wb.ru/exactmatch/ru/common/v4/search"
params = {
    "query": "iphone",
    "resultset": "catalog", 
    "limit": 5,
    "sort": "popular",
    "appType": 1,
    "curr": "rub",
    "dest": -1257786,
    "spp": 30
}
r = httpx.get(url, params=params, headers=headers, timeout=10)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    products = data.get("data", {}).get("products", [])
    print(f"Found: {len(products)} products")
    for p in products[:3]:
        print(f"  {p.get('salePriceU', 0) // 100:,} ₽ - {p.get('name', '')[:40]}")
