"""Generates TEST-ONLY fixture editions with dummy text (no real facts). Not used in production."""
import sys
from pathlib import Path
out = Path(sys.argv[1]); (out / "editions").mkdir(parents=True, exist_ok=True); (out / "audits").mkdir(exist_ok=True)
filler = lambda n: " ".join(["ಪರೀಕ್ಷಾ"] * n)

def mcq(i, lvl, ans="B"):
    return f"### MCQ {i}\nQ: ಪರೀಕ್ಷಾ ಪ್ರಶ್ನೆ {i}\nA) ಆಯ್ಕೆ ಒಂದು\nB) ಆಯ್ಕೆ ಎರಡು\nC) ಆಯ್ಕೆ ಮೂರು\nD) ಆಯ್ಕೆ ನಾಲ್ಕು\nAnswer: {ans}\nWhy: ಪರೀಕ್ಷಾ ವಿವರಣೆ\nLevel: {lvl}\n"

def edition(date, topic, subject, status="draft", n_mcq=5, extra="", src_url="https://pib.gov.in/test", news=True):
    levels = ["core", "core", "core", "deeper", "deeper"][:n_mcq]
    mcqs = "\n".join(mcq(i + 1, l) for i, l in enumerate(levels))
    newsblock = (f"### ಪರೀಕ್ಷಾ ಸುದ್ದಿ\n{filler(60)}\n\nSource: PIB | {src_url} | published: {date} | event: {date} | link: {topic}\n") if news else "ಇಂದು ಹೊಸ ಸುದ್ದಿ ಇಲ್ಲ.\n"
    return f"""---
date: {date}
track: CORE
exams: KAS, FDA, SDA
subject: {subject}
topic_id: {topic}
topic_title: TEST FIXTURE ONLY
title_kn: ಪರೀಕ್ಷಾ ಮಾದರಿ (ಇದು ನಿಜವಾದ ವಿಷಯವಲ್ಲ)
read_minutes: 25
status: {status}
---
## ಇಂದಿನ ವಿಷಯ
{filler(1300)}

| ಕಾಲಂ ಒಂದು | ಕಾಲಂ ಎರಡು |
|---|---|
| ಮೌಲ್ಯ | ಮೌಲ್ಯ |

### ಹೆಚ್ಚಿನ ಆಳ
{filler(200)}
## ಇಂದಿನ ಸುದ್ದಿ
{newsblock}
## ನೆನಪಿಡಿ
- ಒಂದು
- ಎರಡು
- ಮೂರು
- ನಾಲ್ಕು
- ಐದು
## ಅಭ್ಯಾಸ
{mcqs}
{extra}
## ಪರಿಶೀಲನಾ ಟಿಪ್ಪಣಿ
- test note
"""
(out/"editions"/"2026-11-26_ECO-01.md").write_text(edition("2026-11-26","ECO-01","ECO","published"), encoding="utf-8")
(out/"editions"/"2026-11-27_SCI-01.md").write_text(edition("2026-11-27","SCI-01","SCI","draft"), encoding="utf-8")
(out/"editions"/"2026-11-28_KAR-01.md").write_text(edition("2026-11-28","KAR-01","KAR","draft", n_mcq=4), encoding="utf-8")            # should FAIL: 4 MCQs
(out/"editions"/"2026-11-29_REV-2026-48.md").write_text(edition("2026-11-29","REV-2026-48","REV","draft", extra="<script>alert(1)</script>"), encoding="utf-8")  # should FAIL: html
(out/"editions"/"2026-11-30_POL-01.md").write_text(edition("2026-11-30","POL-01","POL","draft", src_url="https://www.testbook.com/x"), encoding="utf-8")        # should FAIL: forbidden source
(out/"audits"/"2026-11-26_ECO-01_audit.md").write_text("---\nverdict: PASS\n---\nTest audit body.\n", encoding="utf-8")
