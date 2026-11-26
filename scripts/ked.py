"""Parsing and validation for Karnataka Exams Daily editions.

An edition is one Markdown file: content/editions/YYYY-MM-DD_<TOPICID>.md
Validation is deliberately strict: an edition that fails is NOT published.
"""
import datetime
import json
import re
from pathlib import Path
from urllib.parse import urlparse

LESSON, NEWS, REMEMBER, PRACTICE = "ಇಂದಿನ ವಿಷಯ", "ಇಂದಿನ ಸುದ್ದಿ", "ನೆನಪಿಡಿ", "ಅಭ್ಯಾಸ"
SECTIONS = [LESSON, NEWS, REMEMBER, PRACTICE]
REVIEW = "ಪರಿಶೀಲನಾ ಟಿಪ್ಪಣಿ"
DEEPER = "ಹೆಚ್ಚಿನ ಆಳ"
REQUIRED_FM = ["date", "track", "exams", "subject", "topic_id", "topic_title",
               "title_kn", "read_minutes", "status"]
FILE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_([A-Z]+-[0-9A-Za-z-]+)\.md$")
AUDIT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_([A-Z]+-[0-9A-Za-z-]+)_audit\.md$")
WORD_RE = re.compile(r"[\u0C80-\u0CFF0-9A-Za-z]+")
DANGEROUS_RE = re.compile(
    r"<\s*/?\s*(script|iframe|object|embed|style|link|meta|img|svg|form|input|button|base)\b|javascript\s*:",
    re.I)
WEEKDAY_SUBJECT = {0: ["POL"], 1: ["HIS"], 2: ["GEO"], 3: ["ECO"], 4: ["ENV", "SCI"], 5: ["KAR"], 6: ["REV"]}

# word-count thresholds (Kannada words; Kannada text is whitespace separated)
LESSON_ERROR_BELOW = 400
LESSON_WARN_BELOW = 1200
TOTAL_WARN_BELOW = 2400


def words(text):
    return len(WORD_RE.findall(text or ""))


def normalise(text):
    t = text.replace("\r\n", "\n").replace("\ufeff", "").strip()
    m = re.match(r"^```[a-zA-Z]*\n(.*)\n```$", t, re.S)
    if m:
        t = m.group(1).strip()
    return t + "\n"


