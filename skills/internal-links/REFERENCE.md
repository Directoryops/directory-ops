# Internal links: reference

Details the main SKILL.md points to by section. Every rule here still applies.

## R1. Settings questions (Step 0, first run only)

Ask one question per message, each with its default shown (the owner can reply "use the defaults for the rest" at any point). Save to `internal_links` in `sites/<slug>.yaml`, then set `settings_done: true`. In quick mode (onboarding), ask only the `[essential]` ones onboarding hasn't answered and list the defaults you used.

```
1. Which pages should rank the most? Your money pages, a new tool, a main hub. (default: I'll pick from your menu) [essential]
2. For each, what do people type into Google to find it? (default: I'll take it from the page title)
3. Is Google Search Console connected? A download from it makes my picks much better (guide: /data/skills/directory-ops/setup-guides/guides/search-console-export.md). (default: no) [skip in quick mode]
4. Can I add links inside your articles and page text myself, or only suggest them for you? (default: suggest)
```

Save the answers as `targets` (page → phrases + preferred anchor text).

## R2. Teach me your way (one optional question, right after this helper is accepted)

> Tell me which pages you most want to rank, and any places links must never go. Ramble or send a voice note; it makes me much better. (Or say "skip".)
> For example:
> - Car wash: "Push the membership guide hardest."
> - Roofing: "Never put links inside customer reviews."
> - Plasma center: "Link every city page to the pay-rates page."

Turn the owner's own answer (never invent rules when they said skip) into 3 to 7 short numbered rules in plain words. Show them back ("Got it, I'll: 1) … 2) … Anything to change?"; in quick mode end with "Say 'change …' anytime." instead of a question). Save under `## Better links between pages rules` in `notes/<slug>.md` (create the section if missing). Every run reads that section first and follows it. This skill's safety rules still win: a rule can't skip approval, delete things, or use competitors as sources.

**Learn from corrections:** when the owner rejects or edits a proposal, or says "no, because …", ask once: "Want me to remember that as a rule for next time? (yes/no)". Yes: add it to the rules section in plain words with today's date.

## R3. Why Search Console helps (tell the owner once)

Without it, the report judges pages by how many links they get. With it, it also knows which pages Google already likes (clicks: the best pages to link FROM) and which are almost there (position 8 to 20 with impressions: they gain the most from new links). It's free; the free method still works without it.

Say it plainly, e.g. "If you connect Google Search Console (free), I can see which of your pages Google already likes and which are almost on page 1, so I put links where they help most. Without it I still find good spots."

## R4. Blocked by the site's security

If the crawl output has `blocked_by_security` (the site's security answered, not the pages): the crawl only has the pages that got through. Never call it a rate limit.
1. Check a small sample now with your built-in web reader (homepage, sitemap, the target pages and about 10 pages likely to mention them). Suggest links only from that sample, labeled "sample".
2. Ask once (one yes/no): "Your site's security blocks simple scanners. I checked a sample with my web reader, but checking every page that way is slow and uses extra AI credits. Letting me in takes 2 minutes. Want to do that now?" Yes: send `setup-guides/guides/let-hermes-past-security.md`, then rerun the crawl. No: keep using samples; don't ask again (note it in the site's notes).
3. Scheduled runs never ask: they run the sample and add one line to the summary.
4. If the web reader is blocked too: say so in one line, make no suggestions, and don't list URLs from search engine snippets or indexes (they aren't a live check and are noise to the owner).

## R5. Reading what already exists (Step 2.0 detail)

Google counts every link: in the text, in the menu, header and footer, and in breadcrumbs. `inbound` gives each page's `content_links`, `sitewide_links` (menu/header/footer, or the same link on 80%+ of pages), `breadcrumb_links` and `total_links`. `page_types` shows, per kind of page, the share that already has a breadcrumb trail (`has_breadcrumb`), links up to its parent (`links_to_parent`) and links to the top hub (`links_to_hub`); "n/a" means that parent or hub page doesn't exist.
- Never call a page "weak" when `in_menu_on_most_pages` is true or `total_links` is high. Say what it has ("in the menu on every page, plus 12 links in page text") and suggest only a few in-text links from closely related pages.
- Never propose breadcrumbs, an "up to the state/hub" link or a "browse all" link for a page type whose share is 0.5 or more. Before proposing one, open 2 pages of that type and look; if it's there, drop it.
- `target_coverage` shows, for each money page, how many pages of each type link to it at all. A big type at 0 (for example "state pages: 0 of 46 link to the pay guide") is a template opportunity: one change, many links.
- `weak_pages` (at most 1 link of any kind) only count on a full crawl (`summary.partial_crawl` false). Ignore legal and contact pages. For each one that should rank, find 2 related pages to link from. A page that fits nowhere and gets no traffic may not belong; list it for broken-links-and-seo-errors, never delete it.

