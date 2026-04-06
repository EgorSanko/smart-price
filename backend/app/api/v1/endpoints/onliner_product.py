"""Onliner product detail endpoint — rich product data for Belarus product pages."""

import asyncio
import json
import re

import httpx
import structlog
from fastapi import APIRouter, HTTPException

from app.scrapers.external_reviews import fetch_all_external_reviews


router = APIRouter(prefix="/onliner", tags=["onliner"])

logger = structlog.get_logger()

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/html",
    "Accept-Language": "ru-RU,ru;q=0.9",
}
_API = "https://catalog.onliner.by/sdapi/catalog.api/products"
_SHOP_API = "https://catalog.onliner.by/sdapi/shop.api/products"


def _extract_digest_from_ldjson(html: str) -> dict:
    """Extract AI digest (pros/cons) from LD+JSON structured data."""
    digest = {}
    for m in re.finditer(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL,
    ):
        try:
            data = json.loads(m.group(1).strip())
            items = data if isinstance(data, list) else [data]
            for item in items:
                pos = item.get("positiveNotes", {}).get("itemListElement", [])
                neg = item.get("negativeNotes", {}).get("itemListElement", [])
                if pos or neg:
                    digest["pros"] = [p["name"] for p in pos if p.get("name")]
                    digest["cons"] = [n["name"] for n in neg if n.get("name")]
                    return digest
        except (json.JSONDecodeError, TypeError, KeyError):
            continue
    return digest


def _extract_configurations(html: str) -> dict[str, list]:
    """Extract product configuration options (memory, color, etc.) from HTML."""
    configs: dict[str, list] = {}
    for row_m in re.finditer(r'offers-description-filter__sign">([^<]+)</div>', html):
        label = row_m.group(1).strip().rstrip(":")
        pos = row_m.end()
        next_row = html.find("offers-description-filter__row", pos + 10)
        if next_row < 0:
            next_row = pos + 3000
        chunk = html[pos:next_row]

        opts = []
        for ctrl in re.finditer(
            r'(?:<a\s+href="([^"]+)"[^>]*>|<label[^>]*>)'
            r"(.*?)"
            r"<span[^>]*switcher-inner[^>]*>([^<]+)</span>",
            chunk,
            re.DOTALL,
        ):
            href = ctrl.group(1) or ""
            inner = ctrl.group(2)
            name = ctrl.group(3).strip()
            is_selected = "checked" in inner
            key = href.rstrip("/").split("/")[-1] if href else ""
            opts.append({"name": name, "key": key, "selected": is_selected})

        if opts:
            configs[label] = opts
    return configs


def _extract_specs_from_html(html: str) -> tuple[dict, str]:
    """Extract specs groups and long description from Onliner HTML."""
    specs: dict[str, list] = {}
    long_description = ""

    specs_idx = html.find('class="product-specs"')
    if specs_idx == -1:
        return specs, long_description

    # Find the end of specs section
    end_idx = len(html)
    for marker in ['class="product-recommended', 'class="catalog-footer', "</main>"]:
        eidx = html.find(marker, specs_idx + 100)
        if 0 < eidx < end_idx:
            end_idx = eidx
    specs_html = html[specs_idx:end_idx]

    # Split by group titles
    parts = re.split(r"product-specs__table-title-inner[^>]*>\s*", specs_html)
    for part in parts[1:]:
        title_m = re.match(r"(.+?)\s*</h3>", part)
        if not title_m:
            continue
        group_name = title_m.group(1).strip()

        rows = re.findall(
            r"<tr>\s*<td[^>]*>\s*(.+?)\s*(?:<!--.*?-->)?\s*</td>\s*<td[^>]*>\s*(.*?)\s*</td>\s*</tr>",
            part,
            re.DOTALL,
        )
        group_specs = []
        for name_raw, val_raw in rows:
            name = re.sub(r"<[^>]+>", "", name_raw).strip()
            val = re.sub(r"<[^>]+>", "", val_raw).strip()
            val = re.sub(r"\s+", " ", val)
            if not name or not val:
                continue

            # "Описание" in "Общая информация" is the long marketing description
            if name == "Описание" and group_name == "Общая информация":
                long_description = val
                continue

            group_specs.append({"label": name, "value": val})

        if group_specs:
            specs[group_name] = group_specs

    # Also try to extract long description from special collapsed row
    if not long_description:
        desc_m = re.search(
            r"product-specs__table-spread.*?"
            r"i-faux-td[^>]*>\s*Описание\s*(?:<!--.*?-->)?\s*</div>\s*"
            r"<div[^>]*>\s*(.*?)\s*</div>\s*</div>",
            specs_html,
            re.DOTALL,
        )
        if desc_m:
            raw = desc_m.group(1)
            raw = re.sub(r"<br\s*/?>", "\n", raw)
            raw = re.sub(r"</p>\s*<p[^>]*>", "\n\n", raw)
            raw = re.sub(r"<[^>]+>", "", raw)
            long_description = raw.strip()

    return specs, long_description


