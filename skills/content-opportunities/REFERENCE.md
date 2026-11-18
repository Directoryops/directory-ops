# Content Opportunities: reference

The full detail behind `SKILL.md`. SKILL.md is the lean core you follow every run; open the section it points to when you reach that step. Sections keep their original headings, so "REFERENCE.md § Step 6" means the `## Step 6` heading below. Nothing here overrides SKILL.md's hard rules.

Goal: a short list of articles that are worth writing, each backed by evidence, then one excellent draft at a time. Quality over volume. It is a success to recommend only 2 articles, and a failure to recommend 20 weak ones.

Works for any directory. Uses only free tools: web search, Google autocomplete, forums, the site's own database, and Google Search Console if connected. No paid SEO tools needed.

Read `sites/<slug>.yaml` (section `content`) and `notes/<slug>.md` first. If `notes/<slug>.md` doesn't exist, create it with a 3 line header (site name, URL, "Content rules:") and continue. If the config has no `content` section, run Step 0 (never copy `sites/example.yaml` wholesale). Files go under `$DIROPS_REPO/notes/<slug>/`, never `/tmp`. Check `notes/<slug>/content/log.md` for articles already written or rejected.

## Step 0: Settings (first run only, about 1 minute)

Every owner wants this to work a little differently. If `content.settings_done` is not `true`, ask one question per message, each with its default shown (the owner can reply "use the defaults for the rest" at any point). Skip any question the config already answers. Save the answers in the `content` section and set `settings_done: true`. Never ask again; the owner changes a setting by saying so ("publish every 2 weeks", "ask me before every article").

**In quick mode (during onboarding), ask only the questions marked `[essential]` that onboarding hasn't already answered, and use the defaults (or what onboarding inferred) for the rest. List the defaults you used in the plan message; the owner changes any of them by saying so.**

```
Questions, one per message (say "use the defaults" anytime to skip the rest):
1. What should articles do most? leads / traffic / AI answers citing you / backlinks (default: traffic)
2. Should I ask you before every article, or only before the first one? (default: only the first one; after that I publish on my own. Without a blog I can publish to, I hand you each finished draft to post yourself.)
3. Where should I ask for approvals? this chat / Telegram / email (default: this chat)
4. How often, at most? (default: 1 per week, skipped when no topic is strong enough)
5. Topics: only your niche, or nearby topics people choosing a <business type> care about too? Name any nearby ones. (default: niche only)
6. Any sites I must never link to (competitors, other directories)? (default: none besides directories like yours)
7. Which page on your site sounds most like you? I'll match its tone. (default: your homepage) [skip if the site isn't live]
8. What do you build your website with (WordPress, Webflow, Wix, Framer, custom code, not sure)? I'll give you exact steps to post drafts there. (default: not sure) [in quick mode ask this only when the first draft is ready]
```

Map them to config. Any question the owner doesn't answer takes the default in this table, written into the config explicitly (never left blank):

| Q | Config key | Default |
|---|---|---|
| 1 | `goals` | from onboarding's money answer (ads or affiliate → traffic, leads → leads), else `[traffic]` |
| 2 | `approval` (`first_article_only` / `every_article`) | `first_article_only` |
| 3 | `notify` (`webui` / `telegram` / `email`) | `webui` |
| 4 | `publish_cadence` + `max_articles_per_month` | `weekly` + `4` |
| 5 | `topics.core` + `topics.adjacent` | the listing type, no adjacent |
| 6 | `never_link` | `[]` (other directories in the niche are always excluded anyway) |
| 7 | `voice_page` | homepage; none if no live site |
| 8 | `editor` | `not sure` |

`publish_cadence` is the most often a job runs; `max_articles_per_month` caps the total. Example: weekly + 2 a month = runs weekly, but after 2 articles in a calendar month it skips until next month. `max_articles_per_month` is exactly what the owner said (4 only when they took the default).

### Teach me your way (one optional question, right after this helper is accepted)

This is what makes the helper yours instead of generic. Ask once (in quick mode it replaces settings questions, it doesn't add many):

> Tell me how you want articles to sound and what to write about: topics you love or hate, what people choosing a <business type> ask (or your readers, if the site is live), anything I should never say. Ramble or send a voice note; it makes me much better. (Or say "skip".)
> For example:
> - Plasma center: "Readers are mostly students. Mention first-visit bonuses, never give medical advice."
> - Roofing: "No scare tactics about storms. Plain, honest, short."
> - Car wash: "Casual tone, short paragraphs, end with one practical tip."

Turn the owner's OWN answer (never invent rules when they said skip) into 3 to 7 short numbered rules in plain words, show them back ("Got it, I'll: 1) … 2) … Anything to change?"; in quick mode end with "Say 'change …' anytime." instead of a question, so onboarding stays short), and save them in `notes/<slug>.md` under `## Articles worth writing rules` (create the section if it's missing). **Every run reads that section first and follows it; this skill's own safety rules still win** (a rule can't make it skip approval, delete things, or use competitors as sources).

