"""Shared product filtering and cleanup utilities.

These functions were extracted from search_stream.py so they can be reused
by the price analyzer and other services.
"""

import re


MODEL_PATTERNS = [
    re.compile(r"\b[SAM]\d{1,3}\b", re.IGNORECASE),
    re.compile(r"\biPhone\s+\d{1,2}", re.IGNORECASE),
    re.compile(r"\biPhone\s+SE\s*\d?", re.IGNORECASE),
    re.compile(r"\b(?:RTX|RX|GTX)\s*\d{4}\b", re.IGNORECASE),
    re.compile(r"\b(?:Ryzen|Core)\s+\S+\s+\S+", re.IGNORECASE),
    re.compile(r"\bWatch\s+(?:Series|Ultra)\s+\d+", re.IGNORECASE),
    re.compile(r"\b(?:Fold|Flip)\s*\d+", re.IGNORECASE),
    re.compile(r"\bPixel\s+\d{1,2}", re.IGNORECASE),
    re.compile(r"\b(?:AirPods|Buds)\s+\w+\s*\d*", re.IGNORECASE),
    re.compile(r"\b[A-Z]\d{1,3}\s+\w+", re.IGNORECASE),
]

VARIANT_KEYWORDS = [
    "ultra",
    "fe",
    "plus",
    "lite",
    "pro",
    "pro max",
    "pro+",
    "max",
    "mini",
    "note",
    "neo",
    "edge",
    "slim",
]
_VARIANT_RE = re.compile(
    r"\b(?:"
    + "|".join(re.escape(v) for v in sorted(VARIANT_KEYWORDS, key=len, reverse=True))
    + r")\b",
    re.IGNORECASE,
)

ACCESSORY_WORDS = [
    "пульт",
    "кронштейн",
    "крепление",
    "подставка",
    "кабель",
    "провод",
    "переходник",
    "адаптер",
    "чехол",
    "кейс",
    "стекло",
    "пленка",
    "плёнка",
    "ремешок",
    "зарядк",
    "держатель",
    "брелок",
    "сумка",
    "рюкзак",
    "саундбар",
    "soundbar",
    "колонка speaker",
    "стилус",
    "stylus",
    "наклейка",
    "пленк",
    "протектор",
    "батарея",
    "аккумулятор replacement",
    "плата",
    "матрица",
    "шлейф",
    "блок питания",
    "инвертор",
    "винт",
    "болт",
    "ножк",
    "запчаст",
    "клавиатура для",
    "вентилятор для",
    "петля для",
    "разъем для",
    "шарнир",
    "корпус для",
    "крышка для",
    "аккумулятор для",
]

REFURBISHED_WORDS = [
    "восстановленн",
    "восстановл",
    "восст.",
    "refurbished",
    "реф.",
    " реф ",
    "б/у",
    "б.у.",
    " бу ",
    "уценка",
    "уцен.",
    "витринный",
    "витрина",
    "не новый",
    "как новый",
]

KNOWN_BRANDS = {
    "samsung": ["samsung", "самсунг"],
    "apple": [
        "apple",
        "iphone",
        "айфон",
        "эпл",
        "airpods",
        "аирподс",
        "эирподс",
        "macbook",
        "макбук",
        "ipad",
        "айпад",
    ],
    "xiaomi": ["xiaomi", "сяоми", "ксиоми", "redmi", "редми", "poco", "поко"],
    "huawei": ["huawei", "хуавей", "хуавэй"],
    "honor": ["honor", "хонор"],
    "oneplus": ["oneplus", "ванплас"],
    "google": ["google pixel", "pixel"],
    "nothing": ["nothing"],
    "realme": ["realme", "реалми"],
    "vivo": ["vivo", "виво"],
    "oppo": ["oppo", "оппо"],
    "motorola": ["motorola", "моторола"],
    "tuvio": ["tuvio", "тувио"],
    "lg": ["lg ", " lg"],
    "hisense": ["hisense", "хайсенс"],
    "tcl": ["tcl "],
    "haier": ["haier", "хайер"],
    "philips": ["philips", "филипс"],
    "sony": ["sony", "сони"],
    "dexp": ["dexp"],
    "starwind": ["starwind"],
    "sber": ["sber", "сбер"],
    "lenovo": ["lenovo", "леново"],
    "asus": ["asus", "асус"],
    "hp": ["hp ", " hp"],
    "dell": ["dell "],
    "acer": ["acer", "асер"],
    "msi": ["msi "],
    "jbl": ["jbl"],
    "marshall": ["marshall"],
    "bose": ["bose"],
    "sennheiser": ["sennheiser"],
    "beats": ["beats"],
    "dyson": ["dyson", "дайсон"],
    "roborock": ["roborock", "роборок"],
    "dji": ["dji"],
    "gopro": ["gopro"],
    "playstation": ["playstation", "ps5", "ps4"],
    "nintendo": ["nintendo", "нинтендо"],
    "xbox": ["xbox"],
    "steam deck": ["steam deck"],
}


