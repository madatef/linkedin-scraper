"""Builds LinkedIn job-search URLs from config filters and yields JobListing objects."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import AsyncIterator
from urllib.parse import urlencode

from playwright.async_api import BrowserContext, Page

_EXPERIENCE_MAP = {
    "internship": "1",
    "entry": "2",
    "mid": "3",
    "senior": "4",
    "director": "5",
    "executive": "6",
}

_JOB_TYPE_MAP = {
    "full_time": "F",
    "part_time": "P",
    "contract": "C",
    "temporary": "T",
    "volunteer": "V",
    "internship": "I",
}

_DATE_MAP = {
    "day": "r86400",
    "week": "r604800",
    "month": "r2592000",
    "any": "",
}


@dataclass
class JobListing:
    title: str
    company: str
    location: str
    job_id: str
    url: str
    is_easy_apply: bool
    external_url: str | None = None


def _build_search_url(keyword: str, cfg: dict, start: int = 0) -> str:
    search_cfg = cfg["search"]

    params: dict[str, str] = {
        "keywords": keyword,
        "location": search_cfg.get("location", ""),
        "start": str(start),
    }

    if search_cfg.get("remote"):
        params["f_WT"] = "2"

    if search_cfg.get("easy_apply_only"):
        params["f_LF"] = "f_AL"

    date_key = search_cfg.get("date_posted", "any")
    if date_code := _DATE_MAP.get(date_key, ""):
        params["f_TPR"] = date_code

    exp_codes = [
        _EXPERIENCE_MAP[e]
        for e in search_cfg.get("experience_levels", [])
        if e in _EXPERIENCE_MAP
    ]
    if exp_codes:
        params["f_E"] = ",".join(exp_codes)

    type_codes = [
        _JOB_TYPE_MAP[t]
        for t in search_cfg.get("job_types", [])
        if t in _JOB_TYPE_MAP
    ]
    if type_codes:
        params["f_JT"] = ",".join(type_codes)

    return f"https://www.linkedin.com/jobs/search/?{urlencode(params)}"


async def _human_delay(min_s: float, max_s: float) -> None:
    await asyncio.sleep(random.uniform(min_s, max_s))


async def _scroll_down(page):
    await page.evaluate("""
        async () => {
            await new Promise((resolve) => {
                let totalHeight = 0;
                const distance = 400;
                const timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    totalHeight += distance;

                    if (totalHeight >= document.body.scrollHeight){
                        clearInterval(timer);
                        resolve();
                    }
                }, 300);
            });
        }
    """)


async def search_jobs(
    context: BrowserContext,
    cfg: dict,
) -> AsyncIterator[JobListing]:
    """Async generator that yields JobListing for every result found."""
    search_cfg = cfg["search"]
    delay_cfg = cfg["scraper"]["between_jobs_delay"]
    page_delay_cfg = cfg["scraper"]["between_pages_delay"]
    max_jobs: int = search_cfg.get("max_jobs", 20)

    page = await context.new_page()

    for keyword in search_cfg["keywords"]:
        print(f"\n🔍  Searching: '{keyword}' in '{search_cfg.get('location', '')}'")
        collected = 0
        start = 0

        while collected < max_jobs:
            url = _build_search_url(keyword, cfg, start)
            print(f"   → Page offset {start}: {url}")

            await page.goto(url, wait_until="domcontentloaded")
            await _scroll_down(page)

            try:
                await page.wait_for_selector("li[data-occludable-job-id]", timeout=15000)
            except Exception as e:
                print("   ⚠️  No job cards found on this page — stopping pagination.")
                print(f"reason: {e}")
                break

            cards = await page.query_selector_all("li[data-occludable-job-id]")

            if not cards:
                print("   ⚠️  Empty results page — stopping pagination.")
                break

            for card in cards:
                if collected >= max_jobs:
                    break

                try:
                    await card.click(delay=127)
                    await asyncio.sleep(random.uniform(1.0, 2.0))

                    title_el = await page.query_selector(
                        "div.job-details-jobs-unified-top-card__job-title h1 a"
                    )
                    title = (
                        (await title_el.inner_text()).strip()
                        if title_el
                        else "Unknown Title"
                    )

                    company_el = await page.query_selector(
                        "div.job-details-jobs-unified-top-card__company-name a"
                    )
                    company = (
                        (await company_el.inner_text()).strip()
                        if company_el
                        else "Unknown Company"
                    )

                    location_el = await page.query_selector(
                        "div.job-details-jobs-unified-top-card__tertiary-description-container span span,"
                        "span.jobs-unified-top-card__workplace-type"
                    )
                    location = (
                        (await location_el.inner_text()).strip()
                        if location_el
                        else ""
                    )

                    job_url = page.url
                    job_id = ""
                    if "/jobs/view/" in job_url:
                        job_id = job_url.split("/jobs/view/")[1].split("/")[0]

                    easy_apply_btn = await page.query_selector(
                        "button.jobs-apply-button[aria-label*='Easy Apply'],"
                        "button.jobs-apply-button span:text('Easy Apply')"
                    )
                    is_easy = easy_apply_btn is not None

                    external_url: str | None = None
                    if not is_easy:
                        ext_btn = await page.query_selector(
                            "button.jobs-apply-button"
                        )
                        if ext_btn:
                            async with page.expect_popup() as popup_ctx:
                                await ext_btn.click(delay=127)
                            popup = await popup_ctx.value
                            await popup.wait_for_load_state("networkidle")
                            external_url = popup.url
                            await popup.close()

                    listing = JobListing(
                        title=title,
                        company=company,
                        location=location,
                        job_id=job_id,
                        url=job_url,
                        is_easy_apply=is_easy,
                        external_url=external_url,
                    )

                    print(
                        f"   {'🟢' if is_easy else '🔵'}  [{collected + 1}] "
                        f"{title} @ {company}"
                        f"  ({'Easy Apply' if is_easy else 'External'})"
                    )
                    collected += 1
                    yield listing

                    await _human_delay(
                        delay_cfg["min"], delay_cfg["max"]
                    )

                except Exception as exc:
                    print(f"   ⚠️  Skipping card due to error: {exc}")
                    continue

            start += 25
            await _human_delay(page_delay_cfg["min"], page_delay_cfg["max"])

    await page.close()
