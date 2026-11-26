# Karnataka Exams Daily (working name) — product & content design (v2)

A 20-minute daily reading for Karnataka competitive-exam aspirants (KAS, FDA, SDA, PSI, PDO, RTO and the general-awareness parts of banking and defence exams). Kannada first, with English technical terms in brackets. Like a newspaper in habit, but every issue teaches one syllabus topic properly, ties current affairs to concepts, and ends with 5 MCQs. No accounts, no learner tracking, no ads.

## 1. Evaluation

**What is strong**
- Clear gap: coaching sites sell headline digests; few offer a *taught concept + news + practice* routine in Kannada.
- The habit format (one finite issue a day) is easy to sell and easy to share on WhatsApp/Telegram.
- Cheap to run: static site on GitHub Pages, one scheduled Gemini run, near-zero hosting cost.

**What can sink it (and what this design does about it)**

| Risk | Why it matters | Mitigation |
|---|---|---|
| Wrong facts reach students | One wrong Article number or date destroys trust, and students memorise what they read | Source rules (section 4), a build-time validator, and a `draft` gate for the first two weeks |
| Weak or machine-like Kannada | Students will notice immediately | Fixed style rules in the prompt, a growing glossary from your corrections, and a native read of every draft in the first two weeks |
| Repetition or random topic order | Feels like a digest, not a course | Fixed weekday-to-subject rotation and an ordered topic plan; `covered.json` is generated from the repo itself |
| Current affairs filler | News "because it is trending" | A 3-question gate and a hard cap of 3 items |
| Thin demand signal for monetisation | "Interest" is invisible without any data | Privacy-friendly aggregate analytics and a WhatsApp/Telegram channel (section 6) |
| Syllabus drift | The plan is not the official syllabus | `plan.json` is marked provisional and reconciled with the official KPSC notification PDF |

**Facts to confirm from the official notification** (I found them only on secondary sites): the 2026-27 KAS notification is dated 31 July 2026 for 319 posts; the prelims was tentatively set for 15 Nov 2026; prelims is two objective papers; mains is 7 papers (Kannada and English qualifying, essay, four GS) plus an interview. Download the notification PDF from KPSC and I will reconcile `plan.json` against it. Note the original brief lists `kpsc.karnataka.gov.in`, while the sources I found cite `kpsc.kar.nic.in` as the official site. Check which one actually serves the notification.

## 1b. Scope: one core reading, add-on corners later

**The pattern I found:** almost every Karnataka state exam has a General Knowledge (GK) paper plus separate language, computer or aptitude papers. Banking and defence exams also carry a General Awareness section. So the shared, reusable asset is **GK + current affairs**. The skill papers (language, computer, quant, reasoning, technical) are a different kind of content: drills, not reading.

| Exam family | Structure as reported by secondary sites (confirm in each notification) | Daily Core covers | Core does NOT cover |
|---|---|---|---|
| KAS | Prelims two objective papers; mains essay + GS papers | GS content, current affairs, Karnataka | Essay and mains answer writing |
| FDA / SDA | GK paper (100) + Kannada/English/Computer paper (100); Kannada language test | The whole GK paper | Language and computer paper |
| PDO | Same GK + language pattern; secondary sources add rural development and Panchayati Raj | GK, plus Panchayati Raj topics in the ladders | Language, computer |
| PSI | Descriptive paper (essay, precis, translation) + objective Mental Ability and Current Affairs | The current-affairs half | Mental ability, descriptive writing |
| RTO / MVI | GK paper + technical paper (automobile / mechanical engineering) | The GK paper | The technical paper |
| Banking | Prelims: English, quant, reasoning. Mains add General/Economy/Banking Awareness | GA and economy part | Quant, reasoning, English, computer |
| Defence | English, GK, maths/science depending on the exam | GK part | Maths, English, physics |

**Honest promise on day one:** "covers the GK / General Awareness paper for these exams". Do not claim it covers a whole exam.

**Level differences:** FDA is reported to be degree-level GK and SDA PUC-level, while KAS is deeper. Every lesson therefore has two layers (section 3) and every MCQ is tagged by level.

**Roadmap**
1. **Phase 1 (now):** the Core daily edition, tagged by exam.
2. **Phase 2:** a short (~8 min) **Corner** edition on its own schedule: Banking and Financial Awareness, and Defence and Security Awareness. Draft ladders are in `data/plan_corners.json`.
3. **Phase 3:** skill drills: Kannada and English language, computer knowledge, mental ability / quant / reasoning, PSI descriptive writing and the criminal-law topics PSI aspirants need.
4. **Out of scope:** RTO technical paper, physical and SSB tests.

