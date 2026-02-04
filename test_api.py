import httpx
import time

# === Яндекс Маркет API ===
print('=== Yandex Market API ===')
url = 'https://market.yandex.ru/api/search'
params = {
    'text': 'iphone 16 128gb',
    'page': 1
}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json'
}

try:
    r = httpx.get(url, params=params, headers=headers, timeout=10)
    print(f'Status: {r.status_code}')
    print(f'Content-Type: {r.headers.get("content-type")}')
    print(f'Response: {r.text[:500]}')
except Exception as e:
    print(f'Error: {e}')

time.sleep(2)

# === AliExpress API ===
print('\n=== AliExpress API ===')
url = 'https://aliexpress.ru/aer-api/v1/search'
params = {
    'searchText': 'iphone 16',
    'page': 1
}

try:
    r = httpx.get(url, params=params, headers=headers, timeout=10)
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text[:500]}')
except Exception as e:
    print(f'Error: {e}')

# === AliExpress альтернативный ===
print('\n=== AliExpress glosearch ===')
url = 'https://aliexpress.ru/aer-jsonapi/v1/bx/glosearch/search'
data = {
    'searchText': 'iphone 16',
    'page': 1
}

try:
    r = httpx.post(url, json=data, headers=headers, timeout=10)
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text[:500]}')
except Exception as e:
    print(f'Error: {e}')
