import re

# --- DNS ---
print("=== DNS ===")
with open("dns_live.html", "r", encoding="utf-8") as f:
    html = f.read()
print(f"Len: {len(html)}")

# check for captcha
if "captcha" in html.lower() or "check-page" in html.lower():
    print("CAPTCHA detected!")

# find product-like patterns
for pat_name, pat in [
    ("catalog-product__name", r'catalog-product__name'),
    ("product-buy__price", r'product-buy__price'),
    ("data-id=product", r'data-id="product"'),
    ("product-card", r'product-card'),
    ("price_value", r'price[_-]value'),
    ("rub sign", r'\d+\s*₽'),
]:
    found = re.findall(pat, html)
    print(f"  {pat_name}: {len(found)} matches")

# show a chunk around first price
price_pos = html.find("₽")
if price_pos > 0:
    print(f"\nFirst price context:")
    print(html[max(0,price_pos-300):price_pos+50])
else:
    print("\nNo ₽ found. Checking for 'руб'...")
    rub_pos = html.find("руб")
    if rub_pos > 0:
        print(html[max(0,rub_pos-300):rub_pos+50])
    else:
        print("No prices at all. Showing chunk:")
        mid = len(html) // 3
        print(html[mid:mid+1000])
