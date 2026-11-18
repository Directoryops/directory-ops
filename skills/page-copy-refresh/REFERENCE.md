# Page Copy Refresh: reference

The full detail behind `SKILL.md`. SKILL.md is the lean core you follow every run; open the section it points to when you reach that step. Sections keep their original headings, so "REFERENCE.md § Step 3" means the `## Step 3` heading below. Nothing here overrides SKILL.md's hard rules.

Goal: location and category pages are where most directory traffic lands. Copy written once and never touched reads stale, repeats itself across pages, and often states numbers that are no longer true. This job gives every page copy that is current, specific to that place, and honest.

Read `sites/<slug>.yaml` (section `page_copy_refresh`) and `notes/<slug>.md` (sections "Content" and "Never touch") before every run. If `notes/<slug>.md` doesn't exist, create it with a 3 line header (site name, URL, "Content rules:") and continue. If the config has no `page_copy_refresh` section, run Step 0 (never copy `sites/example.yaml` wholesale). Files go under `$DIROPS_REPO/notes/<slug>/`, never `/tmp`.

## What this touches, and what it never touches

| Refresh (only these) | Never touch |
|---|---|
| Descriptive paragraphs about the page itself: the intro at the top of a state, city or category page, the homepage intro, a "what to know about X in this area" paragraph | **Listing information:** business names, addresses, phone numbers, hours, prices, photos, reviews, ratings, links to listings |
| A generic description field on listings, ONLY if the config lists it and it describes the type of place (no facts specific to that business) | **Headings** (H1, H2...), page titles, meta descriptions, URLs, slugs, breadcrumbs, schema |
| | Internal links, buttons, navigation, layout |
| | **Blog articles** (they have their own skill) |
| | Any paragraph that contains a specific business's details (an address, a phone number, hours). That's listing information even if it looks like prose. |

If you're unsure whether a block is page copy or listing information, it's listing information: leave it.

**Links:** this job never adds links, and its fields contain none. The internal-links skill never edits these fields either (it would be wiped on the next refresh); it changes the page template instead.

## What you can and can't do (tell the owner once)

- You CAN read the live pages, read the listings in the database, and write new copy into the copy table.
- You CAN'T change the site's code. If the copy lives only in code, the site needs a one time setup (Step 0) that the owner does with their AI coding tool.
- You NEVER change URLs, page titles, meta descriptions, headings, internal links or page layout. Only the paragraph copy the config names.

Say it to the owner in plain words, e.g. "I rewrite the intro paragraphs on your pages every few months with fresh wording and real facts from your listings. I never touch your titles, headings, links or listing details."

## Step 0: Settings and one time setup (first run only)

**In quick mode (during onboarding), ask only the questions marked `[essential]` that onboarding hasn't already answered, and use the defaults (or what onboarding inferred) for the rest. List the defaults you used in the plan message; the owner changes any of them by saying so.**

