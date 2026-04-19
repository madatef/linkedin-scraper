"""Extracts form fields from external job application forms."""

from __future__ import annotations

import asyncio
import random
import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

from playwright.async_api import BrowserContext, Page


@dataclass
class FormField:
    label: str
    field_type: str
    required: bool
    options: list[str] = field(default_factory=list)
    placeholder: str = ""
    section: str = ""


async def _human_delay(min_s: float = 0.8, max_s: float = 2.0) -> None:
    await asyncio.sleep(random.uniform(min_s, max_s))


def _detect_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "greenhouse" in host or "grnh.se" in host:
        return "greenhouse"
    if "lever.co" in host:
        return "lever"
    if "myworkdayjobs" in host or "wd1.myworkdayjobs" in host:
        return "workday"
    if "ashbyhq" in host:
        return "ashby"
    return "generic"


async def _safe_text(el, page: Page = None) -> str:
    try:
        return (await el.inner_text()).strip()
    except Exception:
        return ""


async def _extract_generic_fields(page: Page, section: str = "") -> list[FormField]:
    fields: list[FormField] = []
    seen: set[str] = set()

    async def find_label(el) -> str:
        el_id = await el.get_attribute("id") or ""
        if el_id:
            lbl = await page.query_selector(f"label[for='{el_id}']")
            if lbl:
                return (await lbl.inner_text()).strip()
        aria = await el.get_attribute("aria-label") or ""
        if aria:
            return aria.strip()
        labelledby = await el.get_attribute("aria-labelledby") or ""
        if labelledby:
            lb = await page.query_selector(f"#{labelledby}")
            if lb:
                return (await lb.inner_text()).strip()
        try:
            p = await el.evaluate("el => el.closest('label')?.innerText?.trim() || ''")
            if p:
                return p
        except Exception:
            pass
        return ""

    for sel in [
        "form input:not([type='hidden']):not([type='submit']):not([type='button'])"
        ":not([type='radio']):not([type='checkbox']):not([type='file'])",
        "form textarea",
    ]:
        for inp in await page.query_selector_all(sel):
            tag = await inp.evaluate("el => el.tagName.toLowerCase()")
            label = await find_label(inp) or await inp.get_attribute("placeholder") or "Unlabeled"
            if label in seen:
                continue
            seen.add(label)
            required = (
                await inp.get_attribute("required") is not None
                or await inp.get_attribute("aria-required") == "true"
            )
            placeholder = await inp.get_attribute("placeholder") or ""
            ftype = "textarea" if tag == "textarea" else "text"
            fields.append(FormField(label=label, field_type=ftype, required=required, placeholder=placeholder, section=section))

    for sel in await page.query_selector_all("form select"):
        label = await find_label(sel) or "Unlabeled Select"
        if label in seen:
            continue
        seen.add(label)
        options = await sel.evaluate("el => Array.from(el.options).map(o => o.text.trim()).filter(Boolean)")
        required = await sel.get_attribute("required") is not None
        fields.append(FormField(label=label, field_type="select", required=required, options=options, section=section))

    radio_groups: dict[str, list[str]] = {}
    radio_req: dict[str, bool] = {}
    for radio in await page.query_selector_all("form input[type='radio']"):
        gname = await radio.get_attribute("name") or "radio"
        rid = await radio.get_attribute("id") or ""
        opt_label = ""
        if rid:
            lbl = await page.query_selector(f"label[for='{rid}']")
            if lbl:
                opt_label = (await lbl.inner_text()).strip()
        if not opt_label:
            opt_label = await radio.get_attribute("value") or "option"
        radio_groups.setdefault(gname, []).append(opt_label)
        radio_req.setdefault(gname, await radio.get_attribute("required") is not None)

    for gname, opts in radio_groups.items():
        legend = await page.query_selector(f"fieldset:has(input[name='{gname}']) legend")
        label = (await legend.inner_text()).strip() if legend else gname
        if label in seen:
            continue
        seen.add(label)
        fields.append(FormField(label=label, field_type="radio", required=radio_req.get(gname, False), options=opts, section=section))

    for cb in await page.query_selector_all("form input[type='checkbox']"):
        label = await find_label(cb) or "Checkbox"
        if label in seen:
            continue
        seen.add(label)
        required = await cb.get_attribute("required") is not None
        fields.append(FormField(label=label, field_type="checkbox", required=required, section=section))

    for fi in await page.query_selector_all("form input[type='file']"):
        label = await find_label(fi) or "File Upload"
        if label in seen:
            continue
        seen.add(label)
        accept = await fi.get_attribute("accept") or "*"
        required = await fi.get_attribute("required") is not None
        fields.append(FormField(label=label, field_type="file", required=required, placeholder=f"Accepted: {accept}", section=section))

    return fields


