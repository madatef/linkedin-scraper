# 🔍 LinkedIn Job Scraper

A Python + Playwright project that finds LinkedIn job posts based on your filters and saves all application form fields to structured Markdown files — for both **LinkedIn Easy Apply** and **External Application** forms.

---

## ✨ Features

- 🔍 **Filter by** keywords, location, experience level, job type, date posted, Easy Apply only
- 🟢 **Easy Apply** — walks through every modal step without submitting, extracts all fields
- 🔵 **External Forms** — follows external links and auto-detects ATS platform:
  - Greenhouse, Lever, Workday, Ashby + Generic fallback
- 📋 **Markdown output** — one `.md` file per job (or a single summary file)
- 🕵️ **Anti-detection** — stealth JS patches, human-like delays, session reuse, headed mode

---

## 🗂 Project Structure

```
linkedin_scraper/
├── auth/
│   └── save_session.py       # One-time LinkedIn login → saves session
├── config/
│   └── config.yaml           # All filters and settings
├── scraper/
│   ├── browser.py            # Stealth browser context builder
│   ├── job_search.py         # LinkedIn search + pagination
│   ├── easy_apply.py         # Easy Apply modal field extractor
│   ├── external_apply.py     # External ATS form extractor
│   └── markdown_writer.py    # Markdown renderer + file writer
├── output/                   # Generated .md files go here
│   └── EXAMPLE_OUTPUT.md     # Sample of what output looks like
├── main.py                   # Entry point
├── requirements.txt
└── README.md
```

---

## ⚡ Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Save your LinkedIn session (run once)

```bash
python auth/save_session.py
```

A browser will open. Log into LinkedIn normally. Press **Enter** in the terminal once you're on the feed. Your session will be saved to `auth/session.json`.

> You only need to do this once. The session is reused automatically. Re-run it if you get login errors.

### 3. Configure your filters

Edit `config/config.yaml`:

```yaml
search:
  keywords:
    - "AI Engineer"
    - "Data Scientist"
  location: "Egypt"
  easy_apply_only: false
  date_posted: "week"
  experience_levels:
    - "mid"
    - "senior"
  max_jobs: 20
```

### 4. Run the scraper

```bash
python main.py
```

Results are saved to the `output/` directory.

---

## 📄 Output Format

Each job gets a `.md` file like `ai_engineer_techcorp.md`:

```markdown
# AI Engineer — Backend Systems
> Company: TechCorp | Location: Cairo | Easy Apply

## Application Form Fields

### 1. Phone Number `required`
| Type | Text Input |
| Required | Yes ✅ |

### 2. Years of Experience `required`
| Type | Dropdown Select |
| Options | `1-2 years` · `3-5 years` · `5-10 years` |
...
```

See `output/EXAMPLE_OUTPUT.md` for a full example.

---

## ⚙️ Config Reference

| Key | Description | Default |
|-----|-------------|---------|
| `search.keywords` | List of search terms | — |
| `search.location` | City/country or "Remote" | — |
| `search.remote` | Remote jobs only | `false` |
| `search.easy_apply_only` | LinkedIn Easy Apply only | `false` |
| `search.date_posted` | `day` / `week` / `month` / `any` | `week` |
| `search.experience_levels` | `entry`, `mid`, `senior`, etc. | all |
| `search.job_types` | `full_time`, `contract`, etc. | all |
| `search.max_jobs` | Max listings per keyword | `20` |
| `scraper.headless` | Run without visible browser | `false` |
| `scraper.slow_mo_ms` | Delay between actions (ms) | `150` |
| `output.one_file_per_job` | One file per job vs. summary | `true` |

---

## 🛡 Anti-Detection Notes

- **Keep `headless: false`** — LinkedIn is aggressive against headless browsers
- The scraper injects stealth JS to hide `navigator.webdriver`
- Human-like random delays are added between all actions
- Session reuse avoids repeated logins which can trigger 2FA
- Avoid setting `max_jobs` above 50 in a single run

---

## ⚠️ Disclaimer

This tool is intended for **personal job search use only**. Automated scraping may violate LinkedIn's Terms of Service. Use responsibly: run it slowly, don't share sessions, and don't use it for bulk data collection.
