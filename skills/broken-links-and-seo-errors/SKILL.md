---
name: broken-links-and-seo-errors
description: Finds and fixes broken links, dead old URLs (redirects) and SEO errors on a directory website, for free. Crawls the site's own pages (no paid tools), finds broken links, old URLs that now 404, pages fighting for the same keyword, stale years in titles, duplicate or missing titles, thin pages and sitemap problems, then hands the owner a short fix list and a ready-to-paste fix prompt. Use when the owner asks for a site audit, checkup, broken links, "why did my rankings drop", or on its monthly schedule.
---

# Broken links and SEO errors

## Playbook card (show this to the owner)

Show this card to the owner before setting the helper up (onboarding plan or "add a helper"), so they see and approve the process.

**What it does:** checks every page of your site for the quiet problems that cost rankings, and gives you a short fix list.
**Why it works:** broken links, dead old addresses and two pages fighting for the same search waste the strength your site already earned. Fixing them is low risk and often the fastest win.
**How I work:**
1. I read every page your site lists, plus old addresses that used to work.
2. I find broken links, dead pages worth forwarding, duplicate titles and two pages competing for one search.
3. I check each finding by hand and drop false alarms.
4. You get the fixes in order of impact, with a risk label for each.
5. Changes to your site's code come as one ready-to-paste instruction for Claude Code or your developer.
**You approve:** every fix. For a site that lost rankings, one small group at a time.
**Cadence:** monthly. Sites don't break much faster than that.
**What you get:** a ranked fix list with counts, plus the exact fixes.
**What I need from you:** nothing to start. A Search Console export sharpens it.
**Make it yours:** "don't touch the homepage title", "forward old pages to the state page", "skip the blog".

**Onboarding sample:** the top issues list with counts and a risk label for each.

**If a step fails** (blocked site, thin data, noisy results): try the fallback this skill documents, and still deliver the best honest sample. Never end with less than the onboarding sample without telling the owner, in plain words, what blocked it and the fix.


Goal: find what quietly costs a directory rankings, in plain words, with the fix for each. Free: it reads the site's own sitemap and pages and the Wayback Machine. No Ahrefs, no Semrush, no API keys.

Read `sites/<slug>.yaml` (section `broken_links_and_seo_errors`) and `notes/<slug>.md` first. The scripts live in this skill's folder.

## Step 0: Settings (first run only)

