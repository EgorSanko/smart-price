import httpx
import json

# WB Search API  публичный!
url = "https://search.wb.ru/exactmatch/ru/common/v4/search"
params = {
    "query": "iphone 16",
    "resultset": "catalog",
    "limit": 10,
    "sort": "popular",
    "appType": 1,
    "curr": "rub",
    "dest": -1257786
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json"
}

print("=== WB Search API ===")
r = httpx.get(url, params=params, headers=headers, timeout=10)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    products = data.get("data", {}).get("products", [])
    print(f"Found: {len(products)} products\n")
    
    for p in products[:5]:
        price = p.get("salePriceU", 0) // 100  # Цена в копейках
        name = p.get("name", "")
        brand = p.get("brand", "")
        product_id = p.get("id")
        print(f"  {price:>7,} ₽  {brand} {name[:40]}")
        print(f"           https://www.wildberries.ru/catalog/{product_id}/detail.aspx")
else:
    print(f"Error: {r.text[:200]}")
