---
name: tool-page-finder
description: Find calculator and tool page ideas for any website.
version: 0.3.0
author: Frey Chu
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [seo, keyword-research, tool-pages, calculators, free]
    related_skills: []
---

# Tool Page Finder

## Playbook card (show this to the owner)

Show this card to the owner before setting the helper up (onboarding plan or "add a helper"), so they see and approve the process.

**What it does:** finds the simple calculators and tools your visitors already search for (fee calculators, cost estimators, checkers) that small sites can rank for.
**Why it works:** tools answer a search better than any article, earn links, and keep people coming back. We only pick ones where small sites already rank, so you can win too.
**How I work:**
1. I list the main topic, the brands your visitors use, and what they do next.
2. I pull hundreds of real Google suggestions around them (free).
3. Scripts group them into tool ideas and drop junk (other countries, shopping, owner-only tools).
4. I check who ranks for the top 10 and score each idea.
5. You get the top 5 with the evidence and where the numbers would come from.
**You approve:** which tool to build. Nothing is built without your yes.
**Cadence:** every few months, because good tool ideas don't change weekly.
**What you get:** a top 5 tool list with search evidence, who ranks today, and a build brief.
**What I need from you:** nothing. A keyword export from an SEO tool makes it sharper, but it's optional.
**Make it yours:** "visitors only, nothing for business owners", "no brand-name tools", "we already have a cost calculator".

**Onboarding sample:** the top 5 tools, with search evidence and who ranks today.

**If a step fails** (blocked site, thin data, noisy results): try the fallback this skill documents, and still deliver the best honest sample. Never end with less than the onboarding sample without telling the owner, in plain words, what blocked it and the fix.

**Details for any step are in `REFERENCE.md` (same folder), section R<step number>.** Open a section only when this file points you there.

Finds the calculator and tool pages a website should build next: fee calculators, cost estimators, price lookups, schedules and checkers.

- **FREE MODE:** no paid tools. Google Autocomplete plus your web search.
- **DATA MODE:** used when the user gives a keyword export with search volume (Ahrefs, Semrush, Google Keyword Planner, Google Search Console).

`${HERMES_SKILL_DIR}` = this skill's folder (on Hostinger: `/data/skills/directory-ops/tool-page-finder`; if your agent doesn't set it, use that full path). The scripts do all the counting, filtering and scoring. You run commands in order, answer yes/no questions, and copy URLs.

**Use it for:** "what tools or calculators should I build?", "find tool page ideas for <site>", "find low-competition pages I can add to <site>". **Not for** blog post ideas, backlinks, or local "near me" pages.

## Golden rules
1. Do the steps in order. Never skip a step.
2. **Unsure what's next? Run** `python3 ${HERMES_SKILL_DIR}/scripts/next.py --site <site>`. It prints the exact next step and command.
3. Never invent a number, URL, fee or score. Don't know it: write `unknown`.
4. A command prints `ERROR:` → do what it says, run the same command again. Don't move on until the error is gone.
5. Never edit candidates.csv or scored.csv by hand.
6. Never call the FREE MODE demand number "searches per month".

## Steps

| Step | You do | File it makes |
|---|---|---|
| 0 | Ask up to 3 questions, make a work folder, copy in keyword exports | work folder |
| 1 | Write seeds.txt | seeds.txt |
| 2 | Run suggest.py | suggestions.csv |
| 3 | Run classify.py | candidates.csv, review.txt |
| 4 | Answer yes/no in review.txt | review.txt |
| 5 | Run score.py --make-serp-template | serp.csv (empty) |
| 6 | Web-search 10 keywords, paste URLs (6b: optional Google Trends) | serp.csv, trends.csv |
| 7 | Run score.py --serp | scored.csv |
| 8 | Run brief.py | tool-pages-report.md |
| 9 | Replace the 5 CHECK lines | tool-pages-report.md |
| 10 | Send the result | done |

### Step 0. Inputs and work folder
- **Quick mode (onboarding):** ask nothing. Write the visitor sentence yourself ("Visitors look for a <business> near them, then <next step>"); say once: "I'll use free Google data. If you ever have an Ahrefs, Semrush or Search Console export, send it and I'll redo the ranking."
- **Otherwise**, one per message, skipping what's known: website URL; "In one sentence, what do your visitors do on your site, and what do they do right after?"; whether they have an SEO tool export (optional). Exact wording and the not-live variant: REFERENCE.md R0.
- `mkdir -p ~/tool-page-finder-runs/<site> && cd ~/tool-page-finder-runs/<site>` (`<site>` = the domain). Run every later command here.
- Copy any CSV exports the user sent into this folder unchanged (never name them suggestions/candidates/serp/scored/trends.csv).
- **Teach me your way** (one optional question right after the helper is accepted; rules saved under `## Tool ideas rules` in `notes/<slug>.md`, read first on every run; corrections → "remember as a rule?"): REFERENCE.md R0b.

