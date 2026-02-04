import re

with open("citilink_live.html", "r", encoding="utf-8") as f:
    html = f.read()

# What price formats exist?
print("=== PRICE FORMATS ===")
for pat_name, pat in [
    ("₽", r'\d[\d\s]+₽'),
    ("руб", r'\d[\d\s]+\s*руб'),
    ("price__value", r'price__value[^>]*>(.*?)<'),
    ("data-price", r'data-price="(\d+)"'),
    ("Price", r'Price[^>]*>([^<]{1,30})<'),
    ("price_value", r'price.value[^>]*>([^<]{1,20})<'),
    ("Snippet__price", r'Snippet[^"]*price[^"]*"[^>]*>(.*?)<'),
    ("ProductCardVertical__price", r'ProductCard[^"]*price[^"]*"[^>]*>(.*?)<'),
]:
    found = re.findall(pat, html, re.IGNORECASE)
    print(f"  {pat_name}: {len(found)}")
    for x in found[:3]:
        clean = re.sub(r'<[^>]+>', '', str(x)).strip()
        if clean:
            print(f"    -> {clean[:80]}")

# Find area around "iPhone 17 Pro Max 256"
idx = html.find("iPhone 17 Pro Max 256")
if idx > 0:
    chunk = html[idx-100:idx+500]
    # remove tags for readability
    clean = re.sub(r'<[^>]+>', ' | ', chunk)
    clean = re.sub(r'\s+', ' ', clean)
    print(f"\n=== CONTEXT AROUND PRODUCT ===")
    print(clean[:400])

# Check for price with spaces like "89 999"
print("\n=== NUMBERS 4-6 DIGITS ===")
nums = re.findall(r'(?<!\d)(\d{2}\s\d{3})(?!\d)', html)
print(f"Found: {len(nums)}, first 5: {nums[:5]}")

# Or without spaces
nums2 = re.findall(r'(?<!\d)(\d{5,6})(?!\d)', html)
print(f"5-6 digit nums: {len(nums2)}, first 10: {nums2[:10]}")