**Learn from corrections:** when the owner rejects or edits one of your proposals, or says "no, because …", ask once: "Want me to remember that as a rule for next time? (yes/no)". Yes: add it to `## Articles worth writing rules` in plain words with today's date.

## Goals decide the ranking

Read `content.goals` from the config (in priority order). If missing, ask the owner once: "What do you want content to do most: bring leads, bring traffic, get cited by AI answers (ChatGPT, Google AI), or earn backlinks?" Scores stay a plain total out of 12 (Step 4). The goal only decides the ORDER of topics that pass: sort by the goal's column first, then by total.

| Goal | Sort first by | Favor these types |
|---|---|---|
| `leads` | Money link | Bottom of funnel: cost, best companies in an area, "for <use case>" guides, calculators |
| `traffic` | Demand | Broad questions with many autocomplete variants |
| `ai_citations` | Data edge | Question topics with a clear answer, quotable facts naming the brand, comparisons |
| `backlinks` | Data edge + "would other sites link here?" | Data studies ("X% of companies..."), listicles with badges, free tools |

## Optional power-ups (only if connected)

The free method always works. If the site has one of these, use it to sharpen Step 3 and Step 4. Never require them.

- **Google Search Console** (free, best signal): queries the site already shows for, with impressions and position. Use first when available.
- **DataForSEO** (`<SLUG>_DATAFORSEO_LOGIN` + `<SLUG>_DATAFORSEO_PASSWORD`, or shared `DATAFORSEO_*`): search volume, top results, competitor keywords.
- **Ahrefs** (`AHREFS_API_KEY`): search volume, difficulty, competitor top pages.

**Budget rules for paid APIs (strict):**
1. Never call a paid API until the free steps have cut the list to the final 15 or fewer topics.
2. Batch: send all keywords in ONE volume request, not one call per keyword.
3. At most `content.api_budget.max_calls_per_run` calls per run (default 5). Stop and report if you would need more.
4. Cache every result in `notes/<slug>/content/seo-cache/YYYY-MM.json` and reuse it for 30 days. Never pay twice for the same data.
5. No backlink exports, full site crawls or bulk competitor dumps unless the owner asks.
6. In the summary, say exactly which paid calls you made.

## What you can and can't do (tell the owner)

- You CAN research, score, and write drafts as markdown files.
- You CAN publish if the site already has a blog you can reach (WordPress) or an `articles` table with a blog section (Step 1.4 and Step 8). Otherwise drafts go to `notes/<slug>/content/drafts/` and the owner publishes them by hand ("Publishing a draft by hand" below; the developer setup at the end is optional).
- Without a power-up you CANNOT see exact search volumes. You use evidence signals instead and say so honestly.

Tell the owner in plain words, e.g. "I'll find articles people really search for and write them with facts from your listings. I can't see exact search numbers without an SEO tool, so I use other proof. If your site has no blog I can post to, I'll hand you each finished article with copy-paste steps."

## Step 1: Learn the site (5 minutes, read only)

