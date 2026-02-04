import httpx, json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

# --- DNS suggest API ---
print("=== DNS SUGGEST API ===")
try:
    r = httpx.get(
        "https://search.dns-shop.ru/search/v1/suggest",
        params={"q": "iPhone 16 256GB"},
        headers=headers,
        follow_redirects=True,
        timeout=15
    )
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:800]}")
except Exception as e:
    print(f"Error: {e}")

# --- DNS catalog API ---
print("\n=== DNS REST API ===")
try:
    r = httpx.get(
        "https://restapi.dns-shop.ru/v1/search",
        params={"q": "iPhone 16 256GB"},
        headers=headers,
        follow_redirects=True,
        timeout=15
    )
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:800]}")
except Exception as e:
    print(f"Error: {e}")

# --- MVideo BFF search ---
print("\n=== MVIDEO BFF SEARCH ===")
try:
    r = httpx.get(
        "https://www.mvideo.ru/bff/search/product",
        params={"query": "iPhone 16 256GB", "pageSize": "10"},
        headers={**headers, "Referer": "https://www.mvideo.ru/"},
        follow_redirects=True,
        timeout=15
    )
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:800]}")
except Exception as e:
    print(f"Error: {e}")

# --- Citilink API ---
print("\n=== CITILINK API ===")
try:
    r = httpx.get(
        "https://www.citilink.ru/api/v1/search",
        params={"text": "iPhone 16 256GB"},
        headers={**headers, "Referer": "https://www.citilink.ru/", "X-Requested-With": "XMLHttpRequest"},
        follow_redirects=True,
        timeout=15
    )
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:800]}")
except Exception as e:
    print(f"Error: {e}")

# --- MVideo suggest ---
print("\n=== MVIDEO SUGGEST ===")
try:
    r = httpx.get(
        "https://www.mvideo.ru/bff/search/suggest",
        params={"query": "iPhone 16"},
        headers={**headers, "Referer": "https://www.mvideo.ru/"},
        follow_redirects=True,
        timeout=15
    )
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:800]}")
except Exception as e:
    print(f"Error: {e}")