async def _extract_greenhouse(page: Page) -> list[FormField]:
    await page.wait_for_selector("#application_form, #application-form, form#application", timeout=15000)
    fields: list[FormField] = []

    field_divs = await page.query_selector_all(
        "#application_form .field, #application-form .field, form#application .field"
    )

    for div in field_divs:
        label_el = await div.query_selector("label")
        label = (await label_el.inner_text()).strip() if label_el else "Unlabeled"
        label = re.sub(r"\s*\*\s*$", "", label).strip()

        required_marker = await div.query_selector("abbr[title='required'], .required")
        required = required_marker is not None

        if await div.query_selector("input[type='file']"):
            accept = await (await div.query_selector("input[type='file']")).get_attribute("accept") or "*"
            fields.append(FormField(label=label, field_type="file", required=required, placeholder=f"Accepted: {accept}"))
        elif await div.query_selector("select"):
            sel = await div.query_selector("select")
            options = await sel.evaluate("el => Array.from(el.options).map(o => o.text.trim()).filter(Boolean)")
            fields.append(FormField(label=label, field_type="select", required=required, options=options))
        elif await div.query_selector("textarea"):
            fields.append(FormField(label=label, field_type="textarea", required=required))
        elif await div.query_selector("input[type='radio']"):
            radios = await div.query_selector_all("input[type='radio']")
            opts = []
            for r in radios:
                rid = await r.get_attribute("id") or ""
                lbl = await page.query_selector(f"label[for='{rid}']")
                opts.append((await lbl.inner_text()).strip() if lbl else await r.get_attribute("value") or "option")
            fields.append(FormField(label=label, field_type="radio", required=required, options=opts))
        elif await div.query_selector("input[type='checkbox']"):
            fields.append(FormField(label=label, field_type="checkbox", required=required))
        elif await div.query_selector("input"):
            ph = await (await div.query_selector("input")).get_attribute("placeholder") or ""
            fields.append(FormField(label=label, field_type="text", required=required, placeholder=ph))

    return fields


async def _extract_lever(page: Page) -> list[FormField]:
    await page.wait_for_selector(".application-form, form.application", timeout=15000)
    fields: list[FormField] = []

    groups = await page.query_selector_all(".application-form .application-group, form.application .form-group")

    for group in groups:
        label_el = await group.query_selector("label, .application-label")
        label = (await label_el.inner_text()).strip() if label_el else "Unlabeled"
        label = re.sub(r"\s*\*\s*$", "", label).strip()

        required_marker = await group.query_selector("[class*='required']")
        required = required_marker is not None or "*" in label

        if await group.query_selector("input[type='file']"):
            fields.append(FormField(label=label, field_type="file", required=required))
        elif await group.query_selector("select"):
            sel = await group.query_selector("select")
            options = await sel.evaluate("el => Array.from(el.options).map(o => o.text.trim()).filter(Boolean)")
            fields.append(FormField(label=label, field_type="select", required=required, options=options))
        elif await group.query_selector("textarea"):
            fields.append(FormField(label=label, field_type="textarea", required=required))
        elif await group.query_selector("input[type='radio']"):
            radios = await group.query_selector_all("input[type='radio']")
            opts = []
            for r in radios:
                rid = await r.get_attribute("id") or ""
                lbl = await page.query_selector(f"label[for='{rid}']")
                opts.append((await lbl.inner_text()).strip() if lbl else await r.get_attribute("value") or "option")
            fields.append(FormField(label=label, field_type="radio", required=required, options=opts))
        elif await group.query_selector("input"):
            ph = await (await group.query_selector("input")).get_attribute("placeholder") or ""
            fields.append(FormField(label=label, field_type="text", required=required, placeholder=ph))

    return fields


async def _extract_ashby(page: Page) -> list[FormField]:
    await page.wait_for_selector("form, [data-testid='application-form']", timeout=15000)
    return await _extract_generic_fields(page)


async def _extract_workday(page: Page) -> list[FormField]:
    try:
        await page.wait_for_selector(
            "[data-automation-id='legalNameSection'], "
            "[data-automation-id='contactInformationSection'], "
            "form",
            timeout=20000,
        )
    except Exception:
        pass
    await _human_delay(2, 4)
    return await _extract_generic_fields(page)


async def extract_external_fields(
    context: BrowserContext,
    external_url: str,
) -> list[FormField]:
    """Navigate to an external application URL, detect the ATS platform, extract all form fields."""
    page = await context.new_page()
    fields: list[FormField] = []

    try:
        await page.goto(external_url, wait_until="domcontentloaded")
        await _human_delay(2, 3)

        platform = _detect_platform(page.url)
        print(f"     🌐  External platform detected: {platform.upper()}  ({page.url[:60]}…)")

        if platform == "greenhouse":
            fields = await _extract_greenhouse(page)
        elif platform == "lever":
            fields = await _extract_lever(page)
        elif platform == "workday":
            fields = await _extract_workday(page)
        elif platform == "ashby":
            fields = await _extract_ashby(page)
        else:
            fields = await _extract_generic_fields(page)

        print(f"     📋  {len(fields)} field(s) found on external form")

    except Exception as exc:
        print(f"     ❌  Error extracting external form: {exc}")

    finally:
        await page.close()

    return fields