## 2. The weekly rhythm (this is the structure)

One subject per weekday, so a learner gets variety daily and steady coverage weekly.

| Day | Subject | Code | Current-affairs lens |
|---|---|---|---|
| Mon | Indian Polity & Governance | POL | Parliament, courts, Bills, constitutional bodies |
| Tue | History & Culture (India) | HIS | Heritage, archaeology, anniversaries, culture schemes |
| Wed | Geography | GEO | Weather, rivers, disasters, mapping-in-news |
| Thu | Indian Economy | ECO | RBI, Budget, GST, data releases |
| Fri | Environment & Science-Tech (alternate weeks) | ENV / SCI | Climate, biodiversity, ISRO, tech policy |
| Sat | Karnataka Special | KAR | State history, geography, economy, administration, schemes |
| Sun | Weekly Recap | REV | Recap of the week's 6 topics, plus the 3 most important news items of the week |

Each subject has an ordered ladder in `data/plan.json`. The ladders run 10 to 25 topics each, so one round of all subjects takes about 5 to 6 months. Round 2 revisits each ladder at a higher depth. The trade-off is slower coverage than a single-subject sprint; if you want faster coverage, we can run two topics per issue on weekdays.

## 3. One edition (target ~20 min, ~2,400 to 2,700 Kannada words)

| # | Section | Time | Purpose |
|---|---|---|---|
| 1 | **ಇಂದಿನ ವಿಷಯ** Concept of the Day | ~9 min | One syllabus topic, explained from basics |
| 2 | **ಇಂದಿನ ಸುದ್ದಿ** Current Affairs (max 3) | ~6 min | Each news item tied to a concept |
| 3 | **ನೆನಪಿಡಿ** Remember This | ~1 min | 5 one-line takeaways |
| 4 | **ಅಭ್ಯಾಸ** 5 MCQs | ~4 min | Tap to reveal the answer plus a 1 to 2 line explanation |

**Concept lesson template:** why it matters, the basics, the core explanation, a key-facts table (Articles, years, bodies, numbers), the exam angle (common confusions and typical question styles, never claiming a specific question will appear), and a one-line summary.

**Current-affairs item template:** headline, what happened (2 to 3 lines), the concept behind it (links to the syllabus topic ID), why it matters for the exam, 1 to 2 facts to remember, source name, link and date.

**Selection gate:** an item is included only if (1) it maps to a syllabus topic, (2) the source page was actually opened and read, and (3) it teaches something beyond the headline. Exclude celebrity, politics-as-gossip, routine crime, routine sports results and unverifiable items. Fewer than 3 items is fine.

**MCQs:** 5 original questions (mix of recall, concept, statement-based, match-the-following), 4 options each. 2 to 3 should come from today's concept and 1 to 2 from the news. Labelled "practice questions", never "previous-year questions" unless the paper is verified.

**Two layers, so one edition fits many exams:** the main lesson is written so a PUC-pass reader can follow it (about 20 min in total). Under it sits an optional **ಹೆಚ್ಚಿನ ಆಳ (Deeper)** block of up to 500 words with extra nuance for KAS and CDS-level readers. Each MCQ is tagged `core` (3 per edition) or `deeper` (2). Each edition also carries an `exams:` tag so the site can filter by exam.

## 4. Sources

**Rule:** facts come from primary sources. Newspapers are for discovery and explanation. Coaching sites, Telegram/WhatsApp, and Wikipedia are never cited as authority.

**Tier 1: facts (cite these)**

| Area | Source | How Gemini reaches it |
|---|---|---|
| Central government | PIB (RSS available at `pib.gov.in/ViewRss.aspx`), Cabinet decisions | RSS or page fetch |
| Law | India Code, Sansad, Supreme Court judgments, PRS India | Page fetch |
| Economy | RBI press releases, MoSPI, Union Budget, Economic Survey | Page fetch |
| Elections | ECI | Page fetch |
| Science / space / environment | ISRO, MoEFCC, CPCB, IMD, DST | Page fetch |
| External affairs | MEA | Page fetch |
| Karnataka | Government of Karnataka, Karnataka Varthe (DIPR), Karnataka e-Gazette, state Budget and Economic Survey, KPSC | Page fetch |
| Banking (Phase 2) | RBI, SEBI, NPCI, IRDAI, PFRDA | Page fetch |
| Defence (Phase 2) | Ministry of Defence, PIB defence releases, DRDO, official Army / Navy / Air Force sites | Page fetch |

**Tier 2: discovery and explanation:** The Hindu, The Indian Express, Deccan Herald, Down To Earth, Mongabay India; optionally Kannada dailies for Karnataka items. Never reproduce articles; write your own explanation and link to the original.

