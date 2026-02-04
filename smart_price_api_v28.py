import httpx, re, json, time, threading, queue
from flask import Flask, request, Response, jsonify
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
CACHE = {}
CACHE_TTL = 300

_browser_queue = queue.Queue()
_browser_results = {}

def _browser_worker():
    from playwright.sync_api import sync_playwright
    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=False,
        args=["--window-position=-32000,-32000", "--disable-blink-features=AutomationControlled", "--no-sandbox"]
    )
    print("Browser worker started")
    while True:
        task = _browser_queue.get()
        if task is None:
            break
        task_id, fn, args = task
        try:
            result = fn(browser, *args)
            _browser_results[task_id] = ("ok", result)
        except Exception as e:
            print(f"Browser task error: {e}")
            _browser_results[task_id] = ("error", str(e))
        _browser_queue.task_done()

def start_browser_thread():
    t = threading.Thread(target=_browser_worker, daemon=True)
    t.start()

def run_in_browser(fn, *args, timeout=45):
    task_id = f"{time.time()}_{id(fn)}"
    _browser_results.pop(task_id, None)
    _browser_queue.put((task_id, fn, args))
    deadline = time.time() + timeout
    while time.time() < deadline:
        if task_id in _browser_results:
            status, data = _browser_results.pop(task_id)
            if status == "ok":
                return data
            raise Exception(data)
        time.sleep(0.1)
    raise TimeoutError("Browser task timeout")

EXCLUDE_KW = ["чехол","кейс","стекло","пленка","плёнка","кабель","зарядк",
              "ремешок","адаптер","подставк","наушник","колонк","держатель",
              "брелок","strap","case","cover"]

def is_accessory(title):
    t = title.lower()
    return any(kw in t for kw in EXCLUDE_KW)

NORM_MAP = {
    "айфон": "iPhone", "самсунг": "Samsung", "галакси": "Galaxy",
    "посо": "Poco", "поко": "Poco", "сяоми": "Xiaomi", "редми": "Redmi",
    "хуавей": "Huawei", "хонор": "Honor", "реалми": "Realme",
    "ноутбук": "ноутбук", "гб": "GB", "тб": "TB", "про": "Pro",
    "ультра": "Ultra", "плюс": "Plus", "макс": "Max", "мини": "Mini",
}

def normalize_query(q):
    words = q.lower().split()
    return " ".join(NORM_MAP.get(w, w) for w in words)

def price_num(s):
    if not s:
        return 0
    d = re.sub(r"[^\d]", "", str(s))
    return int(d) if d else 0

def cache_get(key):
    if key in CACHE:
        val, ts = CACHE[key]
        if time.time() - ts < CACHE_TTL:
            return val
    return None

def cache_set(key, val):
    CACHE[key] = (val, time.time())

# ========== YANDEX (httpx) ==========

def scrape_yandex(query):
    cached = cache_get(f"ya:{query}")
    if cached is not None:
        return cached
    results = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "ru-RU,ru;q=0.9",
        }
        url = f"https://market.yandex.ru/search?text={quote_plus(query)}"
        r = httpx.get(url, headers=headers, follow_redirects=True, timeout=15)
        if r.status_code == 200:
            titles = re.findall(r'"title"\s*:\s*"([^"]{5,120})"', r.text)
            prices = re.findall(r'"price"\s*:\s*\{\s*"value"\s*:\s*"(\d+)"', r.text)
            links = re.findall(r'"link"\s*:\s*"(/product--[^"]+)"', r.text)
            for i in range(min(len(titles), len(prices))):
                t = titles[i]
                if is_accessory(t):
                    continue
                p = prices[i] if i < len(prices) else "0"
                link = "https://market.yandex.ru" + links[i] if i < len(links) else ""
                results.append({
                    "title": t,
                    "price": f"{int(p):,}".replace(",", " ") + " \u20bd" if p != "0" else "",
                    "price_num": int(p), "url": link,
                    "marketplace": "yandex", "image": ""
                })
    except Exception as e:
        print(f"Yandex error: {e}")
    cache_set(f"ya:{query}", results)
    return results

# ========== CITILINK (Playwright) ==========