If `broken_links_and_seo_errors.settings_done` is not `true`, ask one question per message, each with its default shown (the owner can reply "use the defaults for the rest" at any point), then save and set `settings_done: true`. Skip any question the config already answers (the site's `stage` is usually saved by onboarding; Search Console in `search_console.connected`).

**In quick mode (during onboarding), ask only the questions marked `[essential]` that onboarding hasn't already answered, and use the defaults (or what onboarding inferred) for the rest. List the defaults you used in the plan message; the owner changes any of them by saying so.**

```
Questions, one per message (say "use the defaults" anytime to skip the rest):
1. Is your site new (under 6 months), growing, or did it lose rankings recently? (default: growing) [skip if `stage` is set]
2. Which 1 to 3 pages make you the most money or traffic? (default: I'll pick from your menu and homepage)
3. Is Google Search Console connected to this site? If yes, I can use a download from it for better answers (guide: `/data/skills/directory-ops/setup-guides/guides/search-console-export.md`). (default: no) [skip in quick mode]
4. How often should I run this? (default: monthly)
5. Can I fix things myself where your site's text and links are stored, or only suggest fixes for you? (default: suggest)
```

Map to config: top-level `stage`, `money_pages`, `search_console.connected`, `cadence`, `can_edit_db` (default false).

What the stage changes:
- **New:** focus on broken links, sitemap and missing basics. Don't suggest merging or retitling pages yet; they need time to rank.
- **Growing:** everything, normal pace.
- **Lost rankings:** small, reversible changes, ONE group at a time, and say which Search Console numbers to watch for 3 to 4 weeks before the next change. Never delete pages in the first month. Redirects and broken links first (zero risk), then keyword fights.

### Teach me your way (one optional question, right after this helper is accepted)

This is what makes the helper yours instead of generic. Ask once (in quick mode it replaces settings questions, it doesn't add many):

> Tell me which pages matter most to you, anything I should never change (addresses or titles you picked on purpose), and how careful I should be. Ramble or send a voice note; it makes me much better. (Or say "skip".)
> For example:
> - Plasma center: "Never touch the city page titles, they rank well."
> - Wedding venue: "Old venue pages should forward to their city page, not the homepage."
> - Roofing: "Go slow, one change a month; we just recovered from a drop."

Turn the answer into 3 to 7 short numbered rules in plain words, show them back ("Got it, I'll: 1) … 2) … Anything to change?"; in quick mode end with "Say 'change …' anytime." instead of a question, so onboarding stays short), and save them in `notes/<slug>.md` under `## SEO fixes rules` (create the section if it's missing). **Every run reads that section first and follows it; this skill's own safety rules still win** (a rule can't make it skip approval, delete things, or use competitors as sources).

**Learn from corrections:** when the owner rejects or edits one of your proposals, or says "no, because …", ask once: "Want me to remember that as a rule for next time? (yes/no)". Yes: add it to `## SEO fixes rules` in plain words with today's date.

## Step 1: Crawl (about 1 minute for a few hundred pages)

Both scripts are in this skill's folder (installed: `/data/skills/directory-ops/broken-links-and-seo-errors/`):

```
python3 /data/skills/directory-ops/broken-links-and-seo-errors/site_crawl.py crawl https://<domain> --out $DIROPS_REPO/notes/<slug>/tmp/crawl.json
python3 /data/skills/directory-ops/broken-links-and-seo-errors/site_crawl.py old-urls https://<domain> --out $DIROPS_REPO/notes/<slug>/tmp/old.json
python3 /data/skills/directory-ops/broken-links-and-seo-errors/checkup.py $DIROPS_REPO/notes/<slug>/tmp/crawl.json --old $DIROPS_REPO/notes/<slug>/tmp/old.json --brand "<brand name>" > $DIROPS_REPO/notes/<slug>/tmp/checkup.json
```

If `limit_reached` is true, run again with `--max 2000`. If the Wayback check says it did not answer, skip it this run and say so.

**If the output has `blocked_by_security`** (the site's security answered, not the pages): those pages are blocked, not broken; never report them as broken links and never call it a rate limit. Then:
1. Check a small sample now with your built-in web reader (homepage, sitemap, the 10 most important pages and their links) and report only what that sample shows, labeled "sample".
2. Ask once (one yes/no): "Your site's security blocks simple scanners. I checked a sample with my web reader, but checking every page that way is slow and uses extra AI credits. Letting me in takes 2 minutes. Want to do that now?" Yes: send `setup-guides/guides/let-hermes-past-security.md`, then rerun the crawl. No: keep using samples; don't ask again (note it in the site's notes).
3. Scheduled runs never ask: they run the sample and add one line to the summary.

## Step 2: Judge each finding (don't just paste the script output)

Go through `checkup.json` in this order. For each finding decide: real problem, or fine?

1. **broken_links:** always real. Fix = point the link at the right live page, or build the missing page if it should exist (e.g. a location page the data supports), or redirect the dead URL.
2. **dead_old_urls:** URLs that used to work. They may still have backlinks from other sites, so each one gets a permanent (301) redirect to the closest live page. Check the suggested target makes sense for a visitor; if not, pick the nearest topic page or the main hub. Same page with different capitals = redirect to the lowercase one.
3. **keyword_fights:** two pages with nearly the same title or H1. Real when both aim at the same search ("Find X near you" on the homepage AND on the hub). Decide which page should own that search (usually the one with the most specific topic and the best links), and change the OTHER page's H1 or title to its own focus. Never change both at once.
4. **Same topic spread over many weak pages:** the script can't see this one; you can. Read the list of page titles and group pages that explain the same thing ("how X works", "is X worth it", "X guide"). Several weak pages on one topic should become one strong page: keep the one with the best URL or menu link, fold the best parts of the others into it, 301 the rest to it.
5. **stale_years:** a past year in a title makes the page look abandoned. Drop the year or update it only if the page content is really current.
6. **title_problems, h1_problems, meta_problems:** missing or duplicate are real. Long titles are low priority; mention them last.
7. **thin_pages:** real only if the page is meant to rank. Contact, privacy, login pages are fine thin.
8. **sitemap_problems:** noindex or broken pages in the sitemap are real; a live page missing from the sitemap is real if it should rank.

Never touch anything in the owner's `never_touch` list.

## Step 3: Report

Save `notes/<slug>/checkup/YYYY-MM-DD.md` and show the owner a short list, most important first:

| # | Problem (plain words) | Pages | Fix | Risk |
|---|---|---|---|---|

Risk is `none` (redirects, broken links), `low` (titles, H1s, merges with redirects) or `test` (anything touching the homepage or the top money pages: change, then watch Search Console for 3 to 4 weeks).

Write every row for a non-technical owner: "3 links in your menu go to pages that don't exist", not "404 on /x". Say "page title" and "main headline" instead of title tag and H1, "old address forwarding" instead of 301 redirect, and "the list of pages you give Google" instead of sitemap (first mention). Show the risk as "safe", "low risk" or "test and watch".

## Step 4: Fix

- **Stored in the database** (page text, titles, links inside content) and `broken_links_and_seo_errors.can_edit_db: true`: make the change, log old and new value in `notes/<slug>/checkup/changes.md` so it can be undone.
- **Stored in the website's code** (redirects, page templates, menus): you can't edit code. Give the owner ONE prompt to paste into Claude Code (or send to their developer) in the website's project, with every change listed exactly: First time? Walk them through `/data/skills/directory-ops/setup-guides/guides/paste-into-claude-code.md`.

```
Make these SEO fixes on a branch, then give me the preview link and don't merge until I approve:
1. Add permanent (301) redirects: <old> → <new> (one per line). Verify each target returns 200.
2. Fix internal links: on <page>, the link "<anchor>" points to <dead URL>; point it to <live URL>.
3. Change the H1 on <page> from "<old>" to "<new>". Don't change the URL or title.
<...>
Careful with capital-letter redirects: many frameworks match redirect rules without caring about capitals, so a rule for /Page → /page can send /page to itself forever. Only redirect when the path really has a capital letter.
After deploy, check every old URL redirects to a page that loads, AND load every page of the same type (e.g. all location pages) to make sure none of them now redirect in a loop.
```

For a site that lost rankings, put only the zero-risk group in the first prompt. The next group goes in after the checkpoint.

## Step 5: Re-check

On the next run, confirm last run's fixes are live (redirects answer 301 to a 200 page, broken links gone). Report anything that didn't stick.

## Summary

Plain words, max 6 lines, starting with what the owner needs to do:
- Waiting on you: the fix list to paste into Claude Code (or send to your developer), or decisions only you can make
- Found: the top problems in one line each ("3 menu links go to missing pages")
- Fixed since last time / didn't stick
- What to watch in Google Search Console over the next weeks (if connected)
