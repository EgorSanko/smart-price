"""External review scrapers: Wildberries, Otzovik."""

import asyncio
import re

import httpx
import structlog


logger = structlog.get_logger()

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
_HEADERS_HTML = {
    "User-Agent": _UA,
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8",
}


# ─── Wildberries ───────────────────────────────────────────────────────────


async def fetch_wb_reviews(product_name: str, limit: int = 10) -> dict:
    """Search WB for product and fetch reviews via public feedbacks API."""
    result = {
        "source": "wildberries",
        "source_label": "Wildberries",
        "reviews": [],
        "rating": 0,
        "count": 0,
    }

    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            # Step 1: Search via WB API — try multiple domains/versions
            products = []
            search_params = {
                "query": product_name,
                "resultset": "catalog",
                "limit": "10",
                "sort": "popular",
                "appType": "1",
                "curr": "rub",
                "dest": "-1257786",
                "lang": "ru",
                "spp": "30",
                "suppressSpellcheck": "false",
            }
            for domain in ["search.wb.ru", "search.wildberries.ru"]:
                for ver in ["v18", "v17", "v7"]:
                    try:
                        search_resp = await client.get(
                            f"https://{domain}/exactmatch/ru/common/{ver}/search",
                            params=search_params,
                            headers={"User-Agent": _UA, "Accept": "application/json"},
                        )
                        if search_resp.status_code == 200:
                            data = search_resp.json()
                            products = (
                                data.get("data", {}).get("products") or data.get("products") or []
                            )
                            if products:
                                break
                        elif search_resp.status_code == 429:
                            await asyncio.sleep(1.5)
                            continue
                    except Exception:
                        continue
                if products:
                    break

            if not products:
                return result

            # Pick product with most feedbacks among top results
            best = max(products[:5], key=lambda p: p.get("feedbacks", 0))
            root_id = best.get("root", best.get("id"))
            result["rating"] = best.get("rating", 0)
            result["count"] = best.get("feedbacks", 0)
            result["product_name"] = best.get("name", "")

            if not root_id:
                return result

            # Step 2: Fetch reviews from public feedbacks API
            for domain in ["feedbacks1.wb.ru", "feedbacks2.wb.ru"]:
                fb_resp = await client.get(
                    f"https://{domain}/feedbacks/v2/{root_id}",
                    headers={"User-Agent": _UA, "Accept": "application/json"},
                )
                if fb_resp.status_code == 200:
                    fb_data = fb_resp.json()
                    feedbacks = fb_data.get("feedbacks") or []
                    for fb in feedbacks[:limit]:
                        review = {
                            "author": (fb.get("wbUserDetails") or {}).get("name", "")
                            or "Покупатель WB",
                            "rating": fb.get("productValuation", 0),
                            "date": (fb.get("createdDate", "") or "")[:10],
                            "pros": fb.get("pros", "") or "",
                            "cons": fb.get("cons", "") or "",
                            "summary": fb.get("text", "") or "",
                            "likes": 0,
                            "dislikes": 0,
                            "source": "wildberries",
                        }
                        result["reviews"].append(review)
                    break

    except Exception as e:
        logger.warning("WB reviews fetch failed", error=str(e))

    return result


# ─── Otzovik ───────────────────────────────────────────────────────────────


