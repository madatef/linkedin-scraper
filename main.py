"""Entry point for the LinkedIn Job Scraper."""

from __future__ import annotations

import asyncio
from pathlib import Path

import yaml
from playwright.async_api import async_playwright

from scraper.browser import build_context
from scraper.job_search import search_jobs
from scraper.easy_apply import extract_easy_apply_fields
from scraper.external_apply import extract_external_fields
from scraper.markdown_writer import save_job_markdown, save_summary_markdown

CONFIG_PATH = Path(__file__).parent / "config" / "config.yaml"


def load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


async def run() -> None:
    cfg = load_config()

    print("\n" + "=" * 60)
    print("  🚀  LinkedIn Job Scraper")
    print("=" * 60)
    print(f"  Keywords : {', '.join(cfg['search']['keywords'])}")
    print(f"  Location : {cfg['search'].get('location', 'Any')}")
    print(f"  Max jobs : {cfg['search'].get('max_jobs', 20)}")
    print(f"  Output   : {cfg['output']['dir']}/")
    print("=" * 60 + "\n")

    all_results: list[tuple] = []

    async with async_playwright() as pw:
        browser, context = await build_context(pw, cfg)

        try:
            async for job in search_jobs(context, cfg):
                print(f"\n📌  Processing: {job.title} @ {job.company}")
                fields = []

                if job.is_easy_apply:
                    print("   → Extracting Easy Apply form…")
                    fields = await extract_easy_apply_fields(context, job.url)
                else:
                    if not job.external_url:
                        print("   → No external URL captured; skipping form extraction.")
                    else:
                        print(f"   → Extracting external form: {job.external_url[:60]}…")
                        fields = await extract_external_fields(context, job.external_url)

                if cfg["output"]["one_file_per_job"]:
                    filepath = save_job_markdown(job, fields, cfg)
                    print(f"   💾  Saved → {filepath}")
                    all_results.append((job, fields, filepath))
                else:
                    all_results.append((job, fields, None))

            if not cfg["output"]["one_file_per_job"] and all_results:
                summary_path = save_summary_markdown(all_results, cfg)
                print(f"\n💾  Summary saved → {summary_path}")

        finally:
            await browser.close()

    total = len(all_results)
    easy = sum(1 for job, _, _ in all_results if job.is_easy_apply)
    external = total - easy

    print("\n" + "=" * 60)
    print(f"  ✅  Done!  {total} jobs processed")
    print(f"      🟢 Easy Apply : {easy}")
    print(f"      🔵 External   : {external}")
    print(f"      📁 Output     : {Path(cfg['output']['dir']).resolve()}/")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run())