1. Database: what the listings contain. **Count only valid listings:** use the listing-check settings (`listing_check.types` and its active filter, or `database.active_filter`) so closed, test and off-type rows don't inflate counts. A host business that only offers the service on the side (e.g. a gas station with a car wash) is counted separately or left out, and the article says which ("3 car washes plus 1 gas station with a wash"). Find fields that make interesting facts (features, sizes, accessibility, categories, service areas, ratings, counts per state or city).
2. Compute 10 to 20 **facts nobody else has**, e.g. "only 31% of listed car washes offer a touchless bay", "Texas has the most car washes (78)". Save them in `notes/<slug>/content/facts.md` with the date, the query used, and which rows were excluded and why. These are the raw material for every article.
3. Sitemap: list existing pages. Identify **money pages** (pages that bring leads, affiliate clicks or signups) from the config or by looking. **No live site yet:** use only the location URL pattern in the config (e.g. `url_pattern` / `money_pages`); if there is none, the article has no internal links yet and you tell the owner. Never invent paths.
4. **No live site yet** (the URL doesn't load or is a placeholder): skip the sitemap and blog discovery below, set `content.publish: drafts_only`, and go to Step 2.
   **Find where articles already live** (only if `content.publish` is not set yet). Never create a second blog next to an existing one. Check, in order:
   - Sitemap and homepage links for `/blog`, `/articles`, `/guides`, `/resources`, `/news`, `/learn`, `/posts`.
   - Signs of a CMS: `/wp-json/` responds (WordPress), Ghost (`/ghost/`), Webflow (`webflow` in the page source), Brilliant Directories, etc.
   - An existing articles or posts table in the database.
   - Existing articles: read 2 or 3 to learn the current style, length and URL pattern, and add them to the log so new topics don't duplicate them.

   - **Audit what's there (one time).** Read the outbound links in every existing article. Links to competitors, other directories, or unrelated sites (common in articles written by AI blog tools that join link swap networks) hand rankings to someone else. List them for the owner in one table (article, link, why). **Before calling a link off topic, read the text around it:** a styled button or call to action, a link the article clearly promotes on purpose, or a site that could be the owner's own or a partner's is listed as a QUESTION ("Is <domain> yours or a partner? If not, I'd remove it."), never a removal recommendation. Only clear competitor, directory or link-swap links get "recommend removing". If the owner says fix them, remove the link but keep the sentence readable. Also note which existing articles get traffic (Search Console or Ahrefs if connected) and which topics clearly don't fit the site: that tells you what works here.

   Then pick the publish method and tell the owner what you found in one line ("You already have a WordPress blog at /blog with 12 posts, I'll publish there"):
   - **WordPress:** `content.publish: wordpress`. Owner creates an Application Password (Users → Profile → Application Passwords) and adds it as `<SLUG>_WP_APP_PASSWORD`, plus `content.wp_user` in the config. Publish with the WordPress REST API (`/wp-json/wp/v2/posts`, status draft first).
   - **Supabase articles table:** `content.publish: supabase_articles` (Step 8).
   - **A table made by another tool** (an AI blog writer's webhook, a CMS export) with different columns or no draft status: don't build a second blog. Give the owner the one time upgrade prompt from "Setting up publishing" adapted to add the missing columns to the SAME table (status defaulting to published so old articles stay live, preview_token, body_md, faq), then use `supabase_articles`. Until it's done, approvals happen in chat with the full article text and inserting = live.
   - **Anything else, or no blog at all:** `content.publish: drafts_only` and explain the one time setup at the end of this skill.

## Honest stats (freshness, brand map, suspicious rows)

Every number an article or topic pitch takes from the listings goes through `listing_stats.py` first:
```
python3 /data/skills/directory-ops/content-opportunities/listing_stats.py rows.json --name <name col> --website <website col> --hours <hours col> [--phone <phone col>] [--day su]
```
`rows.json` = `directory-db/db.py select --all` output. It:
- **Leaves out suspicious rows** and says how many: "coming soon" listings, no hours, the same hours all 7 days (often a placeholder), a close at 12:00 AM. Never headline a stat built on rows it excluded. Copy its `say_in_article` line into facts.md.
- **Brand map:** groups listings by website domain. Two brand names on one domain (a parent company and its sub-brands) are ONE company for every per-company stat. Name the group by the parent ("Acme Health, including its Sunrise and Bayview centers"). If the parent can't be told from the domain, read the parent's own "our brands / locations" page.
- **Per company share** for one day (`--day su`), excluding suspicious rows.

**Freshness gate.** Stats from fields that change (hours, prices, fees, rules) need checked data:
- listing-check ran on those listings in the last 60 days (its log) → use the stat, say "as of <month year>".
- Otherwise check a sample yourself first: 10 listings across the biggest companies against each business's own page. Report "N of 10 matched". 8 or more match → use it, with the sample line in facts.md. Fewer → the stat is "from our listings, not yet re-checked": never in a title, quick answer or headline; suggest running listing-check first.

**Rules and eligibility claims** (age limits, weight limits, documents, how often, requirements): quote each company's OWN page (FAQ, eligibility page). Read the listing or company text to the end, including exceptions ("66 and older with a yearly doctor's letter" is not "max 65"). Search results and listing summaries are leads to check, never the source. Two sources disagree → the company's own page wins and you note the conflict for the owner.

## Local searches become page features, not articles

Searches with local or "right now" intent ("near me", "open now", "open today", "open Sunday", "open 24 hours", "closest", "<thing> in <city>") are answered by Google's map and by the site's own city and listing pages, not by an article. Put each such idea in a separate list, **"Better as a page feature"**, with: the searches it catches, the data it uses, the pages it goes on (all city/state/listing pages), and one ready hand-off prompt:
```
On a branch, add an "Open Sunday" filter and a short "Open on Sunday" section to every city and state page, built from each listing's stored hours. Show "Hours last checked <date>". Give me the preview link; don't merge until I approve. Keep every existing URL, title and heading.
```
A page feature never counts toward `max_articles_per_month`. It is still checked for data freshness (the feature shows the last-checked date).

## Step 2: Generate candidate topics

**Owner's list comes first.** If the owner gives researched topics or keywords (from their own SEO tool), save them to the queue in `notes/<slug>/content/log.md` as `queued (owner)`. They skip Steps 2 to 4 (the owner already proved demand) but still get Step 6 writing rules and the checker. Free research only fills gaps when the owner's list runs out.

**Living pages beat new pages.** Some topics depend on facts that change (discount days, senior discounts, fees, hours, prices). For those: look at what ranks, find where those pages get their data, go to that source of truth, write a better page, and add it to the keep-pages-up-to-date list (`notes/<slug>/keep-pages-up-to-date.yaml`) with its sources and a re-check interval. That job keeps it current; never write a second article on it. Never publish a second page on the same topic.

**Tools beat articles when the searcher wants to calculate something** (fees, costs, sizes, savings). If a calculator would answer the search better than an article, propose it to the owner as a tool (the tool-page-finder skill) instead of writing an article.

Build 20 to 40 raw candidates from:

- **Autocomplete (free):** `https://suggestqueries.google.com/complete/search?client=firefox&q=<seed>` for seeds made from the niche and its modifiers: cost, price, how many, how much, vs, best, near me, for <event or use case>, <feature from the data> (e.g. touchless, 24 hour), requirements, checklist, mistakes, scam.
- **Real questions:** web search the niche plus "reddit", "forum" (or the niche's own community site). Note questions people ask more than once.
- **People Also Ask / related searches** in search results.
- **The facts from Step 1:** each surprising fact is a candidate ("Which car washes in Texas are open 24 hours?").
- **Search Console (if connected):** queries the site already gets impressions for but ranks 8 to 30. These are the strongest candidates of all.

Group near identical phrasings into one topic. One topic = one search intent.

**Seed with the area name for local sites:** if the directory covers one city or region, put the area in the seeds ("car wash austin", "austin car wash"), not just the niche.

**Location filter:** drop autocomplete suggestions that name a different city, state or country than the site's area ("austin mn", "austintown", "uk") before grouping. Keep suggestions with no place, or with the site's own places.

## Step 3: Gather evidence for each topic

**Search budget: at most 8 web searches per run for this step.** First rank all candidates with what's free: autocomplete variants and your data edge (Step 1 facts). Then web search only the **top 5** candidates' main phrases and look at the top 10 results of each (the other 3 searches are for checking one ranking page or a People Also Ask question if needed). In the report, say which candidates were not searched.

For each searched candidate, record:

- **Demand signals (need 2 or more):** shows up in autocomplete; several autocomplete variants; People Also Ask present; forum threads asking it; Search Console impressions; competitors bothered to write it.
- **Who ranks:**
  - Beatable: forums, Reddit, Quora, thin AI sites (e.g. `*.pages.dev` with generic text), vendor sales pages, manufacturer blogs, outdated pages (old year), pages that don't actually answer the question.
  - Hard: big national media, government, Wikipedia, huge marketplaces with strong pages on exactly this topic.
- **What the ranking pages do:** listicle or guide? City specific? Do they show prices, data, photos, a method? What do they miss or get wrong? This is the gap we fill.

## Step 4: Score and filter (the junk filter)

Score each topic 0 to 3 on:

| Score | Meaning |
|---|---|
| Demand | evidence that people search it |
| Beatable | weak or mismatched pages rank today |
| Data edge | our own data or facts make it better than what ranks |
| Money link | the reader naturally wants to click to a money page next |

**Hard gates. A topic is dropped if ANY is true:**

1. **Data edge below 2.** No unique data, no article.
2. **Duplicate intent.** Same main question as an existing article or another candidate. Location variants count as duplicates unless the local data is meaningfully different (different counts, features or companies) and the area has at least `min_listings_for_local` listings.
3. **Template spam.** Never produce the same article for many cities or states. Local pages only for the top areas by listing count, at most `max_local_per_month` (default 2). Defaults when the config doesn't say: `min_listings_for_local` 15.
4. **Listicle without enough options.** "Top N" needs at least N + 3 qualifying listings and a clear ranking method based on data.
5. **Can't be honest.** If good data doesn't exist (e.g. prices nobody publishes), only write it if public sources are solid enough to give ranges with sources, and say clearly how uncertain they are. Never invent numbers.
6. **No reader benefit.** If you can't say in one sentence how the reader is better off after reading, drop it.
7. **Off topic.** The topic must be something the site's own visitors search for (`topics.core`, or `topics.adjacent` if the owner allowed them). Articles about unrelated subjects get no traffic and blur what the site is about. A topic only qualifies if a reader of it would naturally click through to a listing or location page.
8. **Your own pages already answer it.** "Where are the most <listings> by state", "<listings> in <state>" and similar are what the directory's location and category pages are for. An article on that competes with the site's own money pages. Drop it; at most suggest improving the page itself.
9. **No proven demand.** Data edge alone is not enough. The topic needs real search demand: Search Console impressions, a volume number from a connected tool, or 3+ autocomplete variants plus People Also Ask. "Our data is unique" with no searcher asking = drop.

**Thin data:** if most candidates fail gate 1 because the listings table is thin (key columns mostly empty), stop researching and tell the owner which fields are empty (e.g. "wash type is empty on 44 of 44 listings"), and suggest running reddit-listing-research or listing-check first to fill them. Owner-given topics can still be written.

Rank the survivors by total score. Keep at most `max_articles_per_month` (default 4).

## Step 5: Report to the owner and let them pick

Save `notes/<slug>/content/opportunities-YYYY-MM-DD.md` and show a short table:

| Article idea | Kind (guide, list, comparison) | Proof people search it | Who shows up on Google now | What we know that they don't | Page it sends readers to | Score (out of 12) |

Also list dropped ideas in one line each with the plain reason ("not enough data in your listings yet", "your city pages already answer this"), so the owner sees the filter working. Use plain words in this report: no gate numbers or internal terms.

Save the survivors as the **queue** in `notes/<slug>/content/log.md` (status `queued`, in score order). If the quality bar is not approved yet, ask: "Which one should I draft first?" Once it is approved, don't ask; the weekly run takes the top of the queue.

## Step 6: Write the draft

**Write the article yourself, section by section.** Never generate articles with a script, template or loop. Before writing, read the `voice_page` and the best existing article and match their tone: friendly, plain, helpful. **No voice page and no articles yet** (new site): write in a plain, friendly tone an 8th grader can read: short sentences, "you", no hype.

**Fresh data only:** before using a fact about hours, prices or anything that changes, check how fresh it is (the listings' `updated_at`). If you can't tell or it's older than 3 months, write it as "as listed on <brand>" and say so in the sources line, never as a promise.

Write for the searcher's actual situation. Plain words, short sentences, about an 8th grade reading level. No fluff intros.

Structure:

1. **Title** with the main phrase, plainly worded.
2. **Quick answer** in the first 2 to 4 sentences. Directly answer the question (this is what AI answers and featured snippets quote).
3. **Key facts** (optional, a short blockquote, no heading) with 2 to 4 of our most useful facts, each phrased so it can be quoted alone and naming the brand, e.g. "> Only about 1 in 3 car washes listed on <Brand> is open 24 hours (November 2026)."
4. **The body**, which depends on type:
   - **Guide / how many / how much:** steps, a simple table, real examples, what changes the answer.
   - **Listicle:** a "How we picked" section first (criteria from the data), then each entry with why it made the list, what it offers (from data), area served, and a link to its listing page. Never rank by who pays.
   - **Comparison (X vs Y):** a side by side table, then "choose X if / choose Y if".
5. **FAQ** with 3 to 6 real questions from autocomplete, People Also Ask or forums.
6. **Next step:** a clear call to action linking the right money page (search, quote form, city or state page).
7. **Sources:** one short italic paragraph at the end saying where numbers came from, in plain words (no internal names).

Search intent first (most important):
- Before writing, write down in one line who is searching and what they need to decide or do (e.g. "someone with a new car who wants to know if touchless washes are safe for the paint and which ones are near them"). Every section must move that person closer to their decision.
- **Every H2 is a question or phrase the searcher would actually type or ask**, taken from autocomplete, People Also Ask, related searches or forums (e.g. "Are touchless car washes safe for paint?", "Touchless vs soft cloth car wash: which is better?", "How much is a car wash membership?"). Headings are also keyword opportunities: use the real phrasing people search.
- **Never write headings about our data, our directory or our method** (bad: "What wash types are actually listed?", "Examples from listings in the directory", "Sources and method", "Quick answer").
- **Translate every fact into advice.** Don't just state "49.6% of car washes offer a monthly membership". Say what it means for the reader: "About half of car washes sell a monthly plan, so if you wash more than twice a month it's worth asking. Only about 1 in 6 is open 24 hours, so check hours before a late trip." Put the fact inside the section where it helps the decision, not in a separate data section.
- **Never show internals to readers:** no database or column names, no site codes or slugs (write the brand name, never a site code like "SCW"), no words like "queried", "records", "rows" or "active listings in our table". Say "companies listed on <Brand>" instead.
- The quick answer is the opening paragraph (bold the key sentence), not a heading.
- Sources go in one short italic paragraph at the very end ("Sources: ..."), not an H2.
- **Naming companies:** in general or national articles (sizing, cost, how to, comparisons) do NOT name individual companies or add "examples from our listings" sections; it distracts and reads like an ad. Name companies only in local articles or "best companies in <area>" listicles, where they are the point.
- **Tables over charts:** put numbers in simple markdown tables (Google and AI answers can read tables; they can't read chart images), keep them to 2 to 4 columns, and follow each table with one plain sentence saying what it means for the reader.

SEO and layout rules:
- Use `##` (H2) for each main section, 4 to 8 of them. The site builds the table of contents from them automatically. Use `###` for sub points.
- Prefer landscape photos for `hero_image_url`; the site shows images in a 16:9 frame.
- Put tables in markdown when comparing options or sizes; tables get quoted by AI answers and featured snippets.
- **Images, no credits needed:** (1) every article gets an automatic branded cover image from the site, so a photo is optional; (2) photos from listings belong to those businesses, so use them sparingly: at most 1 per article, only if it clearly shows what the text describes, always with `hero_image_credit` ("Photo: <Company>"), and in general articles keep the caption about the photo, not a promotion of the company. In local or "best companies" articles, use each featured company's own photo next to its entry. (3) AI generated images only if `content.ai_images: true` (off by default, it costs credits).
- `tags`: 2 to 4 short topic tags (e.g. `membership`, `touchless`, `cost`, `24-hour`). The site uses them to show related guides at the bottom, so reuse existing tags when they fit.
- The site automatically adds at the bottom: a quote call to action, related guides, and browse by state links. Don't repeat those in `body_md`; put your internal links in the text where they help the reader.

Content rules:
- At least 2 facts from our own data, each with a plain source line.
- 3 to 6 internal links, every one useful at that point in the text, with at least 1 to a money page.
- Mention the brand naturally 2 to 4 times as the source of the data (helps AI answers cite the site). No keyword stuffing. The checker counts the brand only with its exact capitalization ("Austin Car Washes", not "austin car washes" in a sentence).
- Different angle, intro and structure from every earlier article in the log. Never reuse paragraphs.
- **At most ONE "check before you go" sentence per article** (call ahead, check before, hours can change, may vary). One clear reminder helps; repeating it reads as unsure and wastes the reader's time. The checker fails on 2 or more.
- **Numbers must agree everywhere.** If the quick answer says 3 of something, the body must say 3 too (or explain the difference, e.g. "3 in Austin, 1 more in Round Rock").
- No made up quotes, reviews, prices or statistics. Every number comes from Step 1 facts or a public source you actually opened.
- **Facts about a business come only from the business's own website or its Google profile.** Never from another directory, listicle, review aggregator or competitor (they copy each other and go stale); listing-check's `untrusted_domains` and every directory-type site are never sources.
- **Outbound links:** at most 4, only to sources a reader would trust for that fact (official sites, government, the business itself, major news). Never to competitors, other directories or listicles in the niche, `never_link` domains, or anything unrelated to the sentence.
- Check the draft against the top 3 ranking pages: ours must answer better, show data they don't have, and be easier to read. If not, improve it before saving.

Save to `notes/<slug>/content/drafts/<url-slug>.md` with a header: target phrase, intent, suggested URL, meta title (max 60 characters), meta description (max 155 characters), internal links used.

## Step 7: Badge (listicles only)

For each company in a listicle, prepare a copy and paste snippet linking to the article:

```html
<a href="<article_url>" title="<Badge text> by <Brand>"><img src="<badge_image_url>" alt="<Badge text> by <Brand>" width="160" height="160"></a>
```

Badge text is specific and true, e.g. "Top Touchless Car Wash, Austin 2026". Propose a simple badge design to the owner first. Never email companies about badges unless the owner explicitly allows it (outreach rules in the notes).

## Step 8: Publish (if `content.publish` is `supabase_articles` or `wordpress`)

1. **WordPress:** create the post with `status: draft`, the meta title and description (Yoast or Rank Math fields if present), FAQ as a section at the end, and use the post's preview link in the approval step. Publishing = set `status: publish`. **Supabase:** insert the article into the `articles` table with `status: draft`: `slug` (lowercase words joined by hyphens, from the target phrase), `title`, `meta_title`, `meta_description`, `excerpt` (1 to 2 sentences for the guides list), `body_md` (the article in markdown WITHOUT the H1 title and WITHOUT the FAQ), `faq` as JSON `[{"q": "...", "a": "..."}]`, `target_phrase`, `author`, `tags`, and the image fields if used.
2. Internal links in `body_md` are relative paths (`/car-washes/texas`). Check every link returns a real page before publishing. **No live pages yet** (new site, `drafts_only`): run the checker with `--no-http` (that's allowed only then), use only paths built from the config's URL pattern, and list every internal link for the owner to confirm before they post.
3. **Run the checker:** save the article as JSON and run `python3 <this skill's folder>/article_check.py article.json --site https://<domain>` (installed path: `/data/skills/directory-ops/content-opportunities/article_check.py`) (fields in the script header; include every fact and source you used, the brand, internal names and `never_link`). Fix any failure by rewriting that part by hand and run it again. Never publish while it fails.
   **Quality gate (must all pass, or keep it as a draft and tell the owner why):** every H2 is a real searcher question or phrase (none about our data or method); every fact is turned into advice; no internal names (table names, site codes like the slug, "queried"); quick answer in the first paragraph; at least 2 facts from our data with a source line; 3 to 6 working internal links including a money page; FAQ with 3 to 6 real questions; no invented numbers; **counts include only valid listings (closed, test and off-type rows excluded; host businesses like gas stations counted separately and named as such), which the checker cannot see, so check it yourself against facts.md**; no business facts from other directories or review sites; different angle from every earlier article in the log; reads easily.
4. **Approval:** if `content.approval` is `first_article_only` and no article has been approved yet (check the log), or `approval` is `every_article`, ask on the `notify` channel. **With `publish: drafts_only`** (no preview link exists) send instead:

   ```
   I wrote a new article: <title>

   <the WHOLE article: title, every section, the FAQ, the sources line>

   Publish-ready? Reply yes or no.
   (Saved at notes/<slug>/content/drafts/<url-slug>.md)
   ```

   Paste the full article so the owner can read all of it in the chat; never just a summary or the first paragraphs.

   "yes" = the quality bar is approved and you send the "Publishing a draft by hand" steps. **With a blog** ask with exactly this message and nothing else:

   ```
   I wrote a new article: <title>
   Read it: https://<domain><blog_path>/preview/<slug>?token=<preview_token>
   Publish it? Reply yes or no.
   ```

   Log it as `awaiting_approval` with the slug. When the owner replies, take the newest `awaiting_approval` entry: **yes** = publish now (steps 5 and 6); **no** = keep it as a draft, ask once "What should change?", and if they answer, save the rule to `notes/<slug>.md` under "Content rules" and rewrite. A reply with comments counts as no plus the change. Only one article waits for approval at a time; if one is still waiting at the next run, remind once and don't write another.

   **How the reply reaches you:** the owner answers in the same place the message arrived (the Hermes chat, or the Telegram chat if `notify: telegram`). That reply starts a normal conversation with you: read `notes/<slug>/content/log.md`, take the newest `awaiting_approval` entry, and act on it right away. If no conversation picks it up, the next scheduled run reads the reply the same way.

   The first approved article is the **format and quality bar**: record "quality bar approved" in the log with the article slug, plus any rules the owner adds to `notes/<slug>.md` under "Content rules". After that, publish without asking, **but only when a publish method exists** (`publish` is `supabase_articles` or `wordpress`). With `publish: drafts_only` nothing is ever published by you: every finished draft goes to the owner with the steps in "Publishing a draft by hand". If `content.approval` is `every_article`, always ask.
5. Publish by setting `status: published` and `published_at`. If the config has `content.revalidate_url` (with its secret in the env var `content.revalidate_secret_env`), call it for `/blog` and the article path so it's live immediately; otherwise it appears when the site's cache refreshes. Open the live URL and confirm it shows before telling the owner.
6. Never publish more than `content.publish_cadence` allows (e.g. `weekly` = at most 1 article per 7 days). Extra approved topics wait in the queue in the log.

## Step 9: Log it

Append to `notes/<slug>/content/log.md`: date, topic, target phrase, status (proposed, drafted, published, rejected), and the reason if rejected. Commit and push `notes/` (CATALOG.md rule 6).

## Summary

Plain words, max 6 lines, starting with what the owner needs to do:
- Waiting on you: which article to write first, a draft to approve, or a draft to post
- Ideas: how many found, how many made the cut, the top reasons the rest didn't
- Recommended order (titles)

## Publishing a draft by hand (`publish: drafts_only`)

When a draft is approved, send the owner the finished article and these steps, in this exact shape (no technical words):

```
Your article is ready: <title>
1. Open your site's editor and start a new post or page (WordPress: Posts → Add New; Webflow: CMS → Blog → New item; Wix: Blog → Create post).
2. Title: copy this line → <title>
3. Text: copy everything between the two lines below and paste it into the post body.
   ---
   <the article, with headings and links, in the format the editor accepts: plain text with headings for most editors; HTML if the owner said their editor takes HTML>
   ---
4. SEO title (often under "SEO" or "Search preview"): <meta title>
5. Description: <meta description>
6. URL / slug: <suggested slug>
7. Publish, then send me the live link so I can check the links work and log it.
```

When the owner sends the live link: open it, check every internal link loads, mark the topic `published` in the log with the URL. If they don't reply within 7 days, remind once in the next run's summary; never write the next article while one waits.

## Setting up publishing (optional, one time, for the owner)

This removes the copy-paste step. Hermes can't add pages to a website by itself. Tell the owner plainly, then give them this to paste into Claude Code (or send to their developer) in the website's own project: First time? Walk them through `/data/skills/directory-ops/setup-guides/guides/paste-into-claude-code.md`.

```
Add a /blog section to this site that reads articles from a Supabase table called articles (columns: slug, title, meta_title, meta_description, excerpt, body_md, faq jsonb [{q,a}], status draft|published|archived, preview_token uuid, author, published_at, updated_at). Create the table with RLS so anon can only select published rows. Pages: /blog (list of published, newest first), /blog/[slug] (render body_md as markdown with tables, FAQ section with FAQPage schema, Article schema, canonical URL, cached and revalidated every 5 minutes), /blog/preview/[slug]?token= (shows drafts when the token matches, noindex). Add published articles to the sitemap. Each article page gets: a table of contents from its H2 headings, an optional hero image with credit (hero_image_url, hero_image_alt, hero_image_credit columns), an automatic branded Open Graph image, related articles chosen by shared tags (tags text[] column), links to the top locations/categories pages, Article + FAQPage + BreadcrumbList schema, reading time and updated date. Add a Blog link in the footer. The /blog list should look polished: the newest article as a large featured card, the rest as a 2 column card grid, text first (title, excerpt, date, reading time); show a photo on a card only if the article has a real photo, never the generated title card. Article images sit in a 16:9 frame so tall photos never dominate. Match the site's existing header, footer and styling, and end each article with a call to action to the site's main lead or signup page. Also add a secured route /api/revalidate?secret=<REVALIDATE_SECRET env var>&path=<path> that revalidates that page, so new articles go live right away. If an articles table already exists (for example from an AI blog tool), add the missing columns to that same table instead of creating a new one (status defaults to published so existing articles stay live) and keep rendering old articles the way they render today. Build on a branch, give me the preview link, and don't merge until I approve.
```

When it's live, set `content.publish: supabase_articles`, `content.revalidate_url: https://<domain>/api/revalidate` and `content.revalidate_secret_env: <SLUG>_REVALIDATE_SECRET` in the site config. The owner adds the same secret value to the website's hosting env vars and to Hermes (walk them through `/data/skills/directory-ops/setup-guides/guides/add-a-setting-in-hostinger.md` with the setting name `<SLUG>_REVALIDATE_SECRET`).

## Schedule (set up after the quality bar is approved)

Create ONE scheduled job per site at `content.publish_cadence` (e.g. every Tuesday) and confirm its ID to the owner. Each run:

0. If an article is `awaiting_approval`, don't write another. Remind the owner once with the same message, then stop.
1. If the queue has a `queued` topic: run Steps 6 to 9 for the top one (write, badge if listicle, quality gate, publish, log). Then tell the owner: title, live link, target phrase, what it links to. With `publish: drafts_only`, "publish" means: send the owner the finished draft and the "Publishing a draft by hand" steps, log it `drafted`, and don't write the next one until they say it's posted (or 7 days pass, then remind once).
2. If the queue is empty AND the last research was more than `content.min_days_between_research` days ago (default 30): run Steps 1 to 5 to refill the queue, then publish the top topic if one qualifies.
3. Otherwise: say "No topic good enough this week, skipping" and stop. This is a cheap run, and it is the right outcome when there is nothing strong to write.

Publishing fewer articles is fine. `max_articles_per_month` is a ceiling, never a target. Only topics whose plain total is at least `content.min_score` (default 9 of 12) enter the queue. Topics the owner gave (`queued (owner)`) skip the score.

If the quality gate fails, keep it as a draft, tell the owner why, and do not try another topic in the same run.

The owner can pause it at any time ("pause content for <site>"). Only enable content on sites where the owner asked for it, to keep total credit use predictable across many sites.
