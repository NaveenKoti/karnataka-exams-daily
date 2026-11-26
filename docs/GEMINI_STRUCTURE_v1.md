# Gemini side: how it is structured

## Why two tasks, not one
One prompt that researches, verifies and writes 3,000 Kannada words in a single run fails in predictable ways: it runs out of room, it writes facts it never verified, and the Kannada gets thinner towards the end. Splitting the job fixes all three.

| Task | Time (IST) | Job | Output |
|---|---|---|---|
| 1. Research desk | 02:30 | Pick today's topic, collect 35 to 45 sourced facts, select news, draft MCQ seeds | `briefs/YYYY-MM-DD_<TOPICID>_brief.md` |
| 2. Writer | 03:30 | Turn the brief into the Kannada edition. **May only use facts in the brief** | `editions/YYYY-MM-DD_<TOPICID>.md` |

The rule "the writer may only use facts from the brief" is the main accuracy control. Every claim in the edition traces to a fact ID with a URL.

## Drive folder (create once)
```
KED/
  plan/plan.json                         <- you upload (static)
  briefs/2026-11-27_POL-04_brief.md      <- Task 1 writes
  editions/2026-11-27_POL-04.md          <- Task 2 writes; your Apps Script picks these up
```
Use the exact folder and file names; the no-repeat logic depends on them.

## How repetition is prevented
- **Lessons:** the topic ID is in the edition's file name. Task 1 lists `editions/`, treats those IDs as covered, and takes the first uncovered topic in the day's ladder. There is no separate log file to corrupt. A day with no edition (a failed run) is retried automatically the next time that weekday comes round.
- **News:** Task 1 opens the last 3 editions and reads their `Source:` lines. A URL or event already used is skipped, unless there is a new official development, and then the brief must say what is new.
- **Revision without re-teaching:** each lesson opens with a one-line link to related earlier topics (from the file names) instead of re-explaining them.
- **Finished ladders:** the ladder restarts as "Round 2" with an advanced angle, never the same lesson again.

## Making 20 to 30 minutes honest
Reading time is planned from a word budget, and the density comes from content, not padding.

| Section | Words (Kannada) | Minutes |
|---|---|---|
| Concept of the Day (main) | 1,500 to 1,800 | ~12 |
| Current affairs (max 3) | ~250 each, 600 to 800 | ~7 |
| Remember This | ~100 | ~1 |
| 5 MCQs with explanations | ~450 | ~5 |
| **Core total** | **~2,800 to 3,200** | **~25** |
| Deeper block (optional) | up to 500 | +4 |

The lesson must contain at least: one table or timeline, 8 or more named or numeric facts, 2 worked examples, 3 common confusions with the correct answer, and a "how it is asked" paragraph. These minimums are what make it worth 12 minutes.

**Calibrate once:** time yourself reading the first edition aloud-silently at study pace and adjust the word budget in Task 2. Kannada reading speed varies by person, so treat the numbers above as a starting estimate.

## Failure behaviour
- Task 1 cannot read the plan or the folder: it outputs `BLOCKED: <reason>` and creates no brief.
- Task 2 finds no brief for today: it outputs `BLOCKED: no brief` and creates no edition.
- A thin brief (fewer than 35 facts): Task 1 marks it `THIN`, and Task 2 writes a shorter lesson and says so in the review note. It never pads.

## First-run test (do this before scheduling)
1. Create the folder and upload `plan.json`.
2. Run Task 1 by hand. Open the brief. Click 5 random URLs and check the fact matches.
3. Run Task 2 by hand. Read it, time it, and fix the Kannada terms in the review note.
4. Only then schedule both tasks, keeping `status: draft` for the first two weeks.

## Practical notes (check in your account)
- I believe Gemini limits the number of active scheduled actions; check your limit. This design uses 2.
- If Gemini cannot create files in Drive from a scheduled run, each prompt tells it to print the file text instead. Your existing pipeline then does the saving.
- If Gemini cannot read `plan.json` from Drive, paste the plan's ladder lists into Task 1's prompt under STEP 1.
