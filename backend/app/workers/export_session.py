"""Export Yandex Alisa session (cookies + localStorage) from local Edge profile.

Run once locally:
    python -m app.workers.export_session

What it does:
  1. Opens Edge with your real User Data profile.
  2. Navigates to https://alice.yandex.ru/ so cookies for *.yandex.ru are live.
  3. Waits for you to press Enter (so you can visually confirm the account is logged in).
  4. Dumps storage_state to session/yandex_storage.json.

The resulting JSON has the entire cookie jar + localStorage for every origin loaded.
It's what Playwright on the VPS loads via browser.new_context(storage_state=...).

Security: treat yandex_storage.json like a password. Don't commit it. scp to VPS over SSH only.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from playwright.async_api import async_playwright


DEFAULT_EDGE_DIR = str(Path.home() / "AppData" / "Local" / "Microsoft" / "Edge" / "User Data")
EDGE_USER_DATA_DIR = os.environ.get("EDGE_USER_DATA_DIR", DEFAULT_EDGE_DIR)

OUT_DIR = Path(__file__).resolve().parents[3] / "session"
OUT_PATH = OUT_DIR / "yandex_storage.json"


async def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        ctx = await pw.chromium.launch_persistent_context(
            EDGE_USER_DATA_DIR,
            channel="msedge",
            headless=False,
            viewport={"width": 1440, "height": 900},
            args=["--profile-directory=Default"],
        )
        page = await ctx.new_page()
        await page.goto("https://alice.yandex.ru/", wait_until="domcontentloaded")
        # Warm cookies for yandex.ru + passport
        await page.wait_for_timeout(5000)
        try:
            await page.goto("https://passport.yandex.ru/profile", wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
        except Exception:
            pass

        await ctx.storage_state(path=str(OUT_PATH))
        print(f"storage_state saved -> {OUT_PATH}")
        await ctx.close()


if __name__ == "__main__":
    asyncio.run(main())
