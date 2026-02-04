import re

# Test new citilink parsing logic on saved HTML
with open("citilink_live.html", "r", encoding="utf-8") as f:
    html = f.read()

# Step 1: Get unique product links with titles
raw = re.findall(r'href="(/product/[^"]+)"[^>]*title="([^"]+)"', html)
seen = set()
products = []
for href, title in raw:
    if "/otzyvy/" in href:
        continue
    if href in seen:
        continue
    seen.add(href)
    title = title.replace("&quot;", '"').replace("&amp;", "&")
    products.append({"href": href, "title": title})

# Step 2: Get prices in order
prices = re.findall(r'Price[^>]*>\s*(\d[\d\s]+\d)\s*<', html)

print(f"Products: {len(products)}, Prices: {len(prices)}")
print()

for i, prod in enumerate(products[:15]):
    p = prices[i] if i < len(prices) else "?"
    pn = int(re.sub(r'\s', '', p)) if p != "?" else 0
    print(f"{i+1}. {prod['title'][:70]}")
    print(f"   Price: {p}  ({pn})")
    print(f"   URL: https://www.citilink.ru{prod['href']}")
    print()