async def fetch_otzovik_reviews(product_name: str, limit: int = 10) -> dict:
    """Search Otzovik and scrape reviews from the first matching product."""
    result = {
        "source": "otzovik",
        "source_label": "Otzovik",
        "reviews": [],
        "rating": 0,
        "count": 0,
    }

    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            # Search on Otzovik via main page query
            search_resp = await client.get(
                "https://otzovik.com/",
                params={"search_text": product_name},
                headers=_HEADERS_HTML,
            )
            if search_resp.status_code != 200:
                return result

            html = search_resp.text

            # Find first product review link
            link_m = re.search(r'href="(/reviews/[^"]+)"', html)
            if not link_m:
                return result

            product_url = "https://otzovik.com" + link_m.group(1)

            # Fetch product reviews page
            page_resp = await client.get(product_url, headers=_HEADERS_HTML)
            if page_resp.status_code != 200:
                return result

            page = page_resp.text

            # Extract rating from schema.org markup
            rating_m = re.search(r'itemprop="ratingValue"[^>]*content="([^"]+)"', page)
            if not rating_m:
                rating_m = re.search(r'content="([^"]+)"[^>]*itemprop="ratingValue"', page)
            if rating_m:
                try:
                    result["rating"] = round(float(rating_m.group(1)), 1)
                except ValueError:
                    pass

            # Extract review count
            count_m = re.search(r'itemprop="reviewCount"[^>]*content="([^"]+)"', page)
            if not count_m:
                count_m = re.search(r'content="([^"]+)"[^>]*itemprop="reviewCount"', page)
            if count_m:
                try:
                    result["count"] = int(count_m.group(1))
                except ValueError:
                    pass

            # Extract individual reviews — split by review-body blocks
            review_blocks = re.split(r'class="review-body\b', page)

            for block in review_blocks[1 : limit + 1]:
                # Author
                author_m = re.search(r"user-login[^>]*>\s*<a[^>]*>([^<]+)</a>", block, re.DOTALL)
                author = author_m.group(1).strip() if author_m else "Пользователь"

                # Rating
                stars_m = re.search(r'tooltip-right"\s*title="(\d)', block)
                if not stars_m:
                    stars_m = re.search(r"product-rating[^>]*>(\d)", block)
                rating = int(stars_m.group(1)) if stars_m else 0

                # Date
                date_m = re.search(
                    r"review-postdate[^>]*>.*?<abbr[^>]*>([^<]+)</abbr>", block, re.DOTALL
                )
                if not date_m:
                    date_m = re.search(r"review-postdate[^>]*>\s*([^<]+)<", block)
                date = date_m.group(1).strip() if date_m else ""

                # Pros — strip "Достоинства:" prefix
                pros_m = re.search(r"review-plus[^>]*>(.*?)</div>", block, re.DOTALL)
                pros = ""
                if pros_m:
                    pros = re.sub(r"<[^>]+>", "", pros_m.group(1)).strip()
                    pros = re.sub(r"^Достоинства:\s*", "", pros)

                # Cons — strip "Недостатки:" prefix
                cons_m = re.search(r"review-minus[^>]*>(.*?)</div>", block, re.DOTALL)
                cons = ""
                if cons_m:
                    cons = re.sub(r"<[^>]+>", "", cons_m.group(1)).strip()
                    cons = re.sub(r"^Недостатки:\s*", "", cons)

                # Summary text
                text_m = re.search(r"review-body-text[^>]*>(.*?)</div>", block, re.DOTALL)
                summary = ""
                if text_m:
                    summary = re.sub(r"<[^>]+>", "", text_m.group(1)).strip()[:500]

                review = {
                    "author": author,
                    "rating": rating,
                    "date": date,
                    "pros": pros,
                    "cons": cons,
                    "summary": summary,
                    "likes": 0,
                    "dislikes": 0,
                    "source": "otzovik",
                }
                result["reviews"].append(review)

    except Exception as e:
        logger.warning("Otzovik reviews fetch failed", error=str(e))

    return result


# ─── Aggregator ────────────────────────────────────────────────────────────


async def fetch_all_external_reviews(product_name: str, limit_per_source: int = 8) -> list[dict]:
    """Fetch reviews from Wildberries and Otzovik in parallel."""
    results = await asyncio.gather(
        fetch_wb_reviews(product_name, limit_per_source),
        fetch_otzovik_reviews(product_name, limit_per_source),
        return_exceptions=True,
    )

    sources = []
    for r in results:
        if isinstance(r, Exception):
            logger.warning("External review source failed", error=str(r))
            continue
        if r and (r.get("reviews") or r.get("count", 0) > 0):
            sources.append(r)

    return sources
