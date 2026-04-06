#!/usr/bin/env python3
"""Smoke test for scraper infrastructure.

Run manually to verify scrapers work against real marketplaces.
Does NOT require the full app to be running — standalone script.

Usage:
    # Quick test (WB API only — safest, no browser needed)
    python -m tests.test_scrapers.smoke_test --quick

    # Full test (WB + Ozon with browser)
    python -m tests.test_scrapers.smoke_test --full

    # Test antidetect components only (no network)
    python -m tests.test_scrapers.smoke_test --unit

    # Test with proxy
    python -m tests.test_scrapers.smoke_test --quick --proxy http://user:pass@host:port
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time


# ANSI colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def ok(msg: str) -> None:
    print(f"  {GREEN}✓{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"  {RED}✗{RESET} {msg}")


def warn(msg: str) -> None:
    print(f"  {YELLOW}⚠{RESET} {msg}")


def info(msg: str) -> None:
    print(f"  {CYAN}ℹ{RESET} {msg}")


def header(msg: str) -> None:
    print(f"\n{BOLD}{'─' * 60}")
    print(f"  {msg}")
    print(f"{'─' * 60}{RESET}")


# ---------------------------------------------------------------------------
# Unit tests (no network)
# ---------------------------------------------------------------------------


def test_antidetect_unit() -> int:
    """Test antidetect components without network access."""
    header("Anti-detection components (no network)")
    errors = 0

    # --- ProxyRotator ---
    print("\n  ProxyRotator:")
    try:
        from app.scrapers.antidetect import ProxyRotator

        rotator = ProxyRotator(min_cooldown=0.01)
        rotator.add_proxies(
            [
                "http://test1:8080",
                "http://test2:8080",
                "http://test3:8080",
            ]
        )

        async def _test_rotator():
            proxy = await rotator.get_next()
            assert proxy is not None
            rotator.report_success(proxy, 100.0)
            assert proxy.total_requests == 1
            assert proxy.consecutive_failures == 0

            rotator.report_failure(proxy)
            assert proxy.consecutive_failures == 1

            stats = rotator.get_stats()
            assert stats["total"] == 3

        asyncio.run(_test_rotator())
        ok("ProxyRotator: add, get_next, report_success/failure, stats")
    except Exception as e:
        fail(f"ProxyRotator: {e}")
        errors += 1

    # --- HumanBehavior ---
    print("\n  HumanBehavior:")
    try:
        from app.scrapers.antidetect import HumanBehavior

        async def _test_behavior():
            start = time.monotonic()
            await HumanBehavior.random_delay(0.01, 0.05)
            elapsed = time.monotonic() - start
            assert elapsed >= 0.005  # At least some delay
            assert elapsed < 1.0  # Not absurdly long

        asyncio.run(_test_behavior())
        ok("random_delay: works within bounds")

        action = HumanBehavior.create_page_action(scroll=True)
        assert callable(action)
        ok("create_page_action: returns callable")

        warmup = HumanBehavior.create_warmup_actions("https://ozon.ru")
        assert len(warmup) >= 1
        ok("create_warmup_actions: returns action list")
    except Exception as e:
        fail(f"HumanBehavior: {e}")
        errors += 1

    # --- RequestFingerprint ---
    print("\n  RequestFingerprint:")
    try:
        from app.scrapers.antidetect import RequestFingerprint

        headers = RequestFingerprint.get_random_headers()
        assert "Accept-Language" in headers
        assert "ru" in headers["Accept-Language"].lower()
        ok(f"Headers: Accept-Language = {headers['Accept-Language']}")

        viewport = RequestFingerprint.get_random_viewport()
        assert viewport["width"] >= 1280
        ok(f"Viewport: {viewport['width']}x{viewport['height']}")

        referer = RequestFingerprint.build_referer_chain(
            "https://ozon.ru", "https://ozon.ru/product/test-123"
        )
        assert "search" in referer
        ok(f"Referer chain: {referer}")
    except Exception as e:
        fail(f"RequestFingerprint: {e}")
        errors += 1

    # --- SessionManager ---
    print("\n  SessionManager:")
    try:
        from app.scrapers.antidetect import ScrapingSession

        session = ScrapingSession(marketplace="test", max_requests_per_session=3)
        assert not session.is_expired
        ok("New session: not expired")

        session.record_visit("https://test.com/1")
        session.record_visit("https://test.com/2")
        session.record_visit("https://test.com/3")
        assert session.is_expired
        ok("Session expires after max_requests")
    except Exception as e:
        fail(f"SessionManager: {e}")
        errors += 1

    # --- Block detection ---
    print("\n  Block detection:")
    try:
        from app.scrapers.base import _is_blocked

        assert _is_blocked(403, "") == "http_403"
        ok("403 → http_403")

        assert _is_blocked(429, "") == "rate_limited"
        ok("429 → rate_limited")

        assert _is_blocked(200, "Подтвердите, что вы не робот") == "captcha"
        ok("Captcha (RU) → captcha")

        assert _is_blocked(200, "cf-browser-verification") == "cloudflare"
        ok("Cloudflare → cloudflare")

        assert _is_blocked(200, "x" * 1000) is None
        ok("Normal 200 → None (not blocked)")

        assert _is_blocked(200, "{}") == "empty_response"
        ok("Empty body → empty_response")
    except Exception as e:
        fail(f"Block detection: {e}")
        errors += 1

    # --- Ozon parser ---
    print("\n  Ozon parser:")
    try:
        from app.scrapers.ozon import _extract_product_id_from_url, _parse_ozon_price

        assert _parse_ozon_price("79 990 ₽") == 79990.0
        ok("Price: '79 990 ₽' → 79990.0")

        assert _parse_ozon_price("1\xa0234\xa0₽") == 1234.0
        ok("Price: '1\\xa0234\\xa0₽' → 1234.0 (nbsp)")

        assert _parse_ozon_price(None) is None
        ok("Price: None → None")

        pid = _extract_product_id_from_url("/product/iphone-15-123456789/")
        assert pid == "123456789"
        ok(f"URL → product_id: {pid}")
    except Exception as e:
        fail(f"Ozon parser: {e}")
        errors += 1

    # --- WB parser ---
    print("\n  WB parser:")
    try:
        from app.scrapers.wildberries import _build_wb_image_url, _get_basket_number

        basket = _get_basket_number(143)
        assert basket == "01"
        ok(f"Basket for vol=143: {basket}")

        url = _build_wb_image_url(111222333)
        assert "wbbasket.ru" in url
        ok(f"Image URL: {url[:60]}...")
    except Exception as e:
        fail(f"WB parser: {e}")
        errors += 1

    return errors


# ---------------------------------------------------------------------------
# Quick smoke test (WB API — no browser needed)
# ---------------------------------------------------------------------------


async def test_wb_api(proxy: str | None = None) -> int:
    """Test Wildberries API with real HTTP request."""
    header("Wildberries API (real request)")
    errors = 0

    try:
        import httpx

        info("Fetching WB search API for 'iphone 15'...")

        params = {
            "query": "iphone 15",
            "resultset": "catalog",
            "limit": 5,
            "page": 1,
            "appType": 1,
            "curr": "rub",
            "dest": -1257786,
            "sort": "popular",
        }

        kwargs: dict = {"timeout": 15.0, "follow_redirects": True}
        if proxy:
            kwargs["proxy"] = proxy

        start = time.monotonic()
        async with httpx.AsyncClient(**kwargs) as client:
            response = await client.get(
                "https://search.wb.ru/exactmatch/ru/common/v9/search",
                params=params,
            )
        elapsed = time.monotonic() - start

        if response.status_code == 200:
            data = response.json()
            products = data.get("data", {}).get("products", [])
            ok(f"HTTP 200 in {elapsed:.1f}s")
            ok(f"Found {len(products)} products")

            if products:
                p = products[0]
                name = p.get("name", "?")
                price = p.get("salePriceU", 0) / 100
                rating = p.get("rating", 0)
                ok(f"First: '{name}' — {price:.0f} ₽ (★{rating})")

                # Test parser
                from unittest.mock import patch

                with patch("app.scrapers.base._get_proxy_rotator"):
                    from app.scrapers.wildberries import WildberriesScraper

                    scraper = WildberriesScraper()
                    parsed = scraper._parse_api_item(p)
                    ok(f"Parsed: id={parsed.external_id}, price={parsed.current_price}")
            else:
                warn("No products returned (might be rate-limited)")
        elif response.status_code == 429:
            warn("Rate limited (429) — try again later or use proxy")
            errors += 1
        else:
            fail(f"HTTP {response.status_code}")
            errors += 1

    except ImportError:
        warn("httpx not installed — run: pip install httpx")
        errors += 1
    except Exception as e:
        fail(f"WB API error: {e}")
        errors += 1

    # --- Test WB product detail API ---
    print()
    try:
        info("Fetching WB product detail (card API)...")

        async with httpx.AsyncClient(timeout=15.0) as client:
            # Use a known popular product
            response = await client.get(
                "https://card.wb.ru/cards/v2/detail",
                params={
                    "appType": 1,
                    "curr": "rub",
                    "dest": -1257786,
                    "nm": "111222333",  # Test ID
                },
            )

        if response.status_code == 200:
            data = response.json()
            products = data.get("data", {}).get("products", [])
            if products:
                ok(f"Card API: got product '{products[0].get('name', '?')}'")
            else:
                info("Card API: no data for test ID (expected for fake ID)")
                ok("Card API: endpoint reachable")
        else:
            warn(f"Card API: HTTP {response.status_code}")

    except Exception as e:
        warn(f"Card API: {e}")

    return errors


# ---------------------------------------------------------------------------
# Full smoke test (Ozon with browser — requires Scrapling installed)
# ---------------------------------------------------------------------------


async def test_ozon_browser(proxy: str | None = None) -> int:
    """Test Ozon with StealthyFetcher (requires browser)."""
    header("Ozon browser test (StealthyFetcher)")
    errors = 0

    try:
        from scrapling.fetchers import StealthyFetcher
    except ImportError:
        warn("Scrapling not installed — run: pip install 'scrapling[fetchers]'")
        warn("Then run: scrapling install")
        return 1

    try:
        info("Fetching ozon.ru homepage...")

        kwargs: dict = {
            "headless": True,
            "network_idle": True,
            "disable_resources": True,
            "block_webrtc": True,
            "timeout": 30000,
        }
        if proxy:
            kwargs["proxy"] = proxy

        start = time.monotonic()
        page = await StealthyFetcher.async_fetch(
            "https://www.ozon.ru",
            **kwargs,
        )
        elapsed = time.monotonic() - start

        body = str(page.body) if hasattr(page, "body") else ""

        from app.scrapers.base import _is_blocked

        block_reason = _is_blocked(page.status, body)

        if block_reason:
            fail(f"Blocked! Reason: {block_reason}")
            fail(f"Status: {page.status}, body length: {len(body)}")
            if "captcha" in (block_reason or ""):
                warn("Got captcha — need residential proxy")
            errors += 1
        elif page.status == 200:
            ok(f"HTTP 200 in {elapsed:.1f}s")
            ok(f"Body length: {len(body)} chars")

            # Check for Ozon-specific elements
            has_search = "searchResultsV2" in body or "search" in body.lower()
            has_ozon = "ozon" in body.lower()
            ok(f"Contains 'ozon': {has_ozon}")
            info(f"Contains search widget: {has_search}")
        else:
            fail(f"HTTP {page.status}")
            errors += 1

    except Exception as e:
        fail(f"Ozon browser error: {e}")
        errors += 1

    # --- Test search ---
    if errors == 0:
        print()
        try:
            info("Searching Ozon for 'наушники'...")

            kwargs["google_search"] = True
            start = time.monotonic()
            page = await StealthyFetcher.async_fetch(
                "https://www.ozon.ru/search/?text=наушники&from_global=true",
                **kwargs,
            )
            elapsed = time.monotonic() - start

            body = str(page.body) if hasattr(page, "body") else ""
            block_reason = _is_blocked(page.status, body)

            if block_reason:
                warn(f"Search blocked: {block_reason}")
                warn("This is expected without residential proxy")
            elif page.status == 200:
                ok(f"Search page loaded in {elapsed:.1f}s")
                ok(f"Body: {len(body)} chars")

                # Count product cards (rough)
                card_count = body.count("data-widget") if body else 0
                info(f"data-widget elements: ~{card_count}")
            else:
                warn(f"Search: HTTP {page.status}")

        except Exception as e:
            warn(f"Ozon search error: {e}")

    return errors


# ---------------------------------------------------------------------------
# Config check
# ---------------------------------------------------------------------------


def check_config() -> int:
    """Check that configuration is accessible."""
    header("Configuration check")
    errors = 0

    try:
        from app.config import settings

        ok("app.config.settings imported OK")

        proxy_urls = getattr(settings, "SCRAPER_PROXY_URLS", "")
        if proxy_urls:
            count = len([u for u in proxy_urls.split(",") if u.strip()])
            ok(f"Proxy URLs configured: {count} proxies")
        else:
            info("No proxy URLs configured (SCRAPER_PROXY_URLS is empty)")
            info("Without proxies, Ozon will block after a few requests")
    except Exception as e:
        warn(f"Config: {e}")
        info("This is OK if running standalone (outside Docker)")

    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Smoke test for Smart Price scrapers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m tests.test_scrapers.smoke_test --unit        # No network
  python -m tests.test_scrapers.smoke_test --quick       # WB API only
  python -m tests.test_scrapers.smoke_test --full        # WB + Ozon
  python -m tests.test_scrapers.smoke_test --quick --proxy http://user:pass@host:port
        """,
    )
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests only (no network)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run WB API test (HTTP only, no browser)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run all tests including Ozon browser test",
    )
    parser.add_argument(
        "--proxy",
        type=str,
        default=None,
        help="Proxy URL (http://user:pass@host:port)",
    )
    args = parser.parse_args()

    # Default to --unit if nothing specified
    if not args.unit and not args.quick and not args.full:
        args.unit = True

    print(f"{BOLD}Smart Price Scraper Smoke Test{RESET}")
    print(f"{'=' * 60}")
    total_errors = 0

    # Always run config check
    total_errors += check_config()

    # Unit tests
    if args.unit or args.quick or args.full:
        total_errors += test_antidetect_unit()

    # WB API test
    if args.quick or args.full:
        total_errors += asyncio.run(test_wb_api(proxy=args.proxy))

    # Ozon browser test
    if args.full:
        total_errors += asyncio.run(test_ozon_browser(proxy=args.proxy))

    # Summary
    print(f"\n{'=' * 60}")
    if total_errors == 0:
        print(f"{GREEN}{BOLD}All tests passed ✓{RESET}")
    else:
        print(f"{RED}{BOLD}{total_errors} test(s) failed ✗{RESET}")

    sys.exit(total_errors)


if __name__ == "__main__":
    main()
