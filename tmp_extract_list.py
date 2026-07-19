import json, re, sys

p = r"C:/Users/egor3/AppData/Local/Temp/frame_82.json"
s = open(p, encoding="utf-8").read()

i = s.find("tcard-1d33f88c")
j = s.find('"json_data":"', i)
k = j + len('"json_data":"')
buf = []
esc = False
end = None
idx = k
BACKSLASH = chr(92)
QUOTE = '"'
while idx < len(s):
    c = s[idx]
    if esc:
        buf.append(c)
        esc = False
    elif c == BACKSLASH:
        buf.append(c)
        esc = True
    elif c == QUOTE:
        end = idx
        break
    else:
        buf.append(c)
    idx += 1
raw = "".join(buf)
decoded = json.loads('"' + raw + '"')
print("DECODED LEN", len(decoded))
print(decoded[:500])
print("...")
print(decoded[-1000:])
try:
    obj = json.loads(decoded)
    print("TYPE", type(obj).__name__)
    if isinstance(obj, dict):
        print("keys", list(obj.keys()))
        for k2, v in obj.items():
            if isinstance(v, list):
                print(f"  {k2}: list len={len(v)}")
                if v:
                    print(
                        "    first item keys:",
                        list(v[0].keys()) if isinstance(v[0], dict) else type(v[0]),
                    )
                    print("    first item:", json.dumps(v[0], ensure_ascii=False)[:500])
            elif isinstance(v, dict):
                print(f"  {k2}: dict keys={list(v.keys())}")
            else:
                print(f"  {k2}: {repr(v)[:200]}")
    elif isinstance(obj, list):
        print("list len", len(obj))
        for it in obj[:3]:
            print(json.dumps(it, ensure_ascii=False)[:500])
except Exception as e:
    print("parse err", e)
