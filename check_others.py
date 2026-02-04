import re

for name, path in [("CITILINK", "citilink_live.html"), ("MVIDEO", "mvideo_live.html")]:
    print(f"\n=== {name} ===")
    try:
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        print(f"Len: {len(html)}")
        if "403" in html[:2000] or "captcha" in html.lower()[:3000]:
            print("BLOCKED or CAPTCHA!")
            print(html[:500])
            continue
        prices = re.findall(r'\d[\d\s]+₽', html)
        print(f"Prices (₽): {len(prices)}, first 3: {prices[:3]}")
        titles_a = re.findall(r'<a[^>]*>(.*?iPhone.*?)</a>', html, re.DOTALL)
        print(f"Title links with iPhone: {len(titles_a)}")
        for t in titles_a[:3]:
            clean = re.sub(r'<[^>]+>', '', t).strip()
            if len(clean) > 5:
                print(f"  - {clean[:100]}")
    except FileNotFoundError:
        print(f"File not found (timed out before saving)")
