# Job Catalog

Every job Hermes can run for a directory. The onboard-site skill reads this file to build a **game plan** for the owner's goal (more traffic, accurate listings, leads, richer pages): 3 to 6 helpers, each with why it fits their site, how often it runs and what they get in month 1. The owner picks which to set up; each chosen helper then gets its own mini-onboarding from the `## Playbook card` in its SKILL.md (what it does, why it works, how I work, you approve, cadence, what you get, what I need, make it yours, onboarding sample), a real sample, and its schedule. `onboard-site/onboard_next.py` tracks the steps so onboarding never ends before every chosen helper has shown its sample (or the owner knows why not and how to fix it).

After onboarding, the owner can add any job later by saying "add the <X> helper" or "what else can you do?": onboard-site's "Adding a helper later" section runs the same per-helper flow (Playbook card → "Teach me your way" → connect → sample → schedule). One-time manual steps (keys, mailbox passwords, photo storage, Search Console downloads, pasting a prompt into Claude Code) always use the shared guides in `skills/setup-guides/`.

Status: `ready` = skill exists in /skills. `planned` = not built yet (onboarding can still recommend it and put it on the roadmap).

| # | Job | What it does | Best for | Cadence | Status |
|---|-----|--------------|----------|---------|--------|
| — | setup-guides | Click-by-click guides for one-time setup steps (adding a setting in Hostinger, Gmail app password, Supabase key, GitHub access key, photo storage, Search Console download, pasting a prompt into Claude Code). Used by every other job; never scheduled. | All | — | ready (helper) |
| 0 | reddit-listing-research | Reads real Reddit conversations (free public archive, never reddit.com) to learn what people need to know before choosing a business in the niche, turns it into 8 to 15 listing fields, fills them from each business's own website with an exact quote as proof (a checker rejects anything not on the site), then writes only owner-approved values. | All, especially new directories with thin listings | Once, then for new listings | ready |
| 2 | listing-check | Re-checks listings (oldest first, small batches): still open, still the right type of business, hours, address, prices, social links. Marks closures, never deletes. Also reports missing details and duplicates across all listings (replaces listing-audit). No setup tables: logs live in notes/. | All listing sites | Weekly batches (each listing about monthly) | ready |
| 4 | inbox-triage | Reads a site inbox read only (never replies), ignores spam, verifies and adds new listings (with a free exterior photo), checks closure and correction reports, turns news alerts into "coming soon" listings. | All with a contact form | Weekly | ready |
| 5 | missing-info-outreach | Drafts emails to businesses asking them to confirm prices or claim their listing. | Lead gen, traditional | Weekly | planned |
| 6 | lead-routing | Checks each lead is real, emails it to the matching business (first lead free), one follow up, reroutes nearby if no reply, auto replies to interested businesses. Takes inventory of which businesses have an email first, and can find missing ones on their own websites (free, no AI reading). | Lead gen | Every 2 hours | ready |
| 7 | page-copy-refresh | Rewrites the intro copy on location/category pages every few months: same meaning and keywords, new words, real facts from the listings, numbers as tokens. Never touches URLs, titles or headings. Moves the real "last updated" date. | All with location/category pages | One full pass every 3 to 4 months | ready |
| 8 | content-opportunities | Finds the few articles worth writing (listicles, guides, comparisons) with free tools, proves each with evidence, filters junk, off-topic and duplicates, writes with the site's own data, checks every number and link (article_check.py), asks yes/no for approval, then publishes on its own. | All | Weekly (skips weak weeks) | ready |
| 9 | tool-page-finder | Finds the boring calculator and tool pages a site should build next (fee calculators, cost estimators, checkers) from Google Autocomplete plus web search; a keyword export (Ahrefs, Semrush, Search Console) is optional and switches on real volume. Scripts do all filtering and scoring; out comes a ranked shortlist with build briefs. | Traffic, affiliate, ads | Every few months | ready |
| 10 | broken-links-and-seo-errors | Free crawl of the site's own pages + Wayback Machine: broken links, old URLs that now 404 (redirect them), pages fighting for the same keyword, stale years, duplicate titles, thin pages, sitemap gaps. Adapts to new / growing / lost-rankings sites. Hands off a ready-to-paste fix prompt. | All | Monthly | ready |
| 11 | internal-links | Finds orphan pages, vague link text ("Florida"), and the exact sentences where links to money pages, hubs and new tools should go. Better with a Search Console export, works without. | All | Monthly, and after any new page or tool | ready |
| 12 | keep-pages-up-to-date | Keeps pages with changing facts current (fees, prices, discount days, policies) from official sources, each on its own schedule. Updates the same page, never a second one. | All with fee, price or policy pages; every calculator | Weekly to yearly, per page | ready |
| 13 | review-insights | Reads recent Google reviews per listing for facts owners care about (prices, wait times, policies) and adds them to the listing with the review date. | Directories where prices or details live in reviews | Monthly | planned |
| — | check-my-setup | Yes/no check that keys, database tables, photo bucket, scripts, mailbox and GitHub all work, with the exact fix for anything that doesn't. Lists scheduled jobs and their last run. Read only. | All. Run after install and after any key change. | On request | ready |
| — | review-changes | Shows every change waiting for approval in plain words (old → new, why, source); applies only what the owner approves ("approve 1, 3"). | All jobs that propose changes | On request | ready |
| — | directory-db | Shared helper, not a job: every skill reads and writes the database through it (allowed tables only, no deletes, one row per update, every change logged with old values). | Used by all jobs | n/a | ready |