def split_front_matter(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None, text
    fm = {}
    for line in m.group(1).split("\n"):
        if not line.strip():
            continue
        if ":" not in line:
            raise ValueError("front matter line without ':' -> " + line[:60])
        k, v = line.split(":", 1)
        fm[k.strip()] = v.strip()
    return fm, m.group(2)


def split_sections(body):
    sections, order, cur = {}, [], None
    for line in body.split("\n"):
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            title = m.group(1)
            key = next((k for k in SECTIONS + [REVIEW] if title.startswith(k)), None)
            if key:
                cur = key
                order.append(key)
                sections[key] = []
                continue
        if cur:
            sections[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}, order


def split_deeper(lesson):
    m = re.search(r"^###\s+" + DEEPER + r".*$", lesson, re.M)
    if not m:
        return lesson, ""
    return lesson[:m.start()].strip(), lesson[m.end():].strip()


def parse_news(text):
    items = []
    parts = re.split(r"^###\s+", text, flags=re.M)
    for p in parts[1:]:
        title, _, rest = p.partition("\n")
        src = re.search(r"^Source:\s*(.+)$", rest, re.M)
        fields = None
        body = rest
        if src:
            segs = [s.strip() for s in src.group(1).split("|")]
            fields = {"segments": len(segs)}
            if len(segs) >= 2:
                fields["name"], fields["url"] = segs[0], segs[1]
            for s in segs[2:]:
                k, _, v = s.partition(":")
                fields[k.strip().lower()] = v.strip()
            body = rest[:src.start()] + rest[src.end():]
        items.append({"title": title.strip(), "body": body.strip(), "source": fields})
    return items


def parse_mcqs(text):
    out = []
    blocks = re.split(r"^###\s+MCQ\s*\d+\s*$", text, flags=re.M)[1:]
    for b in blocks:
        d = {"q": "", "options": {}, "answer": None, "why": "", "level": None}
        cur = None
        for line in b.split("\n"):
            s = line.strip()
            if not s:
                continue
            m = re.match(r"^Q:\s*(.*)$", s)
            if m:
                d["q"], cur = m.group(1), "q"
                continue
            m = re.match(r"^([A-D])\)\s*(.*)$", s)
            if m:
                d["options"][m.group(1)], cur = m.group(2), ("opt", m.group(1))
                continue
            m = re.match(r"^Answer:\s*\(?([A-D])\)?", s)
            if m:
                d["answer"], cur = m.group(1), None
                continue
            m = re.match(r"^Why:\s*(.*)$", s)
            if m:
                d["why"], cur = m.group(1), "why"
                continue
            m = re.match(r"^Level:\s*(core|deeper)", s, re.I)
            if m:
                d["level"], cur = m.group(1).lower(), None
                continue
            if cur == "q":
                d["q"] += " " + s
            elif cur == "why":
                d["why"] += " " + s
            elif isinstance(cur, tuple):
                d["options"][cur[1]] += " " + s
        out.append(d)
    return out


def parse_bullets(text):
    pat = re.compile(r"^\s*([-*\u2022]|\d+[.)])\s+")
    return [pat.sub("", l.strip()) for l in text.split("\n") if pat.match(l)]


def valid_date(s):
    try:
        return datetime.date.fromisoformat(s)
    except Exception:
        return None


def host_ok(url, sources):
    host = (urlparse(url).hostname or "").lower()
    for bad in sources.get("forbidden", []):
        if host == bad or host.endswith("." + bad):
            return False, "forbidden source: " + host
    for good in sources.get("allowed", []):
        if host == good or host.endswith("." + good):
            return True, ""
    return False, "source not on the approved list: " + host


def plan_ids(plan):
    return {t["id"] for ladder in plan["ladders"].values() for t in ladder}


def validate_edition(path, plan, sources):
    name = Path(path).name
    res = {"name": name, "path": str(path), "errors": [], "warnings": [], "ed": None}
    err, warn = res["errors"], res["warnings"]
    m = FILE_RE.match(name)
    if not m:
        err.append("file name must be YYYY-MM-DD_<TOPICID>.md")
        return res
    fdate, ftopic = m.group(1), m.group(2)
    try:
        text = normalise(Path(path).read_text(encoding="utf-8"))
        fm, body = split_front_matter(text)
    except Exception as e:  # noqa
        err.append("cannot read or parse front matter: %s" % e)
        return res
    if fm is None:
        err.append("missing front matter (--- block)")
        return res
    for k in REQUIRED_FM:
        if not fm.get(k):
            err.append("front matter missing: " + k)
    if err:
        return res
    d = valid_date(fm["date"])
    if not d or fm["date"] != fdate:
        err.append("front matter date %r does not match file name date %s" % (fm["date"], fdate))
        return res
    if fm["topic_id"] != ftopic:
        err.append("topic_id %r does not match file name %s" % (fm["topic_id"], ftopic))
    if fm["status"] not in ("draft", "published"):
        err.append("status must be draft or published")
    ids = plan_ids(plan)
    if fm["topic_id"] not in ids and not re.match(r"^REV-\d{4}-\d{1,2}$", fm["topic_id"]):
        err.append("topic_id %s is not in plan.json" % fm["topic_id"])
    if not fm["topic_id"].startswith(fm["subject"] + "-"):
        err.append("subject %s does not match topic_id %s" % (fm["subject"], fm["topic_id"]))
    exams = [e.strip() for e in fm["exams"].split(",") if e.strip()]
    bad = [e for e in exams if e not in plan.get("exam_codes", [])]
    if bad or not exams:
        err.append("unknown or empty exam codes: %s" % (bad or "none given"))
    expected = WEEKDAY_SUBJECT[d.weekday()]
    if fm["subject"] not in expected:
        warn.append("subject %s is off schedule for %s (expected %s)" % (fm["subject"], d.strftime("%A"), "/".join(expected)))

    if DANGEROUS_RE.search(text):
        err.append("contains raw HTML or script-like content")

    secs, order = split_sections(body)
    for k in SECTIONS:
        if k not in secs:
            err.append("missing section: " + k)
        elif not secs[k].strip():
            err.append("empty section: " + k)
    present = [k for k in order if k in SECTIONS]
    if present != [k for k in SECTIONS if k in present]:
        warn.append("sections are not in the standard order")
    if err:
        return res

    lesson_main, deeper = split_deeper(secs[LESSON])
    news = parse_news(secs[NEWS])
    mcqs = parse_mcqs(secs[PRACTICE])
    bullets = parse_bullets(secs[REMEMBER])

    # lesson length
    lw = words(lesson_main)
    if lw < LESSON_ERROR_BELOW:
        err.append("lesson far too short: %d words" % lw)
    elif lw < LESSON_WARN_BELOW:
        warn.append("lesson shorter than target: %d words (target 1500+)" % lw)
    if not re.search(r"^\|.+\|\s*$", lesson_main, re.M):
        warn.append("lesson has no table (the plan asks for one table or timeline)")

    # news
    if len(news) > 3:
        err.append("more than 3 news items")
    for i, n in enumerate(news, 1):
        s = n["source"]
        if not s:
            err.append("news item %d has no Source line" % i)
            continue
        if s["segments"] != 5 or not all(k in s for k in ("name", "url", "published", "event", "link")):
            err.append("news item %d Source line must be: name | url | published: DATE | event: DATE | link: ID" % i)
            continue
        if not s["url"].startswith("https://"):
            err.append("news item %d URL must be https" % i)
        else:
            ok, why = host_ok(s["url"], sources)
            if not ok:
                err.append("news item %d: %s" % (i, why))
        pd, ed_ = valid_date(s["published"]), valid_date(s["event"])
        if not pd or not ed_:
            err.append("news item %d has an invalid date" % i)
        else:
            if pd > d or ed_ > d:
                err.append("news item %d is dated after the edition" % i)
            elif (d - pd).days > 10:
                warn.append("news item %d is %d days old" % (i, (d - pd).days))
        if s["link"] not in ids and not s["link"].startswith("REV-"):
            warn.append("news item %d links to unknown topic %s" % (i, s["link"]))
        if words(n["body"]) < 40:
            warn.append("news item %d is very short" % i)

    # remember + mcqs
    if len(bullets) != 5:
        err.append("ನೆನಪಿಡಿ must have exactly 5 bullets (found %d)" % len(bullets))
    if len(mcqs) != 5:
        err.append("must have exactly 5 MCQs (found %d)" % len(mcqs))
    for i, q in enumerate(mcqs, 1):
        if not q["q"].strip():
            err.append("MCQ %d has no question" % i)
        if sorted(q["options"]) != ["A", "B", "C", "D"] or not all(v.strip() for v in q["options"].values()):
            err.append("MCQ %d needs options A, B, C, D" % i)
        if q["answer"] not in ("A", "B", "C", "D"):
            err.append("MCQ %d has no valid Answer" % i)
        if not q["why"].strip():
            err.append("MCQ %d has no Why explanation" % i)
        if q["level"] not in ("core", "deeper"):
            err.append("MCQ %d needs Level: core or deeper" % i)
    if len(mcqs) == 5 and not err:
        nc = sum(1 for q in mcqs if q["level"] == "core")
        if nc != 3:
            warn.append("expected 3 core and 2 deeper MCQs (found %d core)" % nc)
        qs = [q["q"] for q in mcqs]
        if len(set(qs)) != 5:
            err.append("duplicate MCQ questions")

    total = words(lesson_main) + words(deeper) * 0 + sum(words(n["body"]) for n in news) \
        + words(secs[REMEMBER]) + words(secs[PRACTICE])
    if total < TOTAL_WARN_BELOW:
        warn.append("total core length %d words is below the 20-minute target (%d)" % (total, TOTAL_WARN_BELOW))
    if not secs.get(REVIEW):
        warn.append("no review note section")

    res["ed"] = {
        "fm": fm, "date": d, "exams": exams, "lesson": lesson_main, "deeper": deeper,
        "news": news, "remember": secs[REMEMBER], "mcqs": mcqs, "review": secs.get(REVIEW, ""),
        "words": {"lesson": lw, "deeper": words(deeper), "total_core": total},
        "read_min": round(total / 120), "deeper_min": round(words(deeper) / 120),
        "audit": None,
    }
    return res


def load_audit(path):
    try:
        text = normalise(Path(path).read_text(encoding="utf-8"))
        fm, body = split_front_matter(text)
        if not fm:
            return None
        return {"verdict": fm.get("verdict", "").upper(), "body": body.strip()}
    except Exception:
        return None


def validate_all(content_dir, plan, sources):
    content_dir = Path(content_dir)
    results = []
    for p in sorted((content_dir / "editions").glob("*.md")):
        results.append(validate_edition(p, plan, sources))
    # attach audits
    audits = {}
    for p in sorted((content_dir / "audits").glob("*.md")) if (content_dir / "audits").exists() else []:
        m = AUDIT_RE.match(p.name)
        if m:
            audits[(m.group(1), m.group(2))] = load_audit(p)
    seen_topic, seen_url = {}, {}
    for r in results:
        ed = r["ed"]
        if not ed:
            continue
        fm = ed["fm"]
        r["ed"]["audit"] = audits.get((fm["date"], fm["topic_id"]))
        key = (fm["topic_id"], fm.get("round", "1"))
        if key in seen_topic:
            r["errors"].append("topic %s round %s already used on %s" % (key[0], key[1], seen_topic[key]))
        else:
            seen_topic[key] = fm["date"]
        for n in ed["news"]:
            u = (n["source"] or {}).get("url")
            if u:
                if u in seen_url and seen_url[u] != fm["date"]:
                    r["warnings"].append("news URL already used on %s: %s" % (seen_url[u], u))
                seen_url.setdefault(u, fm["date"])
        if fm["status"] == "published":
            a = r["ed"]["audit"]
            if not a or a["verdict"] != "PASS":
                r["warnings"].append("published without an audit PASS (audit: %s)" % (a["verdict"] if a else "none"))
    for r in results:
        if r["errors"]:
            r["ed"] = None
    return results


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))