def extract_model_keys(text: str) -> set[str]:
    keys = set()
    for pat in MODEL_PATTERNS:
        for m in pat.finditer(text):
            keys.add(m.group(0).strip().lower())
    return keys


def extract_variants(text: str) -> set[str]:
    variants = set()
    for m in _VARIANT_RE.finditer(text):
        variants.add(m.group(0).strip().lower())
    text_lower = text.lower()
    if "pro max" in text_lower:
        variants.discard("pro")
        variants.discard("max")
        variants.add("pro max")
    if "pro+" in text_lower:
        variants.discard("pro")
        variants.add("pro+")
    if re.search(r"[A-Za-z]\d{1,3}\+", text):
        variants.add("plus")
    return variants


def detect_product_line(text: str) -> str | None:
    t = text.lower()
    has_redmi = bool(re.search(r"\bredmi\b", t))
    has_poco = bool(re.search(r"\bpoco\b", t))
    has_note = bool(re.search(r"\bnote\b", t))
    has_xiaomi = bool(re.search(r"\bxiaomi\b", t))

    if has_poco:
        return "poco"
    if has_redmi and has_note:
        return "redmi_note"
    if has_redmi:
        return "redmi"
    if has_xiaomi and not has_redmi and not has_poco:
        if re.search(r"\b\d{1,2}[tTsS]?\s", t) or re.search(r"\b\d{1,2}[tTsS]?\b", t):
            if has_note:
                return "redmi_note"
            return "xiaomi_flagship"

    if re.search(r"\bgalaxy\s+s\d", t):
        return "galaxy_s"
    if re.search(r"\bgalaxy\s+a\d", t):
        return "galaxy_a"
    if re.search(r"\bgalaxy\s+m\d", t):
        return "galaxy_m"
    if re.search(r"\bgalaxy\s+z\s*f", t):
        return "galaxy_z"

    return None


def extract_brand(text: str) -> str | None:
    t = text.lower()
    for brand, aliases in KNOWN_BRANDS.items():
        for alias in aliases:
            if alias in t:
                return brand
    return None


def query_significant_words(query: str) -> list[str]:
    _STOP = {
        "для",
        "на",
        "от",
        "по",
        "из",
        "или",
        "the",
        "for",
        "and",
        "with",
        "pro",
        "max",
        "ultra",
        "lite",
        "mini",
        "plus",
    }
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ]{3,}", query.lower())
    return [w for w in words if w not in _STOP]


def is_accessory(title: str) -> bool:
    """Return True if the product title looks like an accessory.

    Match keywords only at word boundaries — a plain substring match causes
    false positives like "провод" (wire) matching inside "беспроводной"
    (wireless), which drops every cordless vacuum / headphones for "dyson"
    or similar queries.
    """
    t = title.lower()
    t_start = t[:50]
    for kw in ACCESSORY_WORDS:
        if re.search(rf"\b{re.escape(kw)}", t_start):
            return True
    if re.search(r"\b(?:для|for|к|under|под)\b", t_start):
        for kw in ACCESSORY_WORDS:
            if re.search(rf"\b{re.escape(kw)}", t):
                return True
    return False


def is_refurbished(title: str) -> bool:
    """Return True if the product title indicates a refurbished item."""
    t = title.lower()
    return any(kw in t for kw in REFURBISHED_WORDS)


