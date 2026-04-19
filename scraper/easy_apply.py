"""Extracts form fields from LinkedIn Easy Apply modals."""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from typing import Optional

from playwright.async_api import BrowserContext, Page


@dataclass
class FormField:
    step: int
    label: str
    field_type: str
    required: bool
    options: list[str] = field(default_factory=list)
    placeholder: str = ""
    name: str = ""


async def _human_delay(min_s: float = 0.5, max_s: float = 1.2) -> None:
    await asyncio.sleep(random.uniform(min_s, max_s))


async def _extract_fields_from_step(page: Page, step_number: int) -> list[FormField]:
    """Parse all form fields visible in the current modal step."""
    fields: list[FormField] = []

    inputs = await page.query_selector_all(
        ".jobs-easy-apply-modal input:not([type='hidden']):not([type='submit']),"
        ".jobs-easy-apply-modal textarea"
    )
    for inp in inputs:
        tag = await inp.evaluate("el => el.tagName.toLowerCase()")
        inp_type = (await inp.get_attribute("type") or "text").lower()
        if inp_type in ("hidden", "submit", "button"):
            continue

        name = await inp.get_attribute("name") or await inp.get_attribute("id") or ""
        placeholder = await inp.get_attribute("placeholder") or ""
        label = await _find_label(page, inp)

        required_attr = await inp.get_attribute("required")
        aria_required = await inp.get_attribute("aria-required")
        required = required_attr is not None or aria_required == "true"

        field_type = "textarea" if tag == "textarea" else "text"

        fields.append(FormField(
            step=step_number,
            label=label,
            field_type=field_type,
            required=required,
            placeholder=placeholder,
            name=name,
        ))

    selects = await page.query_selector_all(".jobs-easy-apply-modal select")
    for sel in selects:
        label = await _find_label(page, sel)
        options = await sel.evaluate(
            "el => Array.from(el.options).map(o => o.text.trim()).filter(t => t)"
        )
        required_attr = await sel.get_attribute("required")
        aria_required = await sel.get_attribute("aria-required")
        required = required_attr is not None or aria_required == "true"
        name = await sel.get_attribute("name") or ""

        fields.append(FormField(
            step=step_number,
            label=label,
            field_type="select",
            required=required,
            options=options,
            name=name,
        ))

    radio_groups: dict[str, list[str]] = {}
    radio_required: dict[str, bool] = {}
    radios = await page.query_selector_all(
        ".jobs-easy-apply-modal input[type='radio']"
    )
    for radio in radios:
        group_name = await radio.get_attribute("name") or "radio_unknown"
        value = await radio.get_attribute("value") or ""

        radio_id = await radio.get_attribute("id") or ""
        option_label = ""
        if radio_id:
            lbl = await page.query_selector(f"label[for='{radio_id}']")
            if lbl:
                option_label = (await lbl.inner_text()).strip()
        if not option_label:
            option_label = value

        if group_name not in radio_groups:
            radio_groups[group_name] = []
            required_attr = await radio.get_attribute("required")
            aria_required = await radio.get_attribute("aria-required")
            radio_required[group_name] = (
                required_attr is not None or aria_required == "true"
            )

        radio_groups[group_name].append(option_label)

    for group_name, options in radio_groups.items():
        group_label = group_name
        legend = await page.query_selector(
            f"fieldset:has(input[name='{group_name}']) legend"
        )
        if legend:
            group_label = (await legend.inner_text()).strip()

        fields.append(FormField(
            step=step_number,
            label=group_label,
            field_type="radio",
            required=radio_required.get(group_name, False),
            options=options,
            name=group_name,
        ))

    checkboxes = await page.query_selector_all(
        ".jobs-easy-apply-modal input[type='checkbox']"
    )
    for cb in checkboxes:
        label = await _find_label(page, cb)
        required_attr = await cb.get_attribute("required")
        required = required_attr is not None
        name = await cb.get_attribute("name") or ""

        fields.append(FormField(
            step=step_number,
            label=label,
            field_type="checkbox",
            required=required,
            name=name,
        ))

    file_inputs = await page.query_selector_all(
        ".jobs-easy-apply-modal input[type='file']"
    )
    for fi in file_inputs:
        label = await _find_label(page, fi)
        required_attr = await fi.get_attribute("required")
        required = required_attr is not None
        accept = await fi.get_attribute("accept") or "*"

        fields.append(FormField(
            step=step_number,
            label=label or "File Upload",
            field_type="file",
            required=required,
            placeholder=f"Accepted: {accept}",
        ))

    custom_fields = await page.query_selector_all(
        ".jobs-easy-apply-modal .fb-dash-form-element"
    )
    seen_labels = {f.label for f in fields}
    for cf in custom_fields:
        label_el = await cf.query_selector("label, legend")
        if not label_el:
            continue
        label_text = (await label_el.inner_text()).strip()
        if label_text in seen_labels:
            continue

        has_select = await cf.query_selector("select")
        has_radio = await cf.query_selector("input[type='radio']")
        has_file = await cf.query_selector("input[type='file']")
        has_textarea = await cf.query_selector("textarea")

        if has_select:
            ftype = "select"
        elif has_radio:
            ftype = "radio"
        elif has_file:
            ftype = "file"
        elif has_textarea:
            ftype = "textarea"
        else:
            ftype = "text"

        required_el = await cf.query_selector("[required], [aria-required='true']")
        required_marker = await cf.query_selector(
            "span[aria-hidden='true']:text('*'), .required"
        )
        required = required_el is not None or required_marker is not None

        fields.append(FormField(
            step=step_number,
            label=label_text,
            field_type=ftype,
            required=required,
        ))
        seen_labels.add(label_text)

    return fields


