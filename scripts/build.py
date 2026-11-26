#!/usr/bin/env python3
"""Build the static site into _site/.

_site/                 published editions only (status: published, or draft + audit PASS when AUTO_PUBLISH=true)
_site/preview/         every valid edition including drafts (noindex, banner) for the owner to review
Editions that fail validation are skipped and listed in build/report.md.
"""
import argparse
import datetime
import html
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

import markdown

sys.path.insert(0, str(Path(__file__).parent))
import ked  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SITE_TITLE = "ದಿನದ ಓದು"
SITE_SUB = "Karnataka Exams Daily"
WEEKDAYS = ["ಸೋಮವಾರ", "ಮಂಗಳವಾರ", "ಬುಧವಾರ", "ಗುರುವಾರ", "ಶುಕ್ರವಾರ", "ಶನಿವಾರ", "ಭಾನುವಾರ"]
L = {
    "lesson": "ಇಂದಿನ ವಿಷಯ", "news": "ಇಂದಿನ ಸುದ್ದಿ", "remember": "ನೆನಪಿಡಿ", "practice": "ಅಭ್ಯಾಸ",
    "deeper": "ಹೆಚ್ಚಿನ ಆಳ (ಐಚ್ಛಿಕ)", "prev": "← ಹಿಂದಿನ", "next": "ಮುಂದಿನ →", "archive": "ಆರ್ಕೈವ್",
    "source": "ಮೂಲ", "published": "ಪ್ರಕಟ", "event": "ಘಟನೆ", "answer": "ಸರಿಯಾದ ಉತ್ತರ", "why": "ವಿವರಣೆ",
    "core": "ಮೂಲ", "deep": "ಆಳ", "min": "ನಿಮಿಷ", "reviewed": "ಪರಿಶೀಲಿತ",
    "draft": "ಪರಿಶೀಲನೆ ಬಾಕಿ: ಇದು ಪ್ರಕಟಿತ ಆವೃತ್ತಿಯಲ್ಲ (owner preview only)",
    "none": "ಇನ್ನೂ ಯಾವುದೇ ಆವೃತ್ತಿ ಪ್ರಕಟವಾಗಿಲ್ಲ.", "all": "ಎಲ್ಲಾ", "pick": "ದಿನಾಂಕ ಆಯ್ಕೆ",
    "disclaimer": "ಈ ಓದು AI ಸಹಾಯದಿಂದ ತಯಾರಾಗಿದೆ ಮತ್ತು ಅಧಿಕೃತ ಮೂಲಗಳೊಂದಿಗೆ ಹೊಂದಿಸಲು ಪ್ರಯತ್ನಿಸಲಾಗಿದೆ. "
                  "ಪರೀಕ್ಷೆಗೆ ಮುನ್ನ ಸಂಬಂಧಿತ ಅಧಿಕೃತ ಅಧಿಸೂಚನೆ ಮತ್ತು ಪಠ್ಯಕ್ರಮವನ್ನು ತಪ್ಪದೆ ನೋಡಿ. ವಿಷಯ ಯೋಜನೆ ಅಧಿಕೃತ ಪಠ್ಯಕ್ರಮವಲ್ಲ.",
    "disclaimer_en": "AI-assisted and checked against official sources where possible. Always confirm with the official notification and syllabus. "
                     "The topic plan is not an official syllabus.",
}


def esc(s):
    return html.escape(s or "", quote=True)


def md(text):
    text = (text or "").replace("<", "&lt;")
    h = markdown.markdown(text, extensions=["tables", "sane_lists"])
    h = re.sub(r"<img[^>]*>", "", h)
    h = re.sub(r'<a href="(?!https?://|#)[^"]*"', '<a href="#"', h)
    h = re.sub(r'<a href="(https?://[^"]*)"', r'<a rel="noopener noreferrer" target="_blank" href="\1"', h)
    return h


def safe_url(u):
    p = urlparse(u or "")
    return u if p.scheme == "https" and p.hostname else ""


def fmt_date(d):
    return "%s, %s" % (WEEKDAYS[d.weekday()], d.strftime("%d-%m-%Y"))


def page(title, body, root, preview=False, description=""):
    robots = '<meta name="robots" content="noindex,nofollow">' if preview else ""
    banner = '<div class="banner">%s</div>' % esc(L["draft"]) if preview else ""
    return """<!doctype html>
<html lang="kn"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title><meta name="description" content="%s">%s
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Kannada:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="%sassets/style.css"></head>
<body>%s%s
<footer><p>%s</p><p lang="en">%s</p></footer>
<script src="%sassets/app.js" defer></script></body></html>""" % (
        esc(title), esc(description), robots, root, banner, body, esc(L["disclaimer"]), esc(L["disclaimer_en"]), root)