def cluster_filter_by_price(
    products: list[dict], *, min_for_cluster: int = 5
) -> tuple[list[dict], dict]:
    """Detect bimodal price distributions and drop the low-price cluster.

    The insight: when a user searches for "PS5", marketplace scrapers return
    a mix of consoles (~50 000 ₽) and games/accessories for that console
    (~4 000 ₽). These form two clearly separated populations in log-price
    space, with a mean ratio of 10×+ between them. By running 1D k-means
    with k=2 on log(price) and checking the cluster separation, we can
    drop the low-price cluster precisely when it represents a different
    product type — not a legitimate sale or refurbished variant.

    Rules:
      - ratio ≥ 3×  : two distinct populations. Drop the SMALLER side,
                      unless the high cluster is a minority of outliers
                      (e.g. RTX 4090 pre-built PCs bundled at 2-3× the
                      card price) — then drop the high cluster instead.
                      See the "high-cluster population gate" below.
      - ratio < 1.5×: homogeneous (e.g. "чехол iPhone" — all cases are
                      similarly cheap). Do not touch anything.
      - 1.5 ≤ r <3×: ambiguous. Apply a mild fallback: drop items below
                      20% of the high-cluster median (catches extreme
                      outliers without nuking legitimate discounts).

    Why not just "drop low always": works for PS5 (games 4k vs console
    55k — drop games), but catastrophically breaks on RTX 4090 (GPUs
    200k vs pre-built PCs 500k+ — dropping the GPU cluster leaves 2
    pre-built outliers). The population gate distinguishes the cases.

    Returns (filtered_products, meta_dict). meta is for logging only.
    """
    import math

    # Sanity ceiling: scrapers occasionally leak sentinel values like
    # INT32_MAX (2_147_483_647) when a listing has no price. Drop those
    # before clustering — a single such outlier dominates k-means and
    # creates a 1-item "high cluster" that hijacks the split. 100M is
    # higher than any real consumer product on Onliner / Yandex Market
    # in either BYN or RUB.
    _PRICE_CEILING = 100_000_000.0
    products = [p for p in products if 0 < float(p.get("price_num") or 0) < _PRICE_CEILING]

    prices_with_idx = [
        (float(p.get("price_num") or 0), i)
        for i, p in enumerate(products)
        if (p.get("price_num") or 0) > 0
    ]

    if len(prices_with_idx) < min_for_cluster:
        return list(products), {"action": "noop_too_few", "kept_in": len(prices_with_idx)}

    log_prices = sorted(math.log(pr) for pr, _ in prices_with_idx)
    n = len(log_prices)

    # 1D k-means with k=2: because the data is sorted, the optimal cut
    # is a single contiguous split. Try every split, pick the one with
    # minimum within-cluster sum of squared errors. O(n²) but n is ≤ 100
    # here — cheap.
    best_sse = float("inf")
    best_i = 1
    for i in range(1, n):
        low = log_prices[:i]
        high = log_prices[i:]
        m_low = sum(low) / len(low)
        m_high = sum(high) / len(high)
        sse = sum((x - m_low) ** 2 for x in low) + sum((x - m_high) ** 2 for x in high)
        if sse < best_sse:
            best_sse = sse
            best_i = i

    low = log_prices[:best_i]
    high = log_prices[best_i:]
    mean_low_log = sum(low) / len(low)
    mean_high_log = sum(high) / len(high)
    # Geometric means (back from log space) make the ratio interpretable
    # as "how many times more expensive is the top cluster on average".
    ratio = math.exp(mean_high_log - mean_low_log)

    high_prices = sorted(math.exp(x) for x in high)
    top_median = high_prices[len(high_prices) // 2]
    low_cluster_boundary = math.exp(log_prices[best_i])

    # High-cluster population gate: how many items sit in the expensive
    # cluster? If it's a tiny minority relative to total, those are the
    # outliers (pre-built PCs bundled with the GPU, enterprise variants,
    # commercial packs) and we want to drop THEM, keeping the low cluster
    # which is the real product. If it's a substantial fraction, the high
    # cluster IS the real product and we drop the cheap-noise low cluster
    # (games for a console, accessories for a phone).
    #
    # Threshold: high needs at least max(5, 25% of total) items to be
    # considered the "main product group". Empirically:
    #   PS5 live-search: 80 items, 28 high — 28 >= max(5,20)=20 → drop low ✓
    #   RTX 4090:        19 items,  2 high —  2 <  max(5, 5)=5  → drop high ✓
    #   iPhone 15 Pro:    43 items, 29 high — 29 >= max(5,11)=11 → drop low ✓
    high_count = len(high)
    low_count = len(low)
    high_is_main = high_count >= max(5, int(n * 0.25))

    if ratio >= 3.0:
        if high_is_main:
            # Keep high cluster (the main product), drop low (cheap noise)
            threshold_low = low_cluster_boundary
            threshold_high = float("inf")
            action = "aggressive_drop_low"
        else:
            # Keep low cluster (the main product), drop high (expensive outliers)
            threshold_low = 0.0
            threshold_high = low_cluster_boundary
            action = "aggressive_drop_high"
    elif ratio < 1.5:
        threshold_low = 0.0
        threshold_high = float("inf")
        action = "noop_homogeneous"
    else:
        threshold_low = top_median * 0.20
        threshold_high = float("inf")
        action = "mild"

    filtered = [p for p in products if threshold_low <= (p.get("price_num") or 0) < threshold_high]

    meta = {
        "action": action,
        "ratio": round(ratio, 2),
        "top_median": round(top_median, 0),
        "low_count": low_count,
        "high_count": high_count,
        "total_in": len(products),
        "total_out": len(filtered),
    }

    # Safety: if the filter would return empty, fall back to the input
    # so the pipeline never kills a whole result set due to a clustering
    # artifact on very small or degenerate distributions.
    if not filtered:
        meta["action"] = action + "_fallback"
        return list(products), meta

    return filtered, meta


def fast_filter(products: list[dict], query: str) -> list[dict]:
    """Stage 1: Fast regex pre-filter. Catches obvious junk (wrong models, accessories, wrong brands)."""
    query_lower = query.lower()
    query_keys = extract_model_keys(query)
    query_variants = extract_variants(query)
    query_brand = extract_brand(query_lower)
    query_words = query_significant_words(query)
    require_overlap = len(query_words) >= 3
    query_line = detect_product_line(query_lower)

    # If the query itself names an accessory (e.g. "чехол iPhone",
    # "кабель USB-C", "пульт для TV"), is_accessory would drop every
    # result. Skip the accessory check entirely in that case — the user
    # is explicitly asking for the thing the check normally rejects.
    query_is_accessory = is_accessory(query)

    primary_models = set()
    for qk in query_keys:
        qm = re.match(r"^([a-z])\s*(\d+)$", qk)
        if qm:
            primary_models.add(qk)

    filtered = []
    for p in products:
        title = p.get("title", "")
        title_lower = title.lower()

        if not query_is_accessory and is_accessory(title):
            continue

        if is_refurbished(title):
            continue

        if require_overlap:
            matches = sum(1 for w in query_words if w in title_lower)
            if matches < min(2, len(query_words)):
                continue

        if query_brand:
            # Check if the title contains ANY alias of the queried brand.
            # This must come BEFORE extract_brand(title), because dict
            # iteration order in KNOWN_BRANDS makes extract_brand return
            # the *first* brand it matches — e.g. a title "Sony PlayStation
            # 5 Slim" matches "sony" first and returns "sony", even though
            # for the query "PS5" we should recognize it as a PlayStation.
            # If the title explicitly mentions the queried brand/product-line,
            # trust that over the generic extract_brand result.
            query_aliases = KNOWN_BRANDS.get(query_brand, [])
            if not any(alias in title_lower for alias in query_aliases):
                # Title doesn't mention the queried brand at all — reject
                # if it's some other known brand, trust other filters if
                # no brand can be detected.
                title_brand = extract_brand(title_lower)
                if title_brand and title_brand != query_brand:
                    continue
                if not title_brand:
                    continue

        title_keys = extract_model_keys(title)
        title_variants = extract_variants(title)

        if query_line:
            title_line = detect_product_line(title_lower)
            if title_line and title_line != query_line:
                continue

        if primary_models:
            has_primary = False
            for pm in primary_models:
                pm_match = re.match(r"([a-z])(\d+)", pm)
                if pm_match:
                    letter, num = pm_match.group(1), pm_match.group(2)
                    if re.search(rf"\b{letter}\s*{num}\b", title_lower):
                        has_primary = True
                        break
            if not has_primary:
                continue

        dominated = False
        for qk in query_keys:
            qm = re.match(r"([a-z]+)\s*(\d+)", qk)
            if not qm:
                continue
            q_prefix, q_num = qm.group(1), qm.group(2)
            for tk in title_keys:
                tm = re.match(r"([a-z]+)\s*(\d+)", tk)
                if not tm:
                    continue
                t_prefix, t_num = tm.group(1), tm.group(2)
                if q_prefix == t_prefix and q_num != t_num:
                    dominated = True
                    break
            if dominated:
                break
        if dominated:
            continue

        if query_variants:
            if not query_variants.intersection(title_variants):
                continue

        filtered.append(p)

    if not filtered:
        # If a known brand was detected in the query, trust the brand filter
        # and return an empty list. Brand mismatch is a high-confidence signal:
        # e.g. query="PlayStation 5" vs titles "Игра ... для Sony PS5" — the
        # scraper found zero real consoles, only PS5 games. Falling back to
        # the original list here causes the analyze pipeline to compute stats
        # over completely wrong products.
        if query_brand:
            return []
        # Otherwise regex may have been too aggressive — fall back and let
        # the AI filter (Stage 2) decide on semantic relevance.
        return products

    # Price-based clustering happens later in the pipeline, on the combined
    # pool across all sources — not here per-source, because per-source
    # batches are too small to detect bimodal distributions reliably.
    return filtered
