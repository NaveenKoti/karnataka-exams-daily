# Karnataka Exams Daily (KED)

A daily Kannada-first reading edition (about 25 minutes) for Karnataka competitive exams. Gemini researches and writes, an independent Gemini task audits, Apps Script ingests into this repo, and GitHub Actions validates and builds a static site with date navigation.

## Pipeline
1. Gemini Task 1 (03:00 IST): research brief -> Drive `KED/briefs/`
2. Gemini Task 2 (04:00 IST): writes edition (status: draft) -> Drive `KED/editions/`
3. Gemini Task 3 (04:30 IST): audit with verdict PASS/PARTIAL/FAIL -> Drive `KED/audits/`
4. Apps Script (05:00 and 06:00 IST): copies new files into `content/editions/` and `content/audits/`, logs to a Sheet
5. GitHub Actions: validate -> build -> deploy to Pages. Invalid editions never reach the site.

## Publishing gate
Editions are `status: draft` and appear only under `/preview/` (noindex). Publish by changing the front matter to `status: published` after reading the audit, or set repo variable `AUTO_PUBLISH=true` to auto-promote editions whose audit verdict is PASS.

## Setup
1. Repo settings -> Pages -> Source: GitHub Actions.
2. Create a fine-grained PAT (Contents: read/write, this repo only).
3. Apps Script: paste `apps_script/Code.gs` and `appsscript.json`; set Script Properties (GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH, EDITIONS_FOLDER_ID, AUDITS_FOLDER_ID, LOG_SHEET_ID, ALERT_EMAIL); run `selfTest`, then `setupTriggers`.
4. Create the three Gemini scheduled actions from `gemini/*.md`.

## Local check
`python3 scripts/validate.py --content content --plan data/plan.json --sources data/sources.json --out build && python3 scripts/build.py`

See `docs/DESIGN.md` for the full design.