def _citilink_browser(browser, query):
    results = []
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080}
    )
    page = ctx.new_page()
    page.route("**/*.{png,jpg,jpeg,gif,webp,svg,ico,woff,woff2}", lambda r: r.abort())
    try:
        page.goto(f"https://www.citilink.ru/search/?text={quote_plus(query)}", timeout=25000)
        time.sleep(3)
        try:
            page.wait_for_selector('a[href*="/product/"]', timeout=10000)
        except:
            time.sleep(3)
        html = page.content()
    finally:
        page.close()
        ctx.close()

    raw = re.findall(r'href="(/product/[^"]+)"[^>]*title="([^"]+)"', html)
    seen = set()
    product_list = []
    for href, title in raw:
        if "/otzyvy/" in href or "/aksessuary/" in href:
            continue
        if href in seen:
            continue
        seen.add(href)
        title = title.replace("&quot;", '"').replace("&amp;", "&").replace("&#39;", "'")
        product_list.append({"href": href, "title": title})

    price_list = re.findall(r'Price[^>]*>\s*(\d[\d\s]+\d)\s*<', html)

    for i, prod in enumerate(product_list[:15]):
        t = prod["title"]
        if is_accessory(t):
            continue
        pn = price_num(price_list[i]) if i < len(price_list) else 0
        results.append({
            "title": t,
            "price": f"{pn:,}".replace(",", " ") + " \u20bd" if pn else "",
            "price_num": pn,
            "url": f"https://www.citilink.ru{prod['href']}",
            "marketplace": "citilink", "image": ""
        })
    print(f"citilink parsed: {len(results)}")
    return results

def scrape_citilink(query):
    cached = cache_get(f"cl:{query}")
    if cached is not None:
        return cached
    results = run_in_browser(_citilink_browser, query)
    cache_set(f"cl:{query}", results)
    return results

# ========== PARSERS ==========

PARSERS = {
    "yandex":   {"name": "\u042f\u043d\u0434\u0435\u043a\u0441 \u041c\u0430\u0440\u043a\u0435\u0442", "fn": scrape_yandex, "enabled": True, "color": "#ffcc00"},
    "citilink": {"name": "\u0421\u0438\u0442\u0438\u043b\u0438\u043d\u043a", "fn": scrape_citilink, "enabled": True, "color": "#00a046"},
}

# ========== FLASK ==========

@app.route("/api/parsers")
def api_parsers():
    out = {}
    for k, v in PARSERS.items():
        out[k] = {"name": v["name"], "enabled": v["enabled"], "color": v["color"]}
    return jsonify(out)

@app.route("/api/search/stream")
def api_search_stream():
    q_raw = request.args.get("q", "").strip()
    if not q_raw:
        return Response('data: {"error":"empty query"}\n\n', content_type="text/event-stream")
    q = normalize_query(q_raw)
    enabled = {k: v for k, v in PARSERS.items() if v["enabled"]}

    def generate():
        yield f'data: {json.dumps({"status": "start", "query": q, "original": q_raw, "sources": list(enabled.keys())})}\n\n'
        all_results = []
        pool = ThreadPoolExecutor(max_workers=3)
        futures = {}
        for key, par in enabled.items():
            yield f'data: {json.dumps({"status": "parsing", "source": key, "name": par["name"]})}\n\n'
            futures[pool.submit(par["fn"], q)] = key
        for future in futures:
            key = futures[future]
            try:
                items = future.result(timeout=50)
                all_results.extend(items)
                yield f'data: {json.dumps({"status": "done", "source": key, "count": len(items)})}\n\n'
                print(f"{key}: {len(items)}")
            except Exception as e:
                print(f"{key} error: {e}")
                yield f'data: {json.dumps({"status": "error", "source": key, "error": str(e)[:100]})}\n\n'
        pool.shutdown(wait=False)
        all_results = [r for r in all_results if r["price_num"] > 0]
        all_results.sort(key=lambda x: x["price_num"])
        yield f'data: {json.dumps({"status": "complete", "results": all_results, "total": len(all_results)})}\n\n'
    return Response(generate(), content_type="text/event-stream")

@app.route("/api/search")
def api_search():
    q_raw = request.args.get("q", "").strip()
    if not q_raw:
        return jsonify({"error": "empty query"})
    q = normalize_query(q_raw)
    all_results = []
    for k, v in PARSERS.items():
        if v["enabled"]:
            try:
                all_results.extend(v["fn"](q))
            except Exception as e:
                print(f"{k} error: {e}")
    all_results = [r for r in all_results if r["price_num"] > 0]
    all_results.sort(key=lambda x: x["price_num"])
    return jsonify({"query": q, "results": all_results, "total": len(all_results)})

@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "cache_size": len(CACHE),
                    "parsers": sum(1 for v in PARSERS.values() if v["enabled"])})

if __name__ == "__main__":
    print("Smart Price API v28 - Yandex + Citilink")
    print("Starting browser worker...")
    start_browser_thread()
    time.sleep(2)
    print("http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=False)