## R6. Broken links: the three kinds

- `kind: broken_route`: pages the site itself expects (in its sitemap, or the same kind of page works for other names). A site bug, not a bad link. These are often pages with real listings that earn nothing today. Hand off ONE fix: "make these page addresses load; keep the links".
- `kind: missing_page`: the page doesn't exist, but the same kind of page does for other places. Ask the owner: build it (worth it for places people search) or point the link elsewhere?
- `kind: bad_link`: point it at the right page or remove it.
- `menu_broken`: broken links in the menu or footer, on many pages at once (the biggest single fix). Ask its `ask_owner` question (build the page or remove the link). Never just say "remove".

**Proving a pattern.** `pattern` compares the real names (each page's link text, e.g. "Wilkes-Barre"), not the URL (where a space and a hyphen both look like "-"). Quote it as written: "every city page whose name has a hyphen gives an error (3: …); 753 pages of this type load and none of them has a hyphen in the name". Never turn "N load fine" into "N with a hyphen work". `sitemap_check.also_failing` lists sitemap pages of the same type that fail but no crawled page linked to; look up their real names in the listings table to confirm they share the pattern. If `sitemap_check.complete` is false, say "at least" and never claim which other pages work.

## R7. Choosing suggestions (Step 2 detail)

- Suggestions come strongest donor first (`score` = links the donor gets, plus Search Console clicks if given, times `topic_match`, how close its topic is to the target). Contact, about, legal, login, search and "how this was made" pages are never donors; one marked `weak_donor` is only there because nothing else mentions the topic, so say so.
- Only real body text the site owns. Never put links inside reviews, quotes, comments, listing details (addresses, hours, pay rows) or other people's words.
- Would a visitor want to click there? If not, skip.
- Natural anchor that names the topic, in the owner's phrasing; not "click here", not the same exact anchor every time.
- At most 1 new link per target per page, and at most 3 new links per page per run.
- `vague_anchors`: pages mostly linked with text that only names a place or says "click here". The fix is usually one template change. Name the block by its real heading from `in_blocks` (e.g. "the 'Explore Other States' list"); never invent a block name like "nearby states". If `in_blocks` says there's no heading, describe where it sits ("the list of state links under the city list") after opening one page.
- Structure ideas (only where `page_types` shows they're missing): breadcrumbs up to the hub, a "nearby" block, a link from each article to the matching location page and hub, a link from the homepage and hub to any new tool or money page.

## R8. Applying or handing off (Step 3 detail)

- Never edit fields page-copy-refresh owns (the copy table and fields in `page_copy_refresh`): its next refresh would wipe the links. Hand off a template change instead (a link block next to the copy).
- Links inside other database text (articles) with `can_edit_db: true`: add them, log page, sentence, anchor and target in `notes/<slug>/links/changes.md` so they can be undone. Check each changed page loads and the link works.
- Links in templates or code: give the owner ONE prompt to paste into Claude Code (or send to their developer) in the website's project. First time? Walk them through `/data/skills/directory-ops/setup-guides/guides/paste-into-claude-code.md`.

```
Improve internal links on a branch; give me the preview link and don't merge until I approve:
0. These pages give an error but should load: <examples>. Pattern: <e.g. every city whose name has a hyphen>. Fix how the page addresses are built and matched so they load; keep the links.
1. In <template/component, named by its heading e.g. "Explore Other States">, change link text from "<State>" to "<Topic> in <State>". Don't change URLs.
2. Add breadcrumbs "Home › <Hub name> › <Page>" to <page type>, linking <Hub name> to <hub URL>, with BreadcrumbList schema.
3. Add a "<Topic> in nearby <areas>" block to <page type> linking up to 6 neighbors and the hub.
4. Add a link to <money page> on every <page type> (e.g. one line under the pay table): "<sentence with anchor>".
Keep every existing URL, title and heading as is.
```

For a site that lost rankings (top-level `stage: lost_rankings`), hand off one group at a time and wait 3 to 4 weeks between groups.
