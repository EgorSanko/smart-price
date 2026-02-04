import re

with open("citilink_live.html", "r", encoding="utf-8") as f:
    html = f.read()

# Titles from title="" attribute of product links
titles = re.findall(r'href="(/product/[^"]+)"[^>]*title="([^"]+)"', html)
print(f"=== PRODUCT LINKS WITH TITLES: {len(titles)} ===")
for href, title in titles[:10]:
    print(f"  {title[:80]}")
    print(f"    -> {href}")

# Prices from Price pattern
prices = re.findall(r'Price[^>]*>\s*(\d[\d\s]+\d)\s*<', html)
print(f"\n=== PRICES: {len(prices)} ===")
for p in prices[:10]:
    print(f"  {p}")

# Snippet prices
snip_prices = re.findall(r'Snippet[^"]*[Pp]rice[^"]*"[^>]*>\s*(\d[\d\s]+\d)\s*<', html)
print(f"\n=== SNIPPET PRICES: {len(snip_prices)} ===")
for p in snip_prices[:10]:
    print(f"  {p}")

# Full card pattern: find link+title close to price
print("\n=== TRYING CARD EXTRACTION ===")
# Find all product hrefs
all_hrefs = re.findall(r'href="(/product/[^"]+)"', html)
unique_hrefs = list(dict.fromkeys(all_hrefs))
print(f"Unique product links: {len(unique_hrefs)}")
for h in unique_hrefs[:5]:
    print(f"  {h}")
