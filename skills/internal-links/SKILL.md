---
name: internal-links
description: Finds the internal links a directory website is missing and where exactly to add them. Crawls the site for free, finds broken pages the site should have, orphan pages, links whose text doesn't say what the page is about ("Florida" instead of "car washes in Florida"), and pages that should pass strength to the money pages, then proposes each link with the exact sentence and anchor text. Uses Google Search Console if connected. Use when the owner asks about internal links, wants a new page to rank, launched a tool or hub page, or on its monthly schedule.
---

# Internal links

## Playbook card (show this to the owner before setting the helper up)

**What it does:** finds where links to your most important pages naturally fit, so their strength flows where it earns you money.
**Why it works:** internal links are the one ranking lever you fully control, and they're free. Link text that says what the page is about ("car washes in Austin", not "Austin") tells Google what to rank it for.
**How I work:**
1. I map every link on your site, menus and breadcrumbs included, because Google counts them all.
2. I find broken links that point at pages your site should have, pages with almost no links of any kind, and link text that says nothing.
3. For each important page, I find sentences on your strongest, most related pages that already mention its topic (never your contact or about page).
4. I suggest the exact sentence and link text, skipping reviews, quotes and buttons.
5. Template-wide fixes (menus, breadcrumbs) come as one instruction for your developer or Claude Code.
**You approve:** every new link.
**Cadence:** monthly, and whenever you add an important page or tool.
**What you get:** the top 10 link opportunities with the exact sentence for each, plus template fixes.
**What I need from you:** nothing to start. A Search Console export makes the picks much better.
**Make it yours:** "push the quote page hardest", "max 2 new links per page", "never link from the blog to competitors".

**Onboarding sample:** the top 10 link opportunities (exact sentence + link text), plus template fixes.
**If a step fails** (blocked site, thin data): use the fallback below and still deliver the best honest sample; never end with less without telling the owner, in plain words, what blocked it and the fix.

## Before you start

Read `sites/<slug>.yaml` (section `internal_links`) and `notes/<slug>.md` (follow `## Better links between pages rules`). First run: settings questions (REFERENCE.md R1), then "Teach me your way" (R2). Mention Search Console once (R3).

## Step 1: Crawl and report

Write `targets.json` from the config: `{"/page": {"phrases": ["what people search"], "anchor": "preferred link text"}}` (add pages at Search Console position 8 to 20).

```
python3 /data/skills/directory-ops/broken-links-and-seo-errors/site_crawl.py crawl https://<domain> --out $DIROPS_REPO/notes/<slug>/tmp/crawl.json [--max 400 --spread]
python3 /data/skills/directory-ops/internal-links/link_report.py $DIROPS_REPO/notes/<slug>/tmp/crawl.json --targets $DIROPS_REPO/notes/<slug>/tmp/targets.json --check-sitemap 1500 [--gsc $DIROPS_REPO/notes/<slug>/tmp/gsc-pages.csv] > $DIROPS_REPO/notes/<slug>/tmp/links.json
```

- Big sites (over about 1,500 pages) or the onboarding sample: `--max 400 --spread` samples every page type. On a partial crawl say "sample" and never call a page weak.
- **Fewer than 10 strong opportunities** (`summary.need_more_crawl: true`): crawl again with double `--max` (up to 2,000 pages) before reporting. Only then report fewer, and say how many pages were checked.
- `blocked_by_security` in the output: follow REFERENCE.md R4 (web reader sample, one yes/no, never "rate limit").

## Step 2: Decide (read REFERENCE.md R5 to R7 before writing anything)

Hard rules:
1. **Check before you claim.** Every "X has no / only N links" sentence must match `inbound` (text + menu + breadcrumb links). Never propose breadcrumbs, a hub link or "browse all" for a page type where `page_types` shows 0.5 or more already have it.
2. **Broken pages first.** `broken_route` = a site bug, fix the route, keep the links. Quote the `pattern` exactly as written (it compares real names, not URLs). Use `sitemap_check` for the full list; if it isn't `complete`, say "at least" and never claim which others work (R6).
3. **Money pages by page type.** Read `target_coverage`: any big page type with 0 pages linking to a money page is a template fix (state, city, company and listing pages all count).
4. **Name blocks by their real heading** (`in_blocks`). Never invent one ("nearby states").
5. **Good spots only:** real body text from strong, related pages; never reviews, quotes, comments, listing details, or contact/about/legal pages; max 1 new link per target per page, 3 per page per run (R7).

## Step 3: Apply or hand off (REFERENCE.md R8)

Never edit page-copy-refresh fields. Database article links only with `can_edit_db: true`, logged in `notes/<slug>/links/changes.md`. Template changes: ONE paste-ready prompt (R8). Sites with `stage: lost_rankings`: one group at a time, 3 to 4 weeks apart.

## Step 4: Next run

Re-crawl. Confirm last run's links exist. Report how the target pages' link counts changed (and Search Console position if connected).

## Summary

Plain words, max 6 lines, starting with what the owner needs to do:
- Waiting on you: links to approve, build-or-remove answers for broken menu links, or a change to paste into Claude Code (or send to your developer)
- Broken pages your site should have (and the pattern), if any
- Links added: which page now links to which, one line each
- Money pages that whole page types never link to
- Words people search that no page uses yet (write them into a page or article first)
