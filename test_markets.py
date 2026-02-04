import httpx
import time

client = httpx.Client(timeout=15, follow_redirects=True)
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

print("=== Testing APIs ===\n")

# 1. Яндекс Маркет
print("1. Yandex Market...")
try:
    r = client.get("https://market.yandex.ru/search?text=iphone", headers=headers)
    print(f"   Status: {r.status_code}, Has products: {'product' in r.text.lower()}")
except Exception as e:
    print(f"   Error: {e}")

time.sleep(2)

# 2. AliExpress
print("\n2. AliExpress...")
try:
    r = client.get("https://aliexpress.ru/wholesale?SearchText=iphone", headers=headers)
    print(f"   Status: {r.status_code}, Length: {len(r.text)}")
except Exception as e:
    print(f"   Error: {e}")

time.sleep(2)

# 3. СберМегаМаркет  
print("\n3. SberMegaMarket...")
try:
    r = client.get("https://sbermegamarket.ru/catalog/?q=iphone", headers=headers)
    print(f"   Status: {r.status_code}, Length: {len(r.text)}")
except Exception as e:
    print(f"   Error: {e}")

client.close()
