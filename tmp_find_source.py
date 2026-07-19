import re, glob, json
# Frames have escaped JSON nested inside "json_data":"..." → strings can be single or double-escaped
# Strategy: unescape payload progressively and search


def unescape(s):
    try:
        return s.encode().decode("unicode_escape")
    except Exception:
        return s


for fp in sorted(glob.glob("/tmp/ws_dump/frame_*.json"))[:40]:
    raw = open(fp, encoding="utf-8", errors="ignore").read()
    # Unescape twice in case of nested escaping
    variants = [raw, unescape(raw), unescape(unescape(raw))]
    for level, d in enumerate(variants):
        # generic: any price-like number near Galaxy / Samsung / Смартфон
        for m in re.finditer(
            r'(?:Galaxy S25 Ultra|Смартфон Samsung[^"\\]{0,80})[^"\\]{0,80}', d
        ):
            s = m.group(0)
            if re.search(r"\d{4,6}", s):
                print(fp.split("/")[-1], "L", level, s[:200])
                break
        # JSON keys that typically hold source price
        for key in (
            "originalPrice",
            "marketPrice",
            "sourcePrice",
            "from_price",
            "price_from",
        ):
            for m in re.finditer(key + r'"?\s*[:=]\s*"?(\d[\d ,.]*)', d):
                print(fp.split("/")[-1], "key", key, m.group(1)[:40])
