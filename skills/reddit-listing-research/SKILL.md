---
name: reddit-listing-research
description: Reads real Reddit conversations (through a free public archive, never reddit.com) to learn what people need to know before choosing a business in the directory's niche, turns that into 5 to 15 listing fields, then fills those fields from each business's own website with an exact quote as proof, for the owner to approve. Use when the owner wants better, thicker listing pages, asks "what should my listings show", wants niche research, or is starting a new directory.
---

# Reddit listing research

## Playbook card (show this to the owner)

Show this card before setting the helper up (onboarding plan or "add a helper").

**What it does:** learns what people really want to know before choosing a business like yours, then fills those details into your listings from each business's own website, with proof.
**Why it works:** your listing pages win when they answer the questions people actually ask. Every value is quoted word for word from the business's own site, or it stays "unknown".
**How I work:**
1. I read real conversations where people choose a business like yours.
2. I rank what they care about most (price, policies, extras).
3. I turn the top items into 5 to 15 listing details.
4. I read each business's own website (and a chain's company pages once) and copy the exact sentence for each detail.
5. A checker rejects anything not found on that site.
**You approve:** the detail list, a preview on a few listings, then every value before it's saved.
**Cadence:** once, then again for new listings. The research stays valid for about a year.
**What you get:** a research report of what people ask, and listings filled with real, proven details.
**What I need from you:** your list of businesses with their websites.
**Make it yours:** "always cover price for small vs big dogs", "no medical claims", "skip chains".

**Onboarding sample** (≤ about 700 words, ≤ 3 decisions; template in "The owner report" below): what people ask (with the on-topic share), ONE finished listing as it would look on the page, the chain multiplier, fixes for the owner's own pages, the proof sheet.

**If a step fails** (blocked site, thin data, noisy results): use the fallback below and still deliver the best honest sample. Never end with less without telling the owner, in plain words, what blocked it and the fix.

## THE RULES (read before doing anything)

1. **Never use reddit.com** (website, `.json`, RSS, old.reddit, search limited to reddit.com). It blocks AI tools; don't try "just to check".
2. **Never fake a browser, rotate proxies, or pay a scraping service** to get around any block.
3. **Reddit data comes only from the Arctic Shift archive** through the scripts. Never run two archive scripts at once. "Timeout" means wait and retry; `[]` means no results.
4. **Use the scripts in `scripts/`. Never write your own versions.** A script fails: see REFERENCE.md "RT. Troubleshooting".
5. **Never invent facts.** Every listing value has the exact quote and the URL it came from, or it is `unknown`. `unknown` is a good answer.
6. **Never claim anything about competitors** ("most directories don't…") unless you checked 3 competitor pages and name them.
7. **Blocked business sites: use your built-in web reader first** (at most 20 per run) and save its text in the same format. Only if that also fails, the values are `unknown`. **Never ask the owner to paste pages.**
8. **Nothing is written to the directory until Step 12**, and only approved values.
9. **Stop at every 🛑 and ask the owner** (quick mode: you decide, see below).
10. **Reddit is research only.** Never copy Reddit text or usernames onto listing pages.

## Where things live

Research folder per site: `/data/workspace/directory-ops/notes/<slug>/reddit-research/`. **`cd` into it before every command.** Scripts: `S=/data/skills/directory-ops/reddit-listing-research/scripts`, run as `python3 $S/<script>.py`. A long download cut off: run the same command again (they resume). Read `sites/<slug>.yaml` and `notes/<slug>.md` first, including `## Listing research rules`.

## Quick mode (onboarding or "add a helper")

The 🛑 stops in Steps 2, 4, 8 and 9 are yours to decide with the rules below. Default size: a **10% preview** (`max_pages_per_sub` 4, `max_threads` 25, pilot of 3 to 5 listings from different chains or owners); say "10% preview" to the owner and what the full run adds. Ask no setup questions: fill them from onboarding (REFERENCE.md R0 lists them). Never mention subreddits, threads, batches or scripts to the owner: say "Reddit conversations". Run directly by the owner: every 🛑 applies.

**Teach me your way** (one optional question after the helper is accepted, wording in REFERENCE.md R0b): turn their answer into 3 to 7 rules, save under `## Listing research rules` in `notes/<slug>.md`. Owner corrects a proposal: ask once "Want me to remember that as a rule?".

## STEP 0a: Quick check (free)