def header(root, prefix, dates, current, preview):
    base = root + prefix
    opts = "".join('<option value="%se/%s/"%s>%s</option>' % (
        base, d, " selected" if d == current else "", esc(d)) for d in reversed(dates))
    prv = nxt = ""
    if current in dates:
        i = dates.index(current)
        if i > 0:
            prv = '<a class="btn" href="%se/%s/">%s</a>' % (base, dates[i - 1], L["prev"])
        if i < len(dates) - 1:
            nxt = '<a class="btn" href="%se/%s/">%s</a>' % (base, dates[i + 1], L["next"])
    sel = '<select id="datesel" aria-label="%s">%s</select>' % (esc(L["pick"]), opts) if dates else ""
    return ('<header><a class="brand" href="%s">%s <small>%s</small></a>'
            '<nav>%s%s%s<a class="btn" href="%sarchive/">%s</a></nav></header>') % (
        base or "./", SITE_TITLE, SITE_SUB, prv, sel, nxt, base, L["archive"])


def mcq_html(mcqs):
    out = []
    for i, q in enumerate(mcqs, 1):
        opts = "".join('<li><button type="button" data-opt="%s"><b>%s)</b> %s</button></li>' % (
            k, k, esc(q["options"][k])) for k in "ABCD")
        lvl = L["core"] if q["level"] == "core" else L["deep"]
        out.append(
            '<div class="mcq" data-answer="%s"><p class="q"><span class="lvl">%s</span> %d. %s</p>'
            '<ul>%s</ul><div class="why" hidden><b>%s: %s</b><br>%s: %s</div></div>' % (
                q["answer"], lvl, i, esc(q["q"]), opts, L["answer"], q["answer"], L["why"], esc(q["why"])))
    return "".join(out)


def news_html(items, empty_text):
    if not items:
        return md(empty_text)
    out = []
    for n in items:
        s = n["source"] or {}
        url = safe_url(s.get("url"))
        src = ""
        if url:
            src = '<p class="src">%s: <a rel="noopener noreferrer" target="_blank" href="%s">%s</a> · %s %s · %s %s</p>' % (
                L["source"], esc(url), esc(s.get("name", "")), L["published"], esc(s.get("published", "")),
                L["event"], esc(s.get("event", "")))
        out.append('<article class="news"><h3>%s</h3>%s%s</article>' % (esc(n["title"]), md(n["body"]), src))
    return "".join(out)


def edition_body(ed, status, preview, root, prefix, dates):
    fm = ed["fm"]
    chips = "".join('<span class="chip">%s</span>' % esc(e) for e in ed["exams"])
    badge = '<span class="badge ok">%s ✓</span>' % L["reviewed"] if status == "published" else '<span class="badge warn">DRAFT</span>'
    deeper = ""
    if ed["deeper"]:
        deeper = '<details class="deeper"><summary>%s</summary>%s</details>' % (esc(L["deeper"]), md(ed["deeper"]))
    review = ""
    if preview:
        a = ed.get("audit")
        verdict = a["verdict"] if a else "NO AUDIT"
        review = ('<section id="review" class="review"><h2>Editor only</h2><p><b>Audit verdict:</b> %s</p>%s'
                  '<p><b>Words:</b> lesson %d, deeper %d, core total %d</p>%s</section>') % (
            esc(verdict), md(a["body"]) if a else "", ed["words"]["lesson"], ed["words"]["deeper"],
            ed["words"]["total_core"], md(ed["review"]))
    mins = "~%d %s" % (ed["read_min"], L["min"]) + (" (+%d)" % ed["deeper_min"] if ed["deeper_min"] else "")
    pills = "".join('<a href="#%s">%s</a>' % (k, esc(L[k])) for k in ("lesson", "news", "remember", "practice"))
    return """%s
<main><article class="edition">
<p class="meta">%s %s</p>
<h1>%s</h1>
<p class="sub">%s · %s · %s</p><p class="chips">%s</p>
<nav class="pills">%s</nav>
<section id="lesson"><h2>1 · %s</h2>%s%s</section>
<section id="news"><h2>2 · %s</h2>%s</section>
<section id="remember"><h2>3 · %s</h2>%s</section>
<section id="practice"><h2>4 · %s</h2>%s</section>%s
</article></main>""" % (
        header(root, prefix, dates, fm["date"], preview), esc(fmt_date(ed["date"])), badge,
        esc(fm["title_kn"]), esc(fm["topic_title"]), esc(fm["topic_id"]), esc(mins), chips, pills,
        L["lesson"], md(ed["lesson"]), deeper, L["news"], news_html(ed["news"], "ಇಂದು ಪರೀಕ್ಷೆಗೆ ಸಂಬಂಧಿಸಿದ ಹೊಸ ಸುದ್ದಿ ಆಯ್ಕೆಯಾಗಿಲ್ಲ."),
        L["remember"], md(ed["remember"]), L["practice"], mcq_html(ed["mcqs"]), review)