async def _find_label(page: Page, element) -> str:
    """Try multiple strategies to find the label for a form element."""
    el_id = await element.get_attribute("id") or ""
    if el_id:
        lbl = await page.query_selector(f"label[for='{el_id}']")
        if lbl:
            return (await lbl.inner_text()).strip()

    aria_label = await element.get_attribute("aria-label") or ""
    if aria_label:
        return aria_label.strip()

    labelledby = await element.get_attribute("aria-labelledby") or ""
    if labelledby:
        lbl_el = await page.query_selector(f"#{labelledby}")
        if lbl_el:
            return (await lbl_el.inner_text()).strip()

    try:
        parent_label = await element.evaluate(
            "el => el.closest('label')?.innerText?.trim() || ''"
        )
        if parent_label:
            return parent_label
    except Exception:
        pass

    try:
        prev_label = await element.evaluate(
            """el => {
                let sib = el.previousElementSibling;
                while (sib) {
                    if (sib.tagName === 'LABEL') return sib.innerText.trim();
                    sib = sib.previousElementSibling;
                }
                return '';
            }"""
        )
        if prev_label:
            return prev_label
    except Exception:
        pass

    return "Unlabeled Field"


async def extract_easy_apply_fields(
    context: BrowserContext,
    job_url: str,
) -> list[FormField]:
    """Open the job page, click Easy Apply, walk all modal steps, collect fields, then cancel."""
    page = await context.new_page()
    all_fields: list[FormField] = []

    try:
        await page.goto(job_url, wait_until="domcontentloaded")
        await _human_delay(2, 3)

        easy_apply_btn = await page.query_selector(
            "button.jobs-apply-button[aria-label*='Easy Apply'],"
            "button.jobs-apply-button span:text('Easy Apply')"
        )
        if not easy_apply_btn:
            print("     ⚠️  Easy Apply button not found on detail page.")
            return []

        await easy_apply_btn.click(delay=127)
        await _human_delay(1.5, 2.5)

        try:
            await page.wait_for_selector(
                ".jobs-easy-apply-modal, .artdeco-modal",
                timeout=10000,
            )
        except Exception:
            print("     ⚠️  Easy Apply modal did not open.")
            return []

        step = 1
        max_steps = 15

        while step <= max_steps:
            await _human_delay(0.8, 1.5)

            step_fields = await _extract_fields_from_step(page, step)
            all_fields.extend(step_fields)
            print(f"     📋  Step {step}: {len(step_fields)} field(s) extracted")

            next_btn = await page.query_selector(
                "button[aria-label='Continue to next step'],"
                "button[aria-label='Review your application'],"
                "footer button.artdeco-button--primary"
            )

            if not next_btn:
                print(f"     ✅  No more steps found after step {step}.")
                break

            btn_text = (await next_btn.inner_text()).strip().lower()

            if btn_text in ("submit application", "submit", "review"):
                print(f"     ✅  Reached submit/review step — not submitting.")
                break

            await next_btn.click(delay=129)
            await _human_delay(1.0, 2.0)
            step += 1

    except Exception as exc:
        print(f"     ❌  Error during Easy Apply extraction: {exc}")

    finally:
        try:
            dismiss_btn = await page.query_selector(
                "button[aria-label='Dismiss'],"
                "button.artdeco-modal__dismiss,"
                "[data-test-modal-close-btn]"
            )
            if dismiss_btn:
                await dismiss_btn.click(delay=131)
                await _human_delay(0.5, 1.0)

                discard_btn = await page.query_selector(
                    "button[data-control-name='discard_application_confirm_btn'],"
                    "button:has-text('Discard')"
                )
                if discard_btn:
                    await discard_btn.click(delay=130)
        except Exception:
            pass

        await page.close()

    return all_fields
