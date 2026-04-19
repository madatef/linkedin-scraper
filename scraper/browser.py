"""Builds a stealth Playwright browser context that reuses the saved LinkedIn session."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Playwright,
    async_playwright,
)

SESSION_FILE = Path(__file__).parent.parent / "auth" / "session.json"

_USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
]

_STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
window.chrome = { runtime: {} };
"""


async def build_context(
    playwright: Playwright,
    cfg: dict,
) -> tuple[Browser, BrowserContext]:
    """Launch browser + return a stealth context with the saved session."""

    if not SESSION_FILE.exists():
        raise FileNotFoundError(
            f"Session file not found at {SESSION_FILE}.\n"
            "Run  python auth/save_session.py  first."
        )

    browser = await playwright.chromium.launch(
        headless=cfg["scraper"]["headless"],
        slow_mo=cfg["scraper"]["slow_mo_ms"],
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--start-maximized",
        ],
    )

    context = await browser.new_context(
        storage_state=str(SESSION_FILE),
        viewport={"width": 1440, "height": 900},
        user_agent=random.choice(_USER_AGENTS),
        locale="en-US",
        timezone_id="Africa/Cairo",
    )

    await context.add_init_script(_STEALTH_SCRIPT)
    context.set_default_timeout(cfg["scraper"]["page_timeout_ms"])

    return browser, context