```
python3 $S/check_subreddits.py AskReddit
```
`OK` → continue. `ARCHIVE TIMEOUT` → wait 2 minutes, try once more; still failing → tell the owner "The free Reddit archive this uses is down right now. I'll try again tomorrow." and stop.

## STEP 0: Setup 🛑 (full mode only)

Ask the questions in REFERENCE.md R0, one per message, then repeat them back in 3 to 5 lines and ask "Shall I start?".

## STEP 1: Settings

Copy `research.example.json` to `research.json`, fill it from Step 0 (word lists: REFERENCE.md R1). Keep `limits` (quick mode: the 10% sizes) and `"company_facts": "ask"`.

## STEP 2: Find the niche's own community 🛑

The obvious name is often dead; the real community may have a slang name. Do both:
1. One normal web search (not limited to reddit.com): `best subreddit for <customers of this niche>`.
2. ```
   python3 $S/discover_subs.py --words <business word> <customer word> --general <2 to 4 big subs these customers use> --also <names from the search>
   ```
The PRIMARY row is the main source (first in `focused`). Under about 2 comments per post = second source only. Check the final list with `python3 $S/check_subreddits.py <names>` (remove NOT FOUND). Details and examples: REFERENCE.md R2. Show the owner the list with activity numbers 🛑.

## STEP 3: Download posts (free, 5 to 20 min)

```
python3 $S/pull_posts.py
```
TOTAL under 300: add 1 to 2 focused subreddits (Step 2).

## STEP 4: Keep only decision threads 🛑

```
python3 $S/filter_threads.py
```
**Count how many of the 40 printed titles are about choosing, paying for, comparing or complaining about this kind of business. Target: at least 30 of 40 (3 of 4); in a small run, at least 3 of every 4 kept.**
- Under target: add the off-topic words (health, jokes, jobs) to `exclude_words`, run again. Two rounds.
- Still under target, or under about 40 on-topic threads: **plan B** (REFERENCE.md R4): add Google questions (a few web searches for "People also ask" and autocomplete about choosing this business) as extra factors, marked "from Google questions". Never ship thin research as if it were solid.
- `WARNING: 0 threads from the niche's own community` → back to Step 2.
- Write down the final on-topic share ("22 of 25 on topic"); the owner report shows it.

## STEP 5: Download comments (free, about 8 seconds per thread)

```
python3 $S/pull_comments.py
```

## STEP 6: Read the conversations (uses AI credits)

```
python3 $S/make_batches.py
```
For each `batches/batch_NNN.txt` write `extractions/batch_NNN.json`: per thread `{"thread_id", "relevant", "factors": [{"factor", "quote"}], "prices", "red_flags"}`. Factors = what people care about **when choosing a business**, 3 to 8 words; quotes copied exactly, under 25 words. Full format and rules: REFERENCE.md R6. Then:
```
python3 $S/check_batches.py
```
Fix every `FIX` line until `OK`. After 3 batches, report AI usage from the meter (never estimate); over budget → stop and ask 🛑.

## STEP 7: Rank

```
python3 $S/list_factors.py
```
Write `factor_map.json` mapping every printed name to 12 to 25 short canonical factors (or `"DROP"`), REFERENCE.md R7. Then `python3 $S/build_report.py` (counts threads per factor → `output/research_report.md`).

## STEP 8: Pick listing fields 🛑

Write `output/fields.json`: 5 to 15 fields businesses state on their own sites (`found_on_site` likely/sometimes), ordered by the money model, `"money": true` on any amount that changes (prices, pay, bonuses, fees). Fields only found in reviews → `output/not_extractable.json`. Format and ordering: REFERENCE.md R8. A field from 1 thread is weak: mark it "(1 thread)". **Every field must map to a ranked topic** (write its `"topic"`); drop fields the research didn't surface unless the owner asked for them. Top topics no website can answer (pay, bonuses, waits) go to `not_extractable.json` and the report says so plainly.

## STEP 8b: Make room for the fields 🛑 (one time)

Columns for new fields and a "Good to know" section on the page: walk the owner through REFERENCE.md R8b only when they want to save values. Not needed for the preview.

## STEP 9: Pilot

Export listings to `data/listings.csv` (id,name,website,address): commands in REFERENCE.md R9. Then:
```
python3 $S/fetch_sites.py --limit 5        (quick mode: 3 to 5)
python3 $S/chain_pages.py                  (chains with 5+ listings; --min 3 for small directories)
```
- `sites/_failed.txt` lines with `blocked_by_security`: **read each with your built-in web reader now** (Rule 7) and save to `sites/<id>.txt` as `=== PAGE: <url>` + text. Still blocked → `unknown`, one plain line in the report.
- `chain_pages.py` saves each chain's company pages once (`sites/_chains/<domain>.txt`) and 2 other locations' pages (`.siblings.txt`) so the checker can spot chain boilerplate.