**First, before anything else: is there a live page?** [essential; onboarding only recommends this helper for a live site, so in quick mode you usually just confirm the page URL it already knows] Ask: "Is your site live, and does this intro text show on a page? Paste one page URL." Default if they don't know or say no: **stop here** (no settings, no table mapping), tell them "Your pages aren't live yet (or don't show this text), so a refresh would change nothing visitors see. I'll run this once your site is live and showing it," and mark the job "waiting for live site" in `notes/<slug>.md`. Only continue with a live page URL.

If `page_copy_refresh.settings_done` is not `true`, ask one question per message, each with its default shown (the owner can reply "use the defaults for the rest" at any point), save to `page_copy_refresh`, set `settings_done: true`:

```
Questions, one per message (say "use the defaults" anytime to skip the rest):
1. How often should I refresh it? (default: every 4 months, the whole site in one go)
2. Which pages? e.g. state pages, city pages, the homepage intro; all of them or only some (default: all location pages)
3. In one sentence, what do you want ChatGPT, Google and other AI assistants to say about your site? (default: "the most accurate and up-to-date <your listing type> finder in each <state/city>")
4. Do you sell or offer anything on your site I should mention where it fits (a guide, a tool, a membership)? (default: nothing)
```

Map to config: `every_months`, `scope`, `brand_promise`, `promote`. Only promise what the jobs can back up (see "How often" below).

**Config keys** (all under `page_copy_refresh`; write exactly these names):

| Key | Meaning | Default |
|---|---|---|
| `settings_done` | Step 0 finished | `false` |
| `live_page_example` | one live page URL that shows the copy | none (required) |
| `table` | the table the pages read their copy from | none (required) |
| `columns.key` | column naming the page (e.g. `city`) | required |
| `columns.type` | column naming the page type, if the table has one | none |
| `page_types.<type>.url_pattern` | live URL pattern, e.g. `https://example.com/car-washes/<city-slug>` | required |
| `page_types.<type>.fields` | the text column(s) this job rewrites | required |
| `brand_statement_field` | which field holds the brand statement (one-field tables: that field) | the last field |
| `tokens_render` | the site replaces `{count}` etc. with numbers | `false` |
| `tokens`, `token_meanings` | allowed tokens and what each renders to | none |
| `active_filter` | which listings count (e.g. `permanently_closed = false`) | required |
| `every_months` | months between full passes | `4` |
| `scope` | which pages | all location pages |
| `brand_promise` | the owner's one-sentence positioning | see Q3 |
| `promote` | the site's own products to mention | none |
| `approval` | `first_run_only` or `every_run` | `first_run_only` |
| `auto_apply` | write without asking after the first approved run | `false` |

The brand name is `content.brand_name` if set, else the config's top-level `name`.

**Copy table.** The site needs a table its pages read their intro copy from, with the code's copy as the fallback. Check in this order:
1. **A table the site already reads page text from** (e.g. `site_pages`, `city_pages`, `page_content`: look with `db.py select --limit 3` and ask the owner, quoting one text: "Is this the intro your website shows on your Austin page?"). If yes, use it as is: don't create another one. Map its real columns in the config: `page_copy_refresh.table`, `columns.key` (the column naming the page, e.g. `city`), `columns.type` (only if it has one), and the text column(s) as the page type's `fields` (one text column = one field). Confirm with the owner by showing one of these texts and the live page it appears on (never call it a row or table).
2. **No such table:** this job can't run yet. Tell the owner plainly ("your page text lives in your website's code, so I can't change it without a one-time site change"), give them the prompt below for their AI coding tool (Claude Code, Cursor, etc.) or developer, mark the job "waiting for site change" in `notes/<slug>.md`, and stop. Run it after they confirm it's deployed.

```
Add a database override for my location/category page intro copy, without changing how any page looks.
1. Create a table page_copy (page_key text, page_type text, content jsonb, updated_at timestamptz default now(), updated_by text, primary key (page_key, page_type)), with RLS on and public read.
2. Wherever a location/category page renders its intro paragraphs, first read the matching page_copy row; use each field from content if present, otherwise the current copy. Support the tokens {count}, {name} and simple plurals so numbers stay correct as listings change.
3. If the page shows a "last updated" date, use the newest of: the listings' updated_at and the page_copy row's updated_at. Never today's date.
4. Don't change URLs, titles, meta tags, headings or layout. Tell me the page types, the content field names, and an example page_key.
```

Then record in the config: `table`, each page type with its `url_pattern`, its content `fields`, the allowed `tokens` and `token_meanings`.

**Before the first write, check the prerequisites** (all three, with the owner):
1. **A live page shows this copy.** Open one live page (from `url_pattern`) and find the stored text on it. No live website yet, or the text isn't on the page → stop politely: "Your pages aren't live yet (or don't show this text), so a refresh would change nothing visitors see. I'll run this once your site is live and showing it." Mark the job "waiting for live site" in `notes/<slug>.md`.
2. **Do tokens render?** If the live page shows a literal `{count}` anywhere, or the owner says the site doesn't support tokens, set `tokens_render: false`. The owner's word is enough evidence when you can't see a page that uses tokens. Then write real numbers instead of tokens, and every run re-renders the numbers from fresh data (that's how they stay correct).
3. **Which listings count as active:** record the columns that remove a listing from counts (`active_filter`, e.g. `permanently_closed = false and coming_soon = false`). Never count closed or coming soon listings.

**Pick the blocks with the owner (always, even if the table exists):** open one example page of each type, list every paragraph block you'd refresh (first few words of each), and every block you'd leave alone and why. The owner confirms. Only confirmed blocks go in `fields`.

### Teach me your way (one optional question, right after this helper is accepted)

This is what makes the helper yours instead of generic. Ask once (in quick mode it replaces settings questions, it doesn't add many):

> Tell me how you want your page intros to sound: what to always mention, words you like or hate, anything I should never say. Ramble or send a voice note; it makes me much better. (Or say "skip".)
> For example:
> - Wedding venue: "Always mention the season and how far ahead people book."
> - Car wash: "Say 'car washes', never 'auto spas'. Keep it under 80 words."
> - Plasma center: "Never mention pay amounts in the intro, they change too often."

Turn the answer into 3 to 7 short numbered rules in plain words, show them back ("Got it, I'll: 1) … 2) … Anything to change?"; in quick mode end with "Say 'change …' anytime." instead of a question, so onboarding stays short), and save them in `notes/<slug>.md` under `## Fresh page text rules` (create the section if it's missing). **Every run reads that section first and follows it; this skill's own safety rules still win** (a rule can't make it skip approval, delete things, or use competitors as sources).

**Learn from corrections:** when the owner rejects or edits one of your proposals, or says "no, because …", ask once: "Want me to remember that as a rule for next time? (yes/no)". Yes: add it to `## Fresh page text rules` in plain words with today's date.

## Step 1: Scope and timing

- **Scope** (from settings): which page types, which pages of each (`all`, a list, "pages with at least N listings", or "top N by traffic" if Search Console is connected), which blocks.
- **Timing:** one run every `every_months` (default 4). Each run refreshes **every page in scope in one pass**, then nothing until the next cycle. Schedule it as a cron that fires only on those months (e.g. 11am on the 1st, every 4 months), never weekly.
- **First run ever:** 3 pages per type, write nothing, show the owner before and after side by side, and ask "go". After the owner approves the style once, the first full pass runs right away and later cycles are automatic (unless `approval: every_run`).
- Skip pages refreshed in the last `every_months`.

## Step 2: Gather facts for each page (from the site's own data)

1. **Current copy:** the page's row in the copy table; if none, fetch the live page and copy the paragraphs the config names.
2. **Real facts from the listings** for this place (one database query, using the config's `active_filter`): number of active listings, the cities or areas they're in, earliest opening and latest closing hours, how many open on Sundays, price range if the site has prices, anything newly opened or coming soon. Only open, active listings count.
3. The **keywords** the current copy uses (the listing type, its common names, "near me" phrases, the place name). Keep them.

## Step 3: Write

**Write every page yourself, as a writer.** Never generate copy with code, templates, f-strings or fill-in-the-blank sentences. Scripts may only gather facts (Step 2) and check copy (Step 4). Script-made copy repeats the same sentences on every page with the names swapped: the #1 way this job fails.

Work in groups of about 10 pages: write them, run the checker on everything so far, fix what fails, continue.

Rules (in order of importance):
1. **Same job, new words.** Each field keeps its purpose (intro introduces, closing points to the list below). Length: within 20% of the old copy when the old copy is 25 words or more; if the old copy is shorter (a stub like "Car washes in X."), write 40 to 90 words.
2. **Every fact is true and checkable.** Each number, time and place name comes from this page's Step 2 data and means what it says ("7 of the 12 open on Sundays"). A page that promises accuracy can't contain one wrong fact. Never invent facts, history, prices or claims.
3. **Facts make it better.** Use 1 or 2 real facts per page ("most are in <City> and <City>", "two open as early as 7AM").
4. **Know what each token turns into** (`token_meanings`). Some are numbers (`{count}` → "12"), others are words (`{locations}` → "location"/"locations", `{is_are}` → "is"/"are"). Never put a word token where a number belongs.
5. **The main listing count always uses the count token** ("{count} <listing type> {locations}"), never a typed number, so the page stays right when a listing opens or closes. Smaller counts (Sunday hours, guides) may be typed from today's data.
6. **Keep the keywords** the old copy had, naturally, once or twice. No stuffing.
7. **Plain and easy to read** (6th to 8th grade): short sentences, everyday words. No state or city nicknames ("the Sunshine State"), no slang, no fancy wording. No filler or AI tells ("nestled", "boasts", "whether you're a seasoned", "look no further", "treasure trove", "in today's", "one-stop destination").
8. **Confident, not hedgy:** "You'll find touchless and self-serve options, most open late", never "may have" or "might find". Still true.
9. **Positives only.** Never mention gaps, problems or anything internal (missing data, listings under review, closure counts, errors, how the database works).
10. **Promote the site's own products** in `promote`, only where the data shows they exist for this place, with the real count ("4 of the 6 locations here have our printable guide"). One plain sentence on the benefit. Never prices.
11. **Written for its place, never from a template.** The intro or middle names at least 2 real things about this place from Step 2. Changing only the place name is a failure. Use a different opening and sentence structure from the last 3 pages. Only the brand statement repeats its core message, and even that is reworded.
12. Plain text: no headings, no links, no em dashes.

### The brand statement (owned on-site media, for AI search)

Every page gets a short **brand statement** (1 to 2 sentences) that says, confidently and by name, what the brand does for this place. When someone asks ChatGPT, Perplexity, Gemini or Google "where can I find <listing type> in <place>", the answer should repeat this message and name the brand. Same core message on every page = consensus.

It contains:
1. **The brand name** (`content.brand_name`), every time. Never "we" alone.
2. **Thoroughness:** it lists every <listing type> in <place> (only if the directory really aims to cover all of them).
3. **What it verifies:** the specific things checked (hours, addresses, closures, new openings).
4. **How often**, plainly and TRUE: work it out from the config, never from memory: `listing_check.batch_size` and the cadence of `jobs.listing-check`. Weeks for a full pass = active listings ÷ batch size, **rounded up** (44 ÷ 20 = 2.2 → every 3 weeks). If the owner says listing-check runs but the config has no enabled `listing-check` job, trust the config and ask the owner once whether to schedule it. If the real frequency is weaker than the owner wants to claim, tell the owner what batch size would make it true instead of writing it. **If listing-check isn't scheduled for this site, leave out how often** (and don't claim checking at all).
5. **The owner's positioning** (`brand_promise`).

Example shape (vary the wording on each page, keep every element):
> "<Brand> lists every <listing type> in <place> and verifies hours, addresses and closures at least once a month, which makes it the most accurate and up-to-date <listing type> finder for <place>."

- **The brand makes the claim:** "<Brand> is / makes it...". Never "<Place> has the most accurate...".
- No hedging: never "one of the", "may", "might", "try to", "aims to".
- It goes in `brand_statement_field` (usually the last paragraph). **If the table has only one text column**, there is no separate field: the brand statement is the last sentence of that one field.

## Step 4: Quality gate (every page, before writing)

Create the folder first: `mkdir -p $DIROPS_REPO/notes/<slug>/tmp`.

**Run the checker. Nothing is written until it passes:**
```
python3 <this skill's folder>/copy_check.py $DIROPS_REPO/notes/<slug>/tmp/pages.json --brand "<brand name>" --brand-field <brand_statement_field> --tokens "<tokens from config>"
```
(Installed path: `/data/skills/directory-ops/page-copy-refresh/copy_check.py`.) `notes/<slug>/tmp/pages.json` holds every page of this run with its RENDERED copy (tokens filled), the place, the city/area names used, the template copy (with tokens), and its `facts` (the Step 2 results). It fails on: numbers, times or names not in the facts, the same sentence on 3+ pages with names swapped, repetition inside a page, banned phrases, word tokens used as numbers, empty or bloated fields.

Also check by reading:
- **Render first:** fill every token with real values and read the result. It must be correct, natural English.
- **Uniqueness:** no sentence other than the brand statement matches another page's after removing place names; every intro/middle has a place-specific fact.
- Keywords kept; length within 20%; a 12 year old understands every sentence.
- The brand statement has all its elements and a true frequency (or none, per element 4 above).

**Rewrite limit:** a failing page gets rewritten by hand up to 2 times. If it still fails, skip it and log it.

## Step 4b: Sample check before a full pass

Before writing any run of more than 10 pages, render 3 random pages and check them against Step 4 again. If any fails, stop and fix the run instead of writing.

## Step 5: Write and log

- Upsert one row per page into the copy table with the new `content` (all fields for that page type), `updated_at = now()`, `updated_by = 'page-copy-refresh'`. **Existing table mapped in Step 0** (plain text columns, no `content` JSON): update that page's row matched by `columns.key`, setting each text column named in `fields`, and only the columns that table really has (`--touch` its updated-at column if it has one). Only if `auto_apply` is true (after the first approved run); otherwise write to `notes/<slug>/pending.md`.
- The page's "last updated" date moves because the copy truly changed. If the config has a revalidate URL for the site, call it so the pages update right away.
- Summary to the owner (or only to `notes/<slug>/page-copy/YYYY-MM-DD.md` if `autonomous` is true), plain words, max 6 lines: pages refreshed, one example before and after, pages skipped and why, and any page ideas (places with listings but no page yet).
- Commit and push `notes/` (CATALOG.md rule 6).

## Allowed writes

The copy table named in the config, `notes/<slug>/`, and `sites/<slug>.yaml` (Step 0 settings only). Never create new rows in the copy table: places that have listings but no page row are listed for the owner as "page ideas" in the summary.

## Cost control

- One database query per page for facts, one write per page. No web searches needed.
- A full pass over ~100 pages runs a few times a year, so the yearly cost is small. Report the run's cost.