**Advanced:** page-copy-refresh needs a one-time change on the website (copy stored in the database); keep-pages-up-to-date pays off once the site has fee, price or policy pages, or a calculator.

## Monetization to job map

Use this to recommend. Lead with the top 3 for the site's main money model.

- **Lead gen:** 6 lead-routing, 2 listing-check, 5 missing-info-outreach, 4 inbox-triage
- **Affiliate:** 8 content-opportunities, 7 page-copy-refresh, 9 tool-page-finder, 0 reddit-listing-research
- **Display ads / pure traffic:** 8 content-opportunities, 7 page-copy-refresh, 9 tool-page-finder, 11 internal-links, 10 broken-links-and-seo-errors, 12 keep-pages-up-to-date
- **Featured listings / claims:** 5 missing-info-outreach, 2 listing-check
- **Job board:** 8 content-opportunities, 4 inbox-triage, 2 listing-check (stale jobs)

## Global rules for every job

1. Never write to a database directly, except the specific tables a skill lists under "Allowed writes" and only when the site config allows it. Otherwise add the change to `notes/<site>/pending.md` in the format defined in the review-changes skill, and the owner approves it with review-changes.
2. Never send email unless the site config says `auto_send: true` for that job. Otherwise save drafts as files in `notes/<site>/drafts/` (lead-routing's `send_mail.py --draft` does this) for the owner to review.
3. Read the site's config in `sites/<site>.yaml` and notes in `notes/<site>.md` before every run.
4. Start every new job with a dry run of max 20 records and show results before scaling.
5. End every run with a short summary: what was checked, what was found, what needs approval.
6. After writing or changing anything in `sites/` or `notes/`, commit and push to GitHub (`git add sites notes && git commit -m "<site>: <what>" && git push`). Never commit anything in `skills/`. Never commit secrets.
7. **Settings first.** The first time a job runs on a site, it asks its few setup questions in ONE message (defaults shown, "defaults" is a valid answer), saves the answers in the site config and never asks again. Owners change a setting by just saying so. **Scheduled runs never stop to ask:** if a setting is missing during an unattended run, use the default, finish the run, and put the open questions at the top of the summary.
8. **All database reads and writes go through `directory-db/db.py`** with `--allowed-tables` set to the job's allowed tables. No skill writes its own API calls or SQL for site data, and nothing is ever deleted.
9. **Missing pieces are not a stop.** If `notes/<site>.md` doesn't exist, create it with a 3 line header (site name, URL, "Rules go here") and continue. If a job's config section is missing, run that job's Step 0 settings (never copy `sites/example.yaml` wholesale). Every file a job or script writes goes under `$DIROPS_REPO/notes/<site>/` (default `/data/workspace/directory-ops/notes/<site>/`), never `/tmp` or the current folder. The config key for the tables a job may write is always `allowed_tables`.
10. **The owner can click everything you show them.** Never send a server file path (`/data/...`). Articles, page mockups and reports the owner should look at get a clickable link: the site's own preview link when one exists, otherwise `content-opportunities/preview_link.py <file> --style-from <one of the site's own pages>` (shown in the site's real design, free, hidden from Google, deletes itself in 72 hours). Short things go straight into the chat.
