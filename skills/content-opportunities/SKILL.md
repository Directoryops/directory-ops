---
name: content-opportunities
description: Finds the few articles worth writing for a directory (listicles, guides, comparisons, calculators) using only free tools, proves each one with evidence, filters out junk and near duplicates, then drafts the chosen article with the site's own data. Use when the owner asks for article ideas, blog ideas, listicles, content to write, on its schedule, or when the owner answers yes or no to an article approval message.
---

# Content Opportunities

## Playbook card (show this to the owner)

Show this card to the owner before setting the helper up (onboarding plan or "add a helper"), so they see and approve the process.

**What it does:** finds the few articles worth writing for your directory, proves each one, then writes them one at a time in your voice.
**Why it works:** only write what people really search for AND where your own listing data gives you an edge nobody else has. Quality over volume: 2 strong articles beat 20 thin ones.
**How I work:**
1. I pull facts from your listings that nobody else has (counts, features, prices).
2. I collect real questions from Google suggestions, "People also ask" and forums.
3. I drop topics big sites own, your own pages already answer, or you can't answer honestly.
4. I score what's left and show you a ranked list with the evidence for each.
5. You pick; I write by hand, check every number and link, and show you the whole article.
**You approve:** the topic list and the first article (your quality bar), then each new article or only the first, your choice.
**Cadence:** up to once a week; it skips weeks with no strong topic.
**What you get:** a ranked top 10 topic list with evidence, then 1 strong article a week.
**What I need from you:** nothing to start (no blog yet? you paste drafts in).
**Make it yours:** "never write about competitors", "friendly, no fluff", "link every article to a city page".

**Onboarding sample:** a ranked top 10 topic list. For each topic: the evidence people search it, why we can win it, and which of your pages it links to. No draft until the owner picks.

**If a step fails** (blocked site, thin data, noisy results): try the fallback this skill documents, and still deliver the best honest sample. Never end with less than the onboarding sample without telling the owner, in plain words, what blocked it and the fix.