@router.get("/product/{key:path}")
async def get_product(key: str):
    """Fetch complete product data from Onliner: details, offers, reviews, price history."""
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        # Phase 1: fetch JSON API data in parallel
        details_task = client.get(f"{_API}/{key}", headers=_HEADERS)
        offers_task = client.get(f"{_SHOP_API}/{key}/positions", headers=_HEADERS)
        reviews_task = client.get(
            f"{_API}/{key}/reviews",
            params={"order": "created_at:desc"},
            headers=_HEADERS,
        )
        history_task = client.get(f"{_API}/{key}/prices-history", headers=_HEADERS)

        results = await asyncio.gather(
            details_task,
            offers_task,
            reviews_task,
            history_task,
            return_exceptions=True,
        )

    details_resp, offers_resp, reviews_resp, history_resp = results

    # --- Product Details ---
    if isinstance(details_resp, Exception) or details_resp.status_code != 200:
        raise HTTPException(status_code=404, detail="Product not found on Onliner")

    d = details_resp.json()
    product = {
        "key": key,
        "title": d.get("full_name", ""),
        "name": d.get("name", ""),
        "description": d.get("description", ""),
        "micro_description": d.get("micro_description", ""),
        "html_url": d.get("html_url", ""),
        "image": (d.get("images") or {}).get("header", ""),
        "images": d.get("images", {}),
        "rating": (d.get("reviews") or {}).get("rating", 0),
        "reviews_count": (d.get("reviews") or {}).get("count", 0),
    }

    # Category breadcrumb
    sch = d.get("schema") or {}
    product["category"] = sch.get("name", "")
    product["category_key"] = sch.get("key", "")

    # Prices
    pr = d.get("prices") or {}
    product["price_min"] = float((pr.get("price_min") or {}).get("amount", 0))
    product["price_max"] = float((pr.get("price_max") or {}).get("amount", 0))
    product["offers_count"] = (pr.get("offers") or {}).get("count", 0)
    product["currency"] = "BYN"

    # --- Phase 2: fetch HTML page for specs, digest, and long description ---
    html_page = ""
    html_url = d.get("html_url", "")
    if html_url:
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c2:
                html_resp = await c2.get(
                    html_url,
                    headers={**_HEADERS, "Accept": "text/html"},
                )
                if html_resp.status_code == 200:
                    html_page = html_resp.text
        except Exception as exc:
            logger.warning("Failed to fetch HTML page", url=html_url, error=str(exc))

    # --- AI Digest (pros/cons) from LD+JSON ---
    product["digest"] = _extract_digest_from_ldjson(html_page) if html_page else {}

    # --- Specifications + long description from HTML tables ---
    specs, long_description = _extract_specs_from_html(html_page) if html_page else ({}, "")
    product["specs"] = specs
    product["long_description"] = long_description

    # --- Configurations (storage, color, revision) ---
    product["configurations"] = _extract_configurations(html_page) if html_page else {}

    # --- Offers / Sellers ---
    offers = []
    if not isinstance(offers_resp, Exception) and offers_resp.status_code == 200:
        od = offers_resp.json()
        positions = od.get("positions", {}).get("primary", [])
        shops_data = od.get("shops", {})
        seen = set()

        for pos in positions[:20]:
            sid = str(pos.get("shop_id", ""))
            if sid in seen:
                continue
            seen.add(sid)

            price_amount = float(pos.get("position_price", {}).get("amount", 0))
            if price_amount <= 0:
                continue

            shop = shops_data.get(sid, {})
            shop_reviews = shop.get("reviews", {})

            offer = {
                "seller": shop.get("title", "Магазин"),
                "shop_id": sid,
                "price": price_amount,
                "warranty": pos.get("warranty", 0),
                "delivery": pos.get("delivery", {}).get("town_time", ""),
                "rating": shop_reviews.get("rating", 0),
                "reviews_count": shop_reviews.get("count", 0),
                "logo": shop.get("logo", ""),
                "url": shop.get("html_url", ""),
            }
            offers.append(offer)

    offers.sort(key=lambda x: x["price"])
    product["offers"] = offers
    if offers:
        product["best_price"] = offers[0]["price"]
        product["best_seller"] = offers[0]["seller"]

    # --- Reviews ---
    reviews = []
    if not isinstance(reviews_resp, Exception) and reviews_resp.status_code == 200:
        for rv in reviews_resp.json().get("reviews", [])[:10]:
            author_data = rv.get("author", {})
            review = {
                "author": author_data.get("name", "Пользователь"),
                "rating": rv.get("rating", 0),
                "date": rv.get("created_at", "")[:10],
                "pros": rv.get("pros_text", ""),
                "cons": rv.get("cons_text", ""),
                "summary": rv.get("summary_text", "") or rv.get("text", ""),
                "likes": rv.get("likes_count", 0),
                "dislikes": rv.get("dislikes_count", 0),
            }
            reviews.append(review)

    product["reviews"] = reviews

    # --- External Reviews (Wildberries, Otzovik, iRecommend) ---
    try:
        ext_sources = await fetch_all_external_reviews(product.get("title", ""), limit_per_source=8)
    except Exception as exc:
        logger.warning("External reviews failed", error=str(exc))
        ext_sources = []
    product["external_reviews"] = ext_sources

    # --- Price History ---
    price_history = []
    if not isinstance(history_resp, Exception) and history_resp.status_code == 200:
        hd = history_resp.json()
        chart = hd.get("chart_data", {})
        for item in chart.get("items", []):
            ps = item.get("price")
            if ps is not None:
                price_history.append(
                    {
                        "date": item["date"],
                        "price": float(ps),
                    }
                )

    product["price_history"] = price_history
    if price_history:
        prices_list = [p["price"] for p in price_history]
        product["price_stats"] = {
            "min": min(prices_list),
            "max": max(prices_list),
            "avg": round(sum(prices_list) / len(prices_list), 2),
        }

    return product
