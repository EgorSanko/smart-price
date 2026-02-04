import re

# Check if WB saved html
try:
    with open("wb_live.html", "r", encoding="utf-8") as f:
        html = f.read()
    print(f"WB len: {len(html)}")
    if "antibot" in html or "challenges" in html:
        print("WB: ANTIBOT page!")
    elif "data-nm-id" in html:
        cards = re.findall(r'data-nm-id="(\d+)"', html)
        print(f"WB: {len(cards)} product cards found")
    else:
        print("WB: Unknown page")
        print(html[:500])
except FileNotFoundError:
    print("WB: no saved HTML (not saving in current code)")
    print("Adding debug save to WB parser needed")
