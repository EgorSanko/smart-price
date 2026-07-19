import sys, os, glob

sys.path.insert(0, r"C:/Users/egor3/Desktop/smart-price/backend")
from app.workers.alisa import _extract_from_payload, AlisaResult

r = AlisaResult()
DUMP = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ws_dump"
for f in sorted(glob.glob(os.path.join(DUMP, "frame_*.json"))):
    s = open(f, encoding="utf-8", errors="ignore").read()
    _extract_from_payload(s, r)
print("planned", len(r.planned_shops))
print("offers", len(r.offers))
for d, o in sorted(r.offers.items(), key=lambda kv: kv[1].price):
    print(
        f'  {o.price:>8.0f}  {d:<24s}  adv={o.is_adv}  name={(o.product_name or "")[:60]}'
    )
