---
name: page-copy-refresh
description: Keeps the descriptive paragraph copy on a directory's pages fresh, accurate and specific, e.g. the intro text at the top of a state, city or category page, or the homepage intro. Every few months (default every 4) it rewrites that copy with the same meaning and keywords in new words, using real facts from the site's own listings. It never touches listing information (names, addresses, phones, hours, prices, photos, reviews), headings, titles, URLs, links or blog articles. Updates the page's real "last updated" date. Use when the owner says "refresh the page copy", "refresh the state pages", or on its schedule.
---

# Page Copy Refresh

## Playbook card (show this to the owner)

Show this card to the owner before setting the helper up (onboarding plan or "add a helper"), so they see and approve the process.

**What it does:** rewrites the intro paragraphs on your location and category pages every few months, with fresh wording and real facts, without touching anything that ranks.
**Why it works:** fresh, specific, true copy keeps pages current for Google and AI search. Titles, headings and URLs are what rank, so they're never touched.
**How I work:**
1. You confirm which paragraphs on one example page I may refresh.
2. I pull real facts per page from your listings (counts, hours, what's special).
3. I write each page by hand: plain words, at least two facts unique to that place, no hype.
4. A checker blocks invented numbers, copy-paste sentences across pages and banned phrases.
5. You see a sample of 3 pages before anything is saved.
**You approve:** the first sample, then it runs on schedule.
**Cadence:** once every 3 to 4 months for the whole site. More often just looks spammy.
**What you get:** every intro rewritten, with a "last updated" date that's real.
**What I need from you:** your site showing that text from your database (a one-time change I'll explain).
**Make it yours:** "mention our free guide", "never say 'hidden gem'", "keep it under 80 words".

**Onboarding sample:** 3 pages rewritten, shown side by side with the current text.

**If a step fails** (blocked site, thin data, noisy results): try the fallback this skill documents, and still deliver the best honest sample. Never end with less than the onboarding sample without telling the owner, in plain words, what blocked it and the fix.

Goal: every location and category page gets intro copy that is current, specific to that place, and honest. Full detail for every step: `REFERENCE.md` (same headings).

## Before every run

1. Read `sites/<slug>.yaml` (section `page_copy_refresh`) and `notes/<slug>.md` (sections "Content", "Never touch", `## Fresh page text rules`). No notes file: create it with a 3 line header (site name, URL, "Content rules:"). No `page_copy_refresh` section: run Step 0 (never copy `sites/example.yaml` wholesale).
2. Files go under `$DIROPS_REPO/notes/<slug>/`, never `/tmp`.

## Hard rules

1. **Refresh only the descriptive paragraphs the owner confirmed** (`fields`). Never listing information (names, addresses, phones, hours, prices, photos, reviews, ratings, listing links), headings, titles, meta descriptions, URLs, slugs, breadcrumbs, schema, links, buttons, layout, or blog articles. A paragraph with one business's address, phone or hours is listing information. Unsure = leave it. Full table: REFERENCE.md § What this touches.
2. **Never add links** to these fields (the internal-links skill changes the template instead).
3. **Write every page yourself, as a writer.** Never generate copy with code, templates, f-strings or fill-in-the-blank sentences. Scripts only gather facts and check copy.
4. **Every number, time and place name comes from this page's Step 2 data.** Never invent facts, history, prices or claims. Only open, active listings count (`active_filter`).
5. **Nothing is written until `copy_check.py` passes** and the 3-page sample check passes.
6. **Never create new rows** in the copy table; places without a page are "page ideas" for the owner.
7. You can't change site code: copy that lives only in code needs the owner's one-time site change (Step 0). Tell the owner once in plain words what you do and never do (REFERENCE.md § What you can and can't do).

## Step 0: Settings and one time setup (first run only)

1. **Is there a live page?** [essential] "Is your site live, and does this intro text show on a page? Paste one page URL." No → stop, tell them you'll run once it's live, mark "waiting for live site" in `notes/<slug>.md`.
2. If `settings_done` isn't `true`: ask the 4 questions in REFERENCE.md § Step 0 one per message, defaults shown (quick mode: only `[essential]` ones onboarding hasn't answered; list defaults used). Map to `every_months`, `scope`, `brand_promise`, `promote`. All config keys and defaults: REFERENCE.md § Step 0 "Config keys".
3. **Copy table:** use a table the site already reads page text from (check with `db.py select --limit 3`, confirm by quoting one text and the live page it appears on; map `table`, `columns.key`, `columns.type`, `fields`). **No such table:** give the owner the one-time site-change prompt (REFERENCE.md § Step 0), mark "waiting for site change", stop.
4. **Prerequisites before the first write:** a live page shows this copy · do tokens render (a literal `{count}` on the page or the owner's word → `tokens_render: false`, write real numbers and re-render each run) · `active_filter` recorded.
5. **Pick the blocks with the owner** on one example page per type: every block you'd refresh and every block you'd leave alone, and why. Only confirmed blocks go in `fields`.
6. **Teach me your way** (one optional question; wording in REFERENCE.md § Teach me your way): 3 to 7 rules saved under `## Fresh page text rules`. **Learn from corrections:** ask once "Want me to remember that as a rule for next time? (yes/no)".

## Step 1: Scope and timing

- One run every `every_months` (default 4) refreshes **every page in scope in one pass**. Cron fires only on those months (e.g. 11am on the 1st, every 4 months), never weekly.
- **First run ever:** 3 pages per type, write nothing, show before/after side by side, ask "go". After that, full passes run automatically unless `approval: every_run`.
- Skip pages refreshed in the last `every_months`.

## Step 2: Facts per page (one query each)

Current copy (copy table, else the live page) · real facts for this place with `active_filter`: active count, cities/areas, earliest open / latest close, Sunday openings, price range if any, new or coming soon · the keywords the current copy uses (keep them).

## Step 3: Write (groups of about 10, check as you go)

1. **Same job, new words.** Length within 20% of old copy (old under 25 words: write 40 to 90).
2. Every fact true and checkable; 1 or 2 real facts per page.
3. **Know what each token renders to** (`token_meanings`); never a word token where a number belongs. **Main listing count always uses the count token** ("{count} <listing type> {locations}").
4. Keep the old keywords once or twice. Plain 6th to 8th grade words; no nicknames, slang, filler or AI tells ("nestled", "boasts", "look no further"…).
5. Confident, not hedgy. **Positives only**: never gaps, problems or anything internal.
6. Promote `promote` items only where data shows they exist here, with the real count, never prices.
7. **Written for its place:** intro or middle names at least 2 real things about this place; different opening and structure from the last 3 pages.
8. Plain text: no headings, no links, no em dashes.

**Brand statement** (1 to 2 sentences in `brand_statement_field`; one-field tables: the last sentence): brand name every time · covers every <listing type> in <place> (only if true) · what it verifies · **how often, computed and TRUE** (active listings ÷ `listing_check.batch_size`, rounded up, at the cadence of `jobs.listing-check`; listing-check not scheduled → leave frequency out and make no checking claim) · the owner's `brand_promise`. The brand makes the claim; no hedging. Details and example: REFERENCE.md § The brand statement.

## Step 4: Quality gate (before any write)

```
mkdir -p $DIROPS_REPO/notes/<slug>/tmp
python3 /data/skills/directory-ops/page-copy-refresh/copy_check.py $DIROPS_REPO/notes/<slug>/tmp/pages.json --brand "<brand name>" --brand-field <brand_statement_field> --tokens "<tokens from config>"
```
`pages.json` holds every page's RENDERED copy, place, area names, template copy and `facts` (format: REFERENCE.md § Step 4). Then read it yourself: render tokens and read the result · no sentence except the brand statement matches another page once place names are removed · keywords kept · a 12 year old understands it · brand statement complete and true. A failing page gets up to 2 hand rewrites, then is skipped and logged.

**Step 4b:** before any run of more than 10 pages, render 3 random pages and re-check them; any failure → stop and fix the run.

## Step 5: Write and log

- `auto_apply` true (after the first approved run): upsert one row per page (`content`, `updated_at = now()`, `updated_by = 'page-copy-refresh'`), or for a mapped existing table update the row matched by `columns.key`, only the `fields` columns it really has (`--touch` its updated-at column). Otherwise write to `notes/<slug>/pending.md`.
- Call the site's revalidate URL if configured. The "last updated" date moves only because the copy truly changed.
- **Owner summary** (or `notes/<slug>/page-copy/YYYY-MM-DD.md` if `autonomous`): plain words, max 6 lines: pages refreshed, one before/after, pages skipped and why, page ideas. Onboarding sample: about 600 words max, at most 3 decisions with a recommended answer.
- Commit and push `notes/` (CATALOG.md rule 6).

**Allowed writes:** the copy table in the config, `notes/<slug>/`, `sites/<slug>.yaml` (Step 0 only). **Cost:** one query and one write per page, no web searches; report the run's cost.