Goal: a short list of articles worth writing, each backed by evidence, then one excellent draft at a time. Recommending only 2 is a success; 20 weak ones is a failure. Free tools only (web search, Google autocomplete, forums, the site's own database, Search Console if connected). Full detail for every step: `REFERENCE.md` (same headings).

## Before every run

1. Read `sites/<slug>.yaml` (section `content`) and `notes/<slug>.md`. No notes file: create it with a 3 line header (site name, URL, "Content rules:"). No `content` section: run Step 0 (never copy `sites/example.yaml` wholesale).
2. Read `## Articles worth writing rules` and "Content rules" in `notes/<slug>.md` and follow them (this skill's safety rules still win).
3. Read `notes/<slug>/content/log.md`: articles written, rejected, queued, or `awaiting_approval`.
4. Files go under `$DIROPS_REPO/notes/<slug>/`, never `/tmp`.

## Hard rules

1. **Write every article yourself, section by section.** Never with a script, template or loop.
2. **No invented numbers, quotes, reviews or prices.** Every number comes from Step 1 facts or a public source you actually opened.
3. **Business facts only from the business's own site or Google profile.** Never other directories, listicles, review sites, competitors or `untrusted_domains`.
4. **Outbound links:** at most 4, trusted sources only. Never competitors, other directories, `never_link` domains, or anything unrelated.
5. **Never show internals to readers:** no table or column names, site codes or slugs, "queried", "rows", "records".
6. **Never publish while `article_check.py` fails.** Never more often than `publish_cadence`. Only one article `awaiting_approval` at a time.
7. **Never a second blog** next to an existing one, and never a second page on the same topic.
8. **Paid SEO APIs** (only if connected): after free steps cut the list to 15 or fewer, one batched call, max `api_budget.max_calls_per_run` (default 5), cache 30 days, report every paid call (REFERENCE.md § Optional power-ups).
9. **Honest stats only.** Every "X% of listings do Y" claim from text (walk-ins, payment, amenities) comes from `listing_stats.py --text <column> --yes '<regex>' --no '<regex>'`: a listing that doesn't mention it is UNKNOWN, never "no"; say "not stated" for companies whose listings are silent, and report "conditional" ("yes, but only if…") as its own group, quoting the script's example sentence. Every listing number goes through `listing_stats.py` (suspicious rows out, sub-brands rolled up under the parent). Stats from changing fields (hours, prices, rules) need listing-check in the last 60 days or your own 10-listing spot check; otherwise never headline them (REFERENCE.md § Honest stats).
10. **Rules and eligibility** (age, weight, requirements, how often) are quoted from each company's own page, exceptions included. Never from search snippets or listing summaries. **Look before you block or ask:** open the company's FAQ and eligibility pages (and the FAQ data built into the page) yourself. **The official page beats your listings:** use the official number and log the listing value as a data issue for listing-check. Never ask the owner a fact you can look up; owner questions are only for what only the owner knows (their taste, their partners, their goals).
11. **Local searches** ("near me", "open now", "open Sunday", "closest") are page features, not articles (REFERENCE.md § Local searches).
12. Tell the owner plainly what you can't do: no exact search volumes without an SEO tool; you can't add pages to a site that has no blog you can reach (REFERENCE.md § What you can and can't do).

## Step 0: Settings (first run only)

If `content.settings_done` is not `true`: ask the 8 questions in REFERENCE.md § Step 0, one per message, default shown; the owner can say "use the defaults" anytime. **Quick mode (onboarding):** only the `[essential]` ones onboarding hasn't answered; list the defaults you used. Write every key explicitly (table in REFERENCE.md § Step 0: `goals`, `approval`, `notify`, `publish_cadence`, `max_articles_per_month`, `topics.core`/`topics.adjacent`, `never_link`, `voice_page`, `editor`), set `settings_done: true`, never ask again.

**Teach me your way:** one optional question right after this helper is accepted (wording and examples in REFERENCE.md § Teach me your way). Turn the owner's OWN answer into 3 to 7 rules, show them back, save under `## Articles worth writing rules` in `notes/<slug>.md`. **Learn from corrections:** when the owner rejects or edits something, ask once "Want me to remember that as a rule for next time? (yes/no)".

**Goals decide the order** of topics that pass, never the score: sort by the goal's column first (`leads` → money link, `traffic` → demand, `ai_citations` → data edge, `backlinks` → data edge + linkability). Table in REFERENCE.md § Goals decide the ranking.

## Step 1: Learn the site (read only)

1. Count **only valid listings** (listing-check's types and active filter); host businesses (a gas station with a wash) counted separately and named as such.
2. Export the listings (`db.py select --all`) and run `listing_stats.py` (command in REFERENCE.md § Honest stats). Compute 10 to 20 **facts nobody else has** from its output → `notes/<slug>/content/facts.md` (date, query, its `say_in_article` line, freshness: listing-check date or your spot check "N of 10 matched").
3. Sitemap: list pages and **money pages**. No live site: only the config's URL pattern; never invent paths.
4. **No live site:** set `publish: drafts_only`, go to Step 2. Otherwise, if `publish` isn't set, **find where articles already live** (paths, CMS signs, an articles table), read 2 or 3 existing articles, **audit their outbound links once** (table for the owner; read the text around each link first; a button, a deliberate promo or a possible own/partner site is a QUESTION for the owner, never "remove"), and pick the publish method: `wordpress`, `supabase_articles`, upgrade a table another tool made, or `drafts_only`. Checklist and details: REFERENCE.md § Step 1.

## Step 2: Candidate topics (20 to 40)

- **Owner's own topic list first:** queue as `queued (owner)`; they skip Steps 2 to 4 but not Step 6 or the checker.
- **Facts that change** (fees, hours, prices, discount days) → one living page added to `notes/<slug>/keep-pages-up-to-date.yaml`, never a second article. **Searchers who want to calculate** → propose a tool (tool-page-finder) instead.
- Sources: autocomplete `https://suggestqueries.google.com/complete/search?client=firefox&q=<seed>`, forums/Reddit questions, People Also Ask, Step 1 facts, Search Console queries ranking 8 to 30 (strongest).
- Local sites: put the area in the seeds; drop suggestions naming another place. One topic = one search intent.
- **Local or "right now" searches** (near me, open now/today/Sunday/24 hours, closest) → the "Better as a page feature" list with a hand-off prompt, never an article. Seed list: REFERENCE.md § Step 2.

## Step 3: Evidence (max 8 web searches)

Rank all candidates free first (autocomplete variants, data edge), then search only the **top 5** (3 spare searches). Record demand signals (need 2+), who ranks (beatable vs hard) and the gap. Say which candidates weren't searched. Lists: REFERENCE.md § Step 3.

## Step 4: Score and filter

Score 0 to 3 each: Demand, Beatable, Data edge, Money link (total of 12). **Drop a topic if any gate fails:** data edge below 2 · duplicate intent · template spam (local pages only for top areas, max `max_local_per_month`, area needs `min_listings_for_local`, default 15) · "Top N" without N+3 qualifying listings · can't be honest · no reader benefit · off topic · the site's own pages already answer it · no proven demand. Full gate wording: REFERENCE.md § Step 4. **Thin data** (key columns mostly empty): stop, tell the owner which fields are empty, suggest reddit-listing-research or listing-check first. Keep at most `max_articles_per_month`; queue only topics scoring at least `min_score` (default 9).

## Step 5: Report and let them pick

Save `notes/<slug>/content/opportunities-YYYY-MM-DD.md`. Show one table: idea · kind · proof people search it · who shows up now · what we know that they don't · page it sends readers to · score. Then **"Better as a page feature"** (local searches, one line each + the hand-off prompt). Dropped ideas: one plain line each. **Overlap check (required line per topic):** list ALL existing articles first (count them), then for each survivor open any existing article whose title shares its core idea (e.g. eligibility, disqualify, requirements) and add the table column "Overlaps": `none` or `<existing slug>: expand it instead / different because …`. A topic that overlaps an existing article becomes "update that article", not a new one. Any stat in the report that isn't freshness-checked says "from our listings, not yet re-checked". Queue survivors in the log. Before the quality bar is approved, ask "Which one should I draft first?"; after, don't ask.

**Owner report cap:** about 600 words, at most 2 decisions (usually just "which first?"), each with a recommended answer. Data problems you found go in one line pointing to listing-check, not a list. **Before sending, re-read once:** one freshness date stated the same way everywhere, settings that don't contradict each other (e.g. never "auto-publish" next to "drafts only"), every fact relevant to its topic. Defaults go in one line ("Defaults I used: …"). No gate numbers or internal words.

## Step 6: Write the draft

Before writing: read `voice_page` and the best existing article (no voice: plain, friendly, 8th grade); write one line on who is searching and what they need to decide. Then:
- **Structure:** title with the main phrase · quick answer in the first paragraph (bold key sentence) · optional key facts blockquote naming the brand · body by type (guide / listicle with "How we picked" / comparison) · FAQ 3 to 6 real questions · next step to a money page · one italic sources line at the end.
- **Every H2 is a real searcher question or phrase,** never about our data or method. **Turn every fact into advice.**
- At least 2 facts from our data; 3 to 6 working internal links incl. a money page; brand 2 to 4 times (exact capitalization); **at most one** "check before you go" sentence; numbers agree everywhere; facts older than 3 months written "as listed on <brand>".
- Name companies only in local or "best companies in <area>" articles. Tables over charts. Images: max 1 listing photo with credit; AI images only if `ai_images: true`.
- Compare with the top 3 ranking pages; improve until ours is better.
Save to `notes/<slug>/content/drafts/<url-slug>.md` with: target phrase, intent, suggested URL, meta title (≤60), meta description (≤155), internal links used. All writing, SEO and layout rules: REFERENCE.md § Step 6.

## Step 7: Badge (listicles only)

Copy-paste badge snippet per company, true and specific text; propose the design first; never email companies unless the owner allows it. Snippet: REFERENCE.md § Step 7.

## Step 8: Check, approve, publish

1. Create the draft: WordPress post `status: draft`, or a row in `articles` with `status: draft` (fields in REFERENCE.md § Step 8). Internal links are relative paths and must load.
2. **Run the checker until it passes:**
   ```
   python3 /data/skills/directory-ops/content-opportunities/article_check.py article.json --site https://<domain>
   ```
   (`--no-http` only for a site with no live pages yet, then list every internal link for the owner.) Then the quality gate (REFERENCE.md § Step 8), including valid-listing counts checked against facts.md yourself.
3. **Approval** when `approval: every_article`, or `first_article_only` with no approved article yet. `drafts_only` (or no blog connected): save the article as `.md` (and any page mockup as `.html`), make a **clickable preview link in the site's own design**: `python3 /data/skills/directory-ops/content-opportunities/preview_link.py <file.md> --title "<title>" --style-from <URL of one of the site's own article or guide pages>` (it builds the preview inside that real page: the site's header, menu, fonts, sidebar and footer; no blog yet → use any page with paragraphs). Don't build your own HTML mockup, then send the link (its `say` line), the article's title and 3-line summary, and "Publish-ready? Reply yes or no." If the link fails, paste the WHOLE article in chat instead. **Never send the owner a server file path (/data/...): they can't open it.** Never use paste sites or other hosts (they show raw code); only `preview_link.py`. In a page mockup, every link points to the site's real page (`https://<domain>/...`), never `#`. With a blog, send exactly:
   ```
   I wrote a new article: <title>
   Read it: https://<domain><blog_path>/preview/<slug>?token=<preview_token>
   Publish it? Reply yes or no.
   ```
   Log `awaiting_approval`. **yes** = publish (first yes = "quality bar approved" in the log). **no** = ask once "What should change?", save the rule, rewrite. Reply handling: REFERENCE.md § Step 8.
4. **Publish:** `status: published` + `published_at`; call `revalidate_url` with the secret from `revalidate_secret_env` if set; open the live URL and confirm. `drafts_only`: you never publish; send the owner the "Publishing a draft by hand" steps (REFERENCE.md), then check their live link.

## Step 9: Log it

Append to `notes/<slug>/content/log.md`: date, topic, target phrase, status (proposed, drafted, awaiting_approval, published, rejected), reason if rejected. Commit and push `notes/` (CATALOG.md rule 6).

## Summary (every run)

Plain words, max 6 lines, starting with what the owner needs to do: waiting on you · ideas found / kept / top reasons the rest didn't · recommended order.

## Schedule (after the quality bar is approved)

ONE job per site at `publish_cadence`; confirm its ID. Each run: (0) an article `awaiting_approval` → remind once, stop. (1) A `queued` topic → Steps 6 to 9 for the top one. (2) Queue empty and last research older than `min_days_between_research` (default 30) → Steps 1 to 5, then publish the top topic if it qualifies. (3) Otherwise "No topic good enough this week, skipping." `max_articles_per_month` is a ceiling, never a target. Quality gate fails → keep as draft, tell the owner, no second topic that run. Owner can pause anytime. Details: REFERENCE.md § Schedule.

Optional developer setup that removes copy-paste (blog section + revalidate route prompt, settings to save): REFERENCE.md § Setting up publishing.