### Step 9c: Read the directory's own listing pages

```
python3 $S/own_pages.py --site <the directory's URL>
```
For each pilot listing it prints what the owner's page already shows per field (every text block: sidebars and info boxes too), then **TEMPLATE LINES**: sentences on 2+ sampled pages, i.e. on every page of that type. Note:
- **Template lines first:** check each one with a fact in it (times, ages, pay, what to bring) against the VERIFIED values by meaning. A wrong template line is the biggest fix (it touches every page): report it as "appears on every listing page", ranked above single-page fixes.
- **Fill targets:** labels the page shows with no value ("No bonus info reported yet").
- **Page fixes:** only when the MEANING conflicts, not the wording ("no appointment needed" and "walk-ins accepted" agree; "2 to 2.5 hours" vs "1 to 2 hours" conflict). Template sentences that contradict a verified fact (page: "No appointment is necessary. Walk-ins are welcome."; the business: "Download our app to see available appointments"). Quote both. Not found in the sitemap → `--url <id>=<url>`.

## STEP 10: Extract (uses AI credits)

For each `sites/<id>.txt` write `staging/<id>.json` with every approved field: `{"value", "quote", "source_url"}`, `"unknown"` when not stated (format: REFERENCE.md R10). Order:
1. This location's own page first.
2. Still unknown and it's a chain: the chain's company pages, **rules only** (payment method, appointments, what to bring, age or weight rules), with `"scope": "chain"`.
3. **Never an amount from company pages.** "Select/participating locations" never proves this location.
Fill a chain's company facts ONCE and reuse them for every pilot listing of that chain.

## STEP 11: Check, then approve 🛑

```
python3 $S/check_extractions.py
```
It verifies every quote, labels company policy and **chain boilerplate** (the same sentence on other locations' pages = "same wording on every <Chain> location page", never "this location's own page"), dates money values, and prints the FILL RATE and **CHAIN MULTIPLIER** lines ("2 company-wide facts apply to all 49 Parachute listings"). Over 15% REJECTED → redo Step 10 for those. Then send the owner report (below) and write `y`/`n` into `output/review.csv` from their answer ("approve all" = every VERIFIED row; never REJECTED, UNKNOWN or CHECK SCOPE). Details: REFERENCE.md R11.

## STEP 12: Write approved values

```
python3 $S/apply_approved.py --db-py /data/skills/directory-ops/directory-db/db.py --site-url <database.url> \
    --key-env <database.key_env> --table <listings table> --id-column <id col> --slug <slug>
```
Dry run first, show the owner, then add `--apply`. Only empty cells, one update per listing, logged. Other storage: `output/approved.csv` to import. Details: REFERENCE.md R12.

## The owner report (≤ about 700 words, ≤ 3 decisions)

```
<Site>: listing research (<10% preview | full run>)

Reach: <CHAIN REACH TOTAL line in plain words: "<N> company-wide facts fill about <X> details across <Y> of your listings">.

What it means for you: of the top <M> TOPICS people raise before choosing a <business> (count topics, never conversations), your listing pages can answer <N> from the businesses' own websites (<which>). <Which top topics can't be filled from websites and why, e.g. "pay and bonuses change by location and month and aren't on center pages"> (good article or community-report topics instead).

One finished listing:
<Business>: Good to know
- <label>: <value> (<as of date for money>)
- ...

What people ask most (<conversations> conversations, <on-topic share> on topic): <5 to 8 lines, one quote each>

Fixes for your own pages: <up to 3, template lines first ("appears on every listing page"): what your page says vs what the business says, both quoted, by meaning>

Proof: <numbered verified values: listing, detail, value, quote, link>. <unknowns and blocked sites in one line>

Your call (max 3): 1) approve these values? 2) company facts OK? 3) <one more if needed>
```
Defaults decide everything else silently. Offer "say 'show the full research report'" instead of naming files. Fields in `not_extractable` and top questions make good article topics: offer them to content-opportunities.

## Costs and time

Downloads are free (posts 5 to 20 min, comments about 8 s per thread, sites about 5 s each). AI credits go to Step 6 (reading) and Step 10 (extracting); report the meter, never estimate. Full run example: REFERENCE.md RC.
