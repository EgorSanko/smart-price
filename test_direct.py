import httpx, re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}

# --- DNS ---
print("=== DNS ===")
try:
    r = httpx.get("https://www.dns-shop.ru/search/?q=iPhone+16+256GB", headers=headers, follow_redirects=True, timeout=15)
    print(f"Status: {r.status_code}, Len: {len(r.text)}")
    with open("dns_debug.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    # check for prices
    prices = re.findall(r'(\d[\d\s]{2,8})\s*[₽]', r.text)
    print(f"Prices found: {prices[:5]}")
    if "captcha" in r.text.lower() or "robot" in r.text.lower():
        print("WARNING: captcha detected!")
except Exception as e:
    print(f"Error: {e}")

# --- Citilink ---
print("\n=== CITILINK ===")
try:
    r = httpx.get("https://www.citilink.ru/search/?text=iPhone+16+256GB", headers=headers, follow_redirects=True, timeout=15)
    print(f"Status: {r.status_code}, Len: {len(r.text)}")
    with open("citilink_debug.html", "w", encoding="utf-8") as f:
        f.write(r.text)
    prices = re.findall(r'(\d[\d\s]{2,8})\s*[₽]', r.text)
    print(f"Prices found: {prices[:5]}")
    if "captcha" in r.text.lower() or "robot" in r.text.lower():
        print("WARNING: captcha detected!")
except Exception as e:
    print(f"Error: {e}")

# --- MVideo ---
print("\n=== MVIDEO ===")
try:
    r = httpx.get("https://www.mvideo.ru/bff/search/suggest?query=iPhone+16+256GB", headers=headers, follow_redirects=True, timeout=15)
    print(f"Status: {r.status_code}, Len: {len(r.text)}")
    print(f"Body: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