**Tier 3: concept sources (evergreen lessons):** NCERT textbooks, the Constitution text on India Code, Karnataka textbook society books for Karnataka topics, official Economic Survey chapters. Standard reference books may guide *what to cover*, but no text is copied.

**Per-day source routing:** Gemini opens only the sources relevant to the day's subject plus one Karnataka feed, not everything. This keeps the run short and the output focused.

**Housekeeping:** strip the `utm_source=chatgpt.com` tracking tails from every URL in the original brief before using them as a registry.

## 5. Repo and file contract

```
content/editions/2026-11-27.md   <- one file per day (Gemini output, committed by Apps Script)
data/plan.json                    <- ordered topic ladders (hand-maintained, provisional)
data/plan_corners.json            <- Phase 2 banking and defence ladders (draft)
data/covered.json                 <- generated by the Action from editions (never edited by hand)
site/                             <- templates, CSS, JS
scripts/validate.py, build.py
.github/workflows/publish.yml
```

**Edition file:** flat front matter (`key: value` only, no nesting) plus fixed headings. I chose this over nested YAML because LLM-written YAML with Kannada text and quotes breaks easily; this format is easy to validate with simple rules.

**Validator (build fails, nothing broken goes live):** the date matches the filename; the topic ID exists in `plan.json` and is not already covered; all 4 sections are present; exactly 5 MCQs, 4 options each, answer in A to D; at most 3 current-affairs items, each with a URL and date; no section is empty; status is `draft` or `published`; `exams` uses only known exam codes; every MCQ has `Level:` core or deeper. Generated Markdown is sanitised: raw HTML or scripts in it are never rendered.

**Draft gate:** the build only publishes `status: published`. For the first two weeks Gemini writes `draft`; you read it and change one word on GitHub (works from a phone).

## 6. How it looks and how interest is measured

```
┌─────────────────────────────┐
│ ExamDaily        ☰ ಆರ್ಕೈವ್ │
│ ಶುಕ್ರವಾರ · 27 ನವೆಂಬರ್ 2026   │
│ ಇಂದಿನ ವಿಷಯ: ಪೀಠಿಕೆ (POL-04) │
│ ⏱ ~20 ನಿಮಿಷ  ● ○ ○ ○        │  <- 4 section dots
├─────────────────────────────┤
│ 1 ಇಂದಿನ ವಿಷಯ (long read)    │
│ 2 ಇಂದಿನ ಸುದ್ದಿ (3 cards)    │
│ 3 ನೆನಪಿಡಿ (5 bullets)       │
│ 4 ಅಭ್ಯಾಸ  [tap to reveal]    │
│ [WhatsApp ನಲ್ಲಿ ಹಂಚಿ]        │
└─────────────────────────────┘
```

- **Disclaimer on the About page:** the topic plan is our reading of the syllabus, not an official KPSC or KEA document; each exam body's notification is the authority.
- **Pages:** Home (today), edition page (permanent URL `/e/2026-11-27/`), archive by date, subject index, "How we verify" (sources and method), RSS feed.
- **Exam filter:** chips at the top (All, KAS, FDA/SDA, PSI, PDO, RTO, Bank, Defence) hide or show the Deeper block and highlight the topics relevant to the chosen exam.
- **Mobile-first:** single column, Noto Sans Kannada, large type, generous line height, dark mode, plain HTML plus a tiny script for MCQ reveal (no framework, fast on weak networks).
- **Distribution:** a daily WhatsApp/Telegram channel post carrying the edition link (the Apps Script can send it). These channels are for reach only, never for facts.
- **Interest signals for monetisation:** privacy-friendly aggregate analytics (page views, returning visitors, MCQ-reveal clicks), channel subscribers, and a one-tap "was this useful?". This measures demand without tracking individual learners. If you do not want any analytics, drop it and rely on channel growth.
- **Monetisation seam (later):** keep the latest 7 editions free and move the archive and revision packs behind a small payment later. Nothing is built for this now.

## 7. Decisions still open

1. Pace: one subject per day (this design) or deeper multi-topic days.
2. Analytics: yes or no.
3. Exact repo name and whether it is public (Gemini fetches `plan.json` and `covered.json` from the raw URL; if that is not possible the plan goes into the prompt).
4. The existing Courtroom Chronicles Apps Script: I need to see its commit function to confirm only the file path changes.
5. Which exam families to prioritise in messaging at launch. My suggestion: lead with the state exams (KAS, FDA/SDA, PDO, PSI), because the Core covers the whole GK paper for them; mention banking and defence as "GA section only" until Phase 2.
