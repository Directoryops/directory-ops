---
name: listing-check
description: Keeps directory listings accurate. Re-checks existing listings against Google, the business's own website and social pages, then updates hours, address, phone, prices and links, marks closures (never deletes), and confirms each listing is still the right kind of business. Also tests website links, checks what the site publishes to Google, and reports missing details and duplicates. Checks the longest-unchecked listings first, in small batches, and sweeps a whole chain when it changed everywhere. Use when the owner says "check listings", "check closures", "refresh hours", "audit my listings", "what's missing", or on its schedule.
---

# Listing Check

## Playbook card (show this to the owner)

Show this card to the owner before setting the helper up (onboarding plan or "add a helper"), so they see and approve the process.

**What it does:** keeps every listing true: open or closed, hours, phone, website, map spot, and that it's the right kind of business.
**Why it works:** official sources beat other directories, and anything big (a closure, a type change) needs two sources that agree. Copycat sites are never proof.
**How I work:**
1. Each run I take the listings checked longest ago.
2. I look each one up on Google and on the business's own website, matching the exact street address, never just the name.
3. Small facts (hours, phone, website) change only when a trusted source shows them for that exact place.
4. Closures and "is this the right kind of business?" need two agreeing sources, and I never delete anything.
5. Unclear cases go to you as questions, never guesses.
**You approve:** every change, until you tell me which kinds are safe to make on my own. A whole chain's changes are one approval.
**Cadence:** weekly small batches. I tell you the real cycle from your numbers (listings ÷ batch size, e.g. 160 listings at 40 a week = each one about monthly) and never promise more. When one chain changes hours everywhere, I check all its locations in one sweep instead of waiting weeks. Quiet weeks are cheap.
**What you get:** a short weekly message (the biggest problem first, at most 3 decisions), with every fix, its source link and the exact words from that page in a full report. Plus broken website links, a check that your own pages show Google the right hours, and a running count of missing details.
**What I need from you:** access to your list of businesses.
**Make it yours:** "check 50 a week", "gas stations with a car wash count", "never trust Yelp".

**Onboarding sample:** 10 to 20 listings checked, with the proposed fixes and the source link plus quoted value for each; their website links tested; the chain sweep when 3 or more of them drift the same way; the "what your site shows Google" check on one live listing page; and the missing-details count.

**If a step fails** (blocked site, thin data, noisy results): try the fallback this skill documents, and still deliver the best honest sample. Never end with less than the onboarding sample without telling the owner, in plain words, what blocked it and the fix.

Goal: every listing a visitor sees is correct today. Wrong hours, a dead link or a closed business sends people on a wasted trip, and that kills trust and traffic.

**Details live in `REFERENCE.md` (same folder).** Each step below names the section to read. Read it when you reach that step; don't guess.

## Before every run

- Read `sites/<slug>.yaml` (section `listing_check`) and `notes/<slug>.md` (sections "Listing rules" and `## Keep listings accurate rules`; follow them exactly). No notes file: create it with a 3 line header (site name, URL, "Listing rules:" plus the listing type). No `listing_check` section: run Step 0 (never copy `sites/example.yaml` wholesale).
- Files go under `$DIROPS_REPO/notes/<slug>/` (default `/data/workspace/directory-ops/notes/<slug>/`), never `/tmp`. Make `notes/<slug>/tmp/` when needed.
- Tell the owner once, plainly: "I'll check Google and each business's own website. I can't log in to Facebook or read hours that are only in pictures. Pages may take up to a day to show changes."

## Hard rules (never break these)

1. **All database reads and writes** go through `/data/skills/directory-ops/directory-db/db.py --key-env <database.key_env> --allowed-tables <listing tables>`. Write only fields in `listing_check.fields`, only when `auto_apply` is true or the owner approved. Otherwise proposals go to `notes/<slug>/pending.md` (review-changes format, one block per listing; ids continue from the highest id already there). → REFERENCE.md#writes
2. **First run ever:** max 20 listings, writes nothing (even with `auto_apply`), every change is a proposal.
3. **Never delete a listing.** Never touch page URLs or slugs, page structure, owner-added photos, reviews, SEO fields, or anything under "Never touch" in the notes. Never change site code.
4. **The one evidence rule.** Hours, phone, website: the business's own page for this exact location, OR Google with `usable: true` (own page wins if they disagree). Identity (name, address, city), type and closure: 2 agreeing sources, one official; identity is never changed automatically. Less than that: don't change it, log `needs_review`. → REFERENCE.md#sources
5. **Never evidence:** other directories, competitors, listicles, aggregators, AI summaries, `untrusted_domains`, the site's own domain, and pages that copy our listing word for word.
6. **Match by full street address** (number + street), never by name or nearby city. The stored address line is the truth.
7. **Before every proposal or write, read the live row** (`db.py select --where "id=eq.<id>" --limit 1`) and use its current values as `old`. Never propose a value equal to the current one.
8. **Every proposal shows its evidence:** for each source you name, the link and the exact value it shows. Never write "Chain page + Google" unless both are shown with their values. No link + quote = it doesn't go to the owner.
9. **Hours are rendered by `hours_style.py`, never by you.** Change hours only when a day differs by 30 minutes or more, or open vs closed. → REFERENCE.md#decide
10. **Never call something closed, unconfirmed or "not found" from one tool.** Search like a person first: `<name> <full address>`, read the results page.
11. **Count carefully** and recount every number with a second query before reporting it.
12. **The owner's message is at most about 600 words and at most 3 decisions.** Everything else goes in the report file. Never estimate credits; point to the Hermes usage page.

## Step 0: Settings (first run only)