def build_tree(eds, out, prefix, preview, site_url):
    """eds: list of (status, ed) sorted by date. prefix: '' or 'preview/'. Writes pages under out/prefix."""
    base_dir = out / prefix if prefix else out
    dates = [e["fm"]["date"] for _, e in eds]
    depth_root = "../" * (prefix.count("/"))  # path from the tree's index to the site root
    for status, ed in eds:
        d = ed["fm"]["date"]
        root = depth_root + "../../"
        body = edition_body(ed, status, preview, root, prefix, dates)
        p = base_dir / "e" / d
        p.mkdir(parents=True, exist_ok=True)
        (p / "index.html").write_text(page("%s · %s" % (ed["fm"]["title_kn"], d), body, root, preview,
                                           ed["fm"]["topic_title"]), encoding="utf-8")
    # tree index = latest edition
    if eds:
        status, ed = eds[-1]
        root = depth_root
        body = edition_body(ed, status, preview, root, prefix, dates)
        html_ = page("%s · %s" % (SITE_TITLE, ed["fm"]["title_kn"]), body, root, preview, ed["fm"]["topic_title"])
    else:
        root = depth_root
        body = "%s<main><p>%s</p></main>" % (header(root, prefix, [], "", preview), esc(L["none"]))
        html_ = page(SITE_TITLE, body, root, preview)
    base_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / "index.html").write_text(html_, encoding="utf-8")
    # archive
    root = depth_root + "../"
    months = {}
    for status, ed in reversed(eds):
        months.setdefault(ed["fm"]["date"][:7], []).append((status, ed))
    codes = sorted({c for _, e in eds for c in e["exams"]})
    chips = '<p class="chips filter"><button type="button" data-exam="" class="on">%s</button>%s</p>' % (
        L["all"], "".join('<button type="button" data-exam="%s">%s</button>' % (esc(c), esc(c)) for c in codes))
    rows = []
    for m, lst in months.items():
        rows.append("<h2>%s</h2><ul class=\"list\">" % esc(m))
        for status, ed in lst:
            fm = ed["fm"]
            rows.append('<li data-exams="%s"><a href="%se/%s/"><b>%s</b> %s</a> <small>%s · %s</small>%s</li>' % (
                esc(",".join(ed["exams"])), "../", fm["date"],
                esc(fm["date"]), esc(fm["title_kn"]), esc(fm["topic_title"]), esc(fm["topic_id"]),
                "" if status == "published" else ' <span class="badge warn">DRAFT</span>'))
        rows.append("</ul>")
    aroot = ("../" * (prefix.count("/"))) + "../"
    body = "%s<main><h1>%s</h1>%s%s</main>" % (
        header(aroot, prefix, dates, "", preview), esc(L["archive"]), chips if eds else "", "".join(rows) or esc(L["none"]))
    (base_dir / "archive").mkdir(parents=True, exist_ok=True)
    (base_dir / "archive" / "index.html").write_text(page(L["archive"] + " · " + SITE_TITLE, body, aroot, preview), encoding="utf-8")


def feed(eds, site_url, out):
    items = []
    for status, ed in reversed(eds[-30:]):
        fm = ed["fm"]
        items.append("<item><title>%s</title><link>%se/%s/</link><guid>%se/%s/</guid><pubDate>%s</pubDate><description>%s</description></item>" % (
            esc(fm["title_kn"]), site_url, fm["date"], site_url, fm["date"],
            ed["date"].strftime("%a, %d %b %Y 05:30:00 +0530"), esc(fm["topic_title"])))
    (out / "feed.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>%s</title><link>%s</link>'
        "<description>Karnataka Exams Daily</description>%s</channel></rss>" % (SITE_TITLE, site_url, "".join(items)),
        encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", default=str(ROOT / "content"))
    ap.add_argument("--plan", default=str(ROOT / "data" / "plan.json"))
    ap.add_argument("--sources", default=str(ROOT / "data" / "sources.json"))
    ap.add_argument("--out", default=str(ROOT / "_site"))
    ap.add_argument("--site-url", default=os.environ.get("SITE_URL", "./"))
    a = ap.parse_args()
    auto = os.environ.get("AUTO_PUBLISH", "").lower() == "true"
    plan, sources = ked.load_json(a.plan), ked.load_json(a.sources)
    results = ked.validate_all(a.content, plan, sources)
    out = Path(a.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copytree(ROOT / "site" / "assets", out / "assets")
    good = [r["ed"] for r in results if r["ed"]]
    good.sort(key=lambda e: e["fm"]["date"])
    tagged = []
    for ed in good:
        st = ed["fm"]["status"]
        if st != "published" and auto and ed.get("audit") and ed["audit"]["verdict"] == "PASS":
            st = "published"
        tagged.append((st, ed))
    published = [(s, e) for s, e in tagged if s == "published"]
    build_tree(published, out, "", False, a.site_url)
    build_tree(tagged, out, "preview/", True, a.site_url)
    feed(published, a.site_url, out)
    (out / ".nojekyll").write_text("", encoding="utf-8")
    (out / "robots.txt").write_text("User-agent: *\nDisallow: /preview/\n", encoding="utf-8")
    bad = [r for r in results if r["errors"]]
    print("built: %d published, %d total valid, %d invalid" % (len(published), len(tagged), len(bad)))
    for r in bad:
        print("  SKIPPED %s: %s" % (r["name"], "; ".join(r["errors"])))


if __name__ == "__main__":
    main()
