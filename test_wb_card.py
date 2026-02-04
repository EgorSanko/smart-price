import httpx

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "*/*",
    "Origin": "https://www.wildberries.ru",
    "Referer": "https://www.wildberries.ru/"
}

# ID товаров которые мы нашли через Playwright
product_ids = [516913042, 660037832, 482257004, 482257006]

print("=== WB Card API v2 ===")
# Несколько товаров в одном запросе
ids_str = ";".join(map(str, product_ids))
url = f"https://card.wb.ru/cards/v2/detail?appType=1&curr=rub&dest=-1257786&nm={ids_str}"

print(f"URL: {url[:80]}...")
r = httpx.get(url, headers=headers, timeout=10)
print(f"Status: {r.status_code}")

if r.status_code == 200:
    data = r.json()
    products = data.get("data", {}).get("products", [])
    print(f"Found: {len(products)} products\n")
    for p in products:
        price = p.get("sizes", [{}])[0].get("price", {}).get("total", 0) // 100
        if not price:
            price = p.get("salePriceU", 0) // 100
        print(f"  {price:>7,} ₽  {p.get('brand', '')} {p.get('name', '')[:35]}")
else:
    print(f"Response: {r.text[:300]}")

# Альтернативный endpoint
print("\n=== WB Cards Detail v1 ===")
url2 = f"https://card.wb.ru/cards/detail?appType=1&curr=rub&dest=-1257786&nm={ids_str}"
r2 = httpx.get(url2, headers=headers, timeout=10)
print(f"Status: {r2.status_code}")
if r2.status_code == 200:
    data = r2.json()
    products = data.get("data", {}).get("products", [])
    print(f"Found: {len(products)}")