### Step 1. Write seeds.txt
8 to 12 lines, `bucket: seed`, lowercase, 1 to 3 words each: `core` (main topic, 2–3), `entity` (brands/platforms visitors use, 3–5), `next` (what visitors do right after, 2–3). No single words with several meanings ("fish tank", not "tank"); no tool words (calculator, cost, fees, price). Example and rules: REFERENCE.md R1. **Done when** `next.py` no longer says seeds.txt is invalid.

### Step 2. Google Autocomplete
```
python3 ${HERMES_SKILL_DIR}/scripts/suggest.py --seeds-file seeds.txt --out suggestions.csv
```
About 1 minute per seed. **Done when** the last line starts with `DONE:` and shows 500+ suggestions. Under 500, or `ERROR: more than half the requests failed`: REFERENCE.md R2.

### Step 3. Keywords → tool ideas
```
python3 ${HERMES_SKILL_DIR}/scripts/classify.py suggestions.csv --seeds-file seeds.txt --out candidates.csv
```
With keyword exports, list them after suggestions.csv: `... classify.py suggestions.csv ahrefs_export.csv --seeds-file seeds.txt --out candidates.csv`.
Note `FREE MODE` or `DATA MODE`. **Done when** `DONE:` with 10+ ideas. Warnings and errors: REFERENCE.md R2.

### Step 4. Yes/no check
In review.txt replace each `??` on lines starting with `C` with `yes` or `no` by asking **"Would a visitor of this website use this tool?"** (not sure = no; change nothing else). Quick mode: answer yourself and list your choices in the sample. **Before Step 5, also check the top 10 ideas in candidates.csv** and add a `no` line for tools for the business owner, one competitor's own product (unless it's the platform visitors use), or pure shopping/hours. Line format and examples: REFERENCE.md R4. **Done when** no `C` line still has `??`.

### Step 5. Search-results template
```
python3 ${HERMES_SKILL_DIR}/scripts/score.py candidates.csv --decisions review.txt --make-serp-template 10
```
**Done when** it prints `WROTE serp.csv`.

### Step 6. Fill in who ranks
For each of the 10 keywords: web search it exactly as written, paste the first 5 normal results' full URLs into the `url` cells in order (skip ads, videos, "People also ask"). Copy URLs exactly, never from memory. Leave `dr` empty unless the user has Ahrefs/Moz/Semrush numbers. Don't touch `keyword`/`rank`. **Done when** every keyword has 3+ URLs. Details: REFERENCE.md R6. Optional Google Trends (`trends.csv`): REFERENCE.md R6b.

### Step 7. Score
```
python3 ${HERMES_SKILL_DIR}/scripts/score.py candidates.csv --decisions review.txt --serp serp.csv --out scored.csv
```
If you made trends.csv, add `--trends trends.csv` before `--out`.
**You score nothing**; the script does (how: REFERENCE.md R7). **Done when** `DONE: scored ...`. `ERROR: serp.csv has problems` → fix exactly the lines it lists, run again.

### Step 8. Report
```
python3 ${HERMES_SKILL_DIR}/scripts/brief.py scored.csv --site <site> --out tool-pages-report.md
```
**Done when** `DONE: report with 5 briefs`.

### Step 9. Fill the 5 CHECK lines
For each `**CHECK:**` line: open the "Official data source" URL (or the first "Tool pages already ranking" URL), copy the current numbers exactly, and replace the line with `- **Current numbers (checked YYYY-MM-DD from <URL>):** <numbers>`. Blocked page → its newest Internet Archive copy (`https://web.archive.org/web/2/<url>`); never numbers from search snippets. Nothing found → `- **Current numbers:** unknown. Check before building.` Full rules (incl. the "none in the top 5" fallback search): REFERENCE.md R9. **Done when** no `**CHECK:**` is left.

### Step 10. Deliver
Send: the "Ranked shortlist" table, the "Why it's here" line for each of the 5, one line offering the full report ("Say 'show the full tool report'"), the keep-pages-up-to-date line if that skill is installed, and in FREE MODE this sentence exactly: "These rankings use Google Autocomplete, not search volume. Check the top 2–3 picks in Search Console, Keyword Planner or an SEO tool before building." Exact wording: REFERENCE.md R10. Before calling it done, run the checklist in REFERENCE.md "Verification". Common traps: REFERENCE.md "Pitfalls".
