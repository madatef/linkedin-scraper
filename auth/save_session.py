"""
auth/save_session.py
────────────────────
Run this ONCE to log into LinkedIn and save the browser session.
The saved session is reused by the scraper so you don't need to
log in on every run (and don't trigger 2FA repeatedly).

Usage:
    python auth/save_session.py
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SESSION_FILE = Path(__file__).parent / "session.json"


async def save_session() -> None:
    print("=" * 55)
    print("  LinkedIn Session Saver")
    print("=" * 55)
    print("\nA browser window will open. Log into LinkedIn manually.")
    print("Once you're on the LinkedIn home feed, press ENTER here.\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        context = await browser.new_context(
            viewport=None,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        await page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")

        print("Waiting for you to log in…  (Press ENTER after you're on the feed)")
        await asyncio.get_event_loop().run_in_executor(None, input)

        # Verify we're actually logged in
        if "feed" in page.url or "mynetwork" in page.url or "jobs" in page.url:
            await context.storage_state(path=str(SESSION_FILE))
            print(f"\n✅  Session saved to: {SESSION_FILE}")
        else:
            print(
                "\n⚠️  Doesn't look like you're on the LinkedIn feed yet. "
                "Please finish logging in and re-run this script."
            )

        await browser.close()


if __name__ == "__main__":
    asyncio.run(save_session())