If `listing_check.settings_done` is not `true`: ask one question per message, defaults shown ("use the defaults for the rest" ends it). In quick mode (onboarding) ask only `[essential]` questions onboarding hasn't answered. Questions, config mapping, proof words, log storage, cadence math: → REFERENCE.md#settings. Then "Teach me your way" (one optional question) and "learn from corrections": → REFERENCE.md#teach-me. Save, set `settings_done: true`, never ask again.

## Step 1: Pick this run's batch

Oldest `checked_at` first (no log yet: `--order "updated_at.asc,id.asc"`), up to `batch_size`, skipping anything checked within `min_days_between_checks`. "Coming soon" and "temporarily closed" listings are checked EVERY run on top of the batch. → REFERENCE.md#batch

## Step 2: Check each listing (stop early when clear)

```
python3 /data/skills/directory-ops/listing-check/gmaps_lookup.py --listing "<listing name>" "<address line exactly as stored>" "<type keyword>"
```
Read `usable` (and `why_not_usable`), never `status`. → REFERENCE.md#google

- **Pass 1, still there?** Google, then search like a person if unclear. No website: own social posts in the last 60 days.
- **Pass 2, right kind of business?** Existing listings are presumed correct; flag only on evidence AGAINST. Photo check only when adding a listing or when type is in question.
- **Pass 3, details current?** Compare each field in `listing_check.fields` with the best source. Host business rule, archive fallback, prices, social links, coordinates: → REFERENCE.md#check
- A script gets 403 or `blocked_by_security` on an official page: read it with your built-in web reader (max 20 per run).

## Step 2b: Website links (every listing you checked)

```
python3 /data/skills/directory-ops/listing-check/link_check.py notes/<slug>/tmp/links.txt --out notes/<slug>/listing-check/links.jsonl
```
(`links.txt` = one `<id><TAB><stored website>` per line.) Broken, homepage, list-page or glued-tracking links get a proposal with a **tested** clean location link (the script's `suggest`, or the location page you found in Step 2, tested with `--url`). Tracking tags on working links are cosmetic: one bulk line, never one approval each. → REFERENCE.md#links

## Step 2d: Whole-site link check (first run, then every 30 days)

Run it on the first run ever and when the last `link_sweep` line in `notes/<slug>/listing-check/log.jsonl` is 30+ days old. No AI cost, about 1 second per link, so start it in the background and continue:
```
python3 /data/skills/directory-ops/directory-db/db.py select --site-url <database.url> --key-env <key_env> --table <listings table> --columns id,<website column> --where "<active filter>" --all > notes/<slug>/tmp/all-sites.json
python3 /data/skills/directory-ops/listing-check/link_check.py notes/<slug>/tmp/all-sites.json --column <website column> --max 3000 --delay 0.5 --out notes/<slug>/listing-check/link-sweep.jsonl
```
Group every fix with a tested `suggest` under ONE heading in pending.md, `## Website link fix (<n> listings): ids <first>-<last>`, approved with one reply: "approve link fix". Owner summary, one line with the real total: "<n> website links on your listings are broken (tracking text glued into the address, dead pages). Fix waiting: say 'approve link fix'." Broken links with no tested suggestion: `needs_review`. Working links with tracking tags: one cosmetic line, count only. Log one `link_sweep` line with counts by status. → REFERENCE.md#links

## Step 2c: Chain sweep (when 3+ listings of one chain drift the same way)

3 or more listings sharing one website domain with the same kind of change = the chain probably changed everywhere. Tell the owner in one line with the time cost, then:
```
python3 /data/skills/directory-ops/listing-check/chain_hours.py notes/<slug>/tmp/chain-<domain>.txt --out notes/<slug>/listing-check/chain-<domain>.jsonl
```
Max 300 per run. Group all its proposals under `## <Brand> sweep (<n> listings): ids <first>-<last>` in pending.md, so the owner approves it with ONE reply: "approve <Brand> sweep". In chat: the pattern, 3 example rows, the approval line. Test the sweep's links too. → REFERENCE.md#chain-sweep

## Step 3: Decide and write

Use the decision table (unchanged, updated, closed, opened, needs_review, not_found, wrong_place, shared phone…) and the hours and format rules: → REFERENCE.md#decide. Log every listing (file log by default: `notes/<slug>/listing-check/log.jsonl`).

## Step 3b: What your site shows Google (once per run, read only)

Open one live listing page you just checked; read its structured data hours (`chain_hours.py --url <page>`), any "open now" text, and the visible hours. Report **only real impact**: wrong hours in the structured data (Google shows them) or a wrong "open now" status is the first line of the summary. A wrong time zone label next to correct local hours is a **cosmetic** fix, said as such. Check the time zone is actually used before claiming it changes any time. → REFERENCE.md#site-check

## Step 4: Missing details and duplicates (every run, read only)

Across ALL active listings: empty or placeholder values per key field, thin descriptions, and duplicates (only same street address or same phone; same name at different addresses is a chain). Recount before reporting; log one `missing_summary` line. → REFERENCE.md#missing

## Step 5: Summary

Write the full report to `notes/<slug>/listing-check/YYYY-MM-DD.md`. The last message of the run (what the scheduler delivers) is short, plain words, no file or field names:

```
[Biggest real problem first, if any: "Google sees the wrong hours on your pages: …"]
Listing check <date>: <N> checked (add "full pass complete" when fewer than the batch were due).
Waiting for your approval: <n> (<Brand> sweep: <n>, say "approve <Brand> sweep")
Needs your review: <n> (<one short example>)
Closed / opened: <n>. Broken website links (whole site): <n>, say "approve link fix".
Full report: say "show the full listing report"
```
At most 3 decisions, each with your recommended answer. Report contents, autonomous mode, and pushing notes: → REFERENCE.md#report. Cost and cadence wording: → REFERENCE.md#cost
