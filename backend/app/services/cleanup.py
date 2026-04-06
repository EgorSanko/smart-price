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
    """Return True if the product title looks like an accessory."""
    t = title.lower()
    t_start = t[:50]
    for kw in ACCESSORY_WORDS:
        if kw in t_start:
            return True
    if re.search(r"\b(?:для|for|к|under|под)\b", t_start):
        for kw in ACCESSORY_WORDS:
            if kw in t:
                return True
    return False


def is_refurbished(title: str) -> bool:
    """Return True if the product title indicates a refurbished item."""
    t = title.lower()
    return any(kw in t for kw in REFURBISHED_WORDS)


def remove_price_outliers(products: list[dict]) -> list[dict]:
    """Remove products with prices that are extreme outliers (below 25% of median)."""
    if len(products) < 4:
        return products
    prices = sorted(p.get("price_num", 0) for p in products if p.get("price_num", 0) > 0)
    if len(prices) < 4:
        return products
    median = prices[len(prices) // 2]
    if median <= 0:
        return products
    threshold = median * 0.25
    result = [p for p in products if p.get("price_num", 0) >= threshold]
    return result if result else products


def fast_filter(products: list[dict], query: str) -> list[dict]:
    """Stage 1: Fast regex pre-filter. Catches obvious junk (wrong models, accessories, wrong brands)."""
    query_lower = query.lower()
    query_keys = extract_model_keys(query)
    query_variants = extract_variants(query)
    query_brand = extract_brand(query_lower)
    query_words = query_significant_words(query)
    require_overlap = len(query_words) >= 3
    query_line = detect_product_line(query_lower)

    primary_models = set()
    for qk in query_keys:
        qm = re.match(r"^([a-z])\s*(\d+)$", qk)
        if qm:
            primary_models.add(qk)

    filtered = []
    for p in products:
        title = p.get("title", "")
        title_lower = title.lower()

        if is_accessory(title):
            continue

        if is_refurbished(title):
            continue

        if require_overlap:
            matches = sum(1 for w in query_words if w in title_lower)
            if matches < min(2, len(query_words)):
                continue

        if query_brand:
            title_brand = extract_brand(title_lower)
            if title_brand and title_brand != query_brand:
                continue
            if not title_brand:
                brand_found = any(
                    alias in title_lower for alias in KNOWN_BRANDS.get(query_brand, [])
                )
                if not brand_found:
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
        # If regex killed everything, fall back to original products
        # and let AI filter (Stage 2) handle relevance instead
        return products

    filtered = remove_price_outliers(filtered)
    return filtered
