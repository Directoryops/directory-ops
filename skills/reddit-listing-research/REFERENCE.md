# Reddit listing research: reference

Details moved out of SKILL.md so the core stays short. SKILL.md points here by section (R0, R1...). Read a section when its step sends you here.

---

## R0. Setup questions (full mode), with examples

First fill every answer you already have from `sites/<slug>.yaml` and `notes/<slug>.md` (name, URL, business type, one city or national, money model, where listings are stored). Ask the rest **one question per message**, in plain words, with the example answer in brackets so the human knows what you mean (they can reply "use the defaults for the rest" for any question that has a sensible default, like the budget). If an answer is vague, ask one follow up.

1. What is your directory called, and what is its URL?
2. What type of business does it list? [funeral homes and cremation providers]
3. What decision is your visitor making when they land on a listing? Finish this sentence: "My visitor is trying to choose a ___ so they can ___." [choose a funeral home so they can arrange a cremation for a parent]
4. Who is usually making the decision, and what is their situation? [adult children, under time pressure, worried about cost]
5. Is the directory for one city or region, or national? [Los Angeles]
6. How does the directory make money? Pick one: **ads**, **affiliate**, **lead gen or paid listings**, **selling your own product**, **not yet**. [lead gen]
7. Where are your listings kept, and do most of them have a website? [in Supabase, about 400 listings, most have a website] (skip if you already know from the site setup; count them yourself)
8. Do you already know any subreddits where people talk about this decision? [r/askfuneraldirectors]
9. What is the most you want to spend on AI for this whole run, in dollars? [$10]

**Then repeat everything back in a short plain summary (3 to 5 lines) and ask one question: "Shall I start?"** Do not continue until they say yes. (Quick mode: skip this; the onboarding plan was the yes.)

---

## R0b. Teach me your way (full wording)

This is what makes the helper yours instead of generic. Ask once (in quick mode it replaces settings questions, it doesn't add many):

> Tell me what you already know your visitors care about, which details you'd love on every listing, and anything that's off-limits. Ramble or send a voice note; it makes me much better. (Or say "skip".)
> For example:
> - Wedding venue: "People always ask about the catering rules and the rain plan."
> - Plasma center: "Pay per donation is the number one question. Nothing that sounds like medical advice."
> - Roofing: "Warranty length and whether they handle insurance claims."

Turn the owner's OWN answer (never invent rules when they said skip) into 3 to 7 short numbered rules in plain words, show them back ("Got it, I'll: 1) … 2) … Anything to change?"; in quick mode end with "Say 'change …' anytime." instead of a question, so onboarding stays short), and save them in `notes/<slug>.md` under `## Listing research rules` (create the section if it's missing). **Every run reads that section first and follows it; this skill's own safety rules still win** (a rule can't make it skip approval, delete things, or use competitors as sources).

**Learn from corrections:** when the owner rejects or edits one of your proposals, or says "no, because …", ask once: "Want me to remember that as a rule for next time? (yes/no)". Yes: add it to `## Listing research rules` in plain words with today's date.

---

## R1. Settings file word lists

Create the research folder, then copy `research.example.json` from this skill's folder to `research.json` in it. Replace every value with the answers from Step 0. Fill the word lists like this:

| Setting | What to put | Example (funeral homes) |
|---|---|---|
| `business_words` | 3 to 6 word stems for the business type. Short stems catch more ("cremat" catches cremation and cremated). Only used to filter posts from **local** (city) subreddits; focused subreddits are already on topic. | funeral, mortuary, cremat, cemeter, burial |
| `decision_words` | Words that show someone is choosing, paying, comparing, or had a problem. **Keep the generic ones from the example** and add 3 to 8 niche ones. | keep the example list, add "direct cremation", "viewing" |
| `exclude_words` | Whole words that pull in look alike topics you do NOT want. Think: pets, jobs, schools, the industry talking to itself. | cat, dog, pet, salary, hiring, mortuary school |
| `local_title_words` | ONE word each. The business type as people would type it in a title. Only used for city subreddits. | funeral, cremation, mortuary |
| `page_hint_words` | Words that appear in the links of a business site that lead to useful pages. | cremation, price list, viewing |

**Warning about local words (tested):** in a city subreddit, a general word catches the wrong businesses. For dog trainers in r/Austin, `trainer` returned mostly **personal** trainers. Pick the most specific single word (`dog`), and add the look alikes to `exclude_words` (`personal`, `gym`). Step 4 is where you catch this.

Leave `limits` as in the example unless the human asked otherwise.

Leave `company_facts` as `"ask"`: chain company rules are used and labeled, and the owner confirms them once at the approval sheet (Step 11).

---

---

## R2. Choosing subreddits

**First find the niche's OWN community.** The obvious name is often dead or tiny, and the real community has a slang name (tested: plasma donors don't talk in r/plasmadonation, about 1 comment per post; they talk in r/plassing, about 9). A name search alone never finds slang names. Do both:

1. One normal web search (NOT limited to reddit.com, see Rule 1): `best subreddit for <customers of this niche>`, e.g. "best subreddit for plasma donors". Note every r/<name> you see.
2. Run the finder with 2 to 4 niche words (the business word AND the customer word) and 2 to 4 big subreddits where these customers also post:
   ```
   python3 $S/discover_subs.py --words plasma donor --general beermoney Frugal povertyfinance --also <names from the web search>
   ```
   It reads the busiest matching threads and counts which communities people RECOMMEND ("ask on r/…"), then ranks every candidate by activity (posts per day x comments per post). About 3 to 5 minutes, free.

**The PRIMARY row goes first in `focused` and is the main source** (unless its description shows it's off topic). A community with under about 2 comments per post gives almost nothing: use it only as a second source. Then add the kinds below.

You need two kinds of subreddits:

- **Focused** (2 to 4): small subreddits about the topic itself, the niche's own community first, where people ask for advice. Examples: r/askfuneraldirectors for funerals, r/AgingParents or r/dementia for senior living, r/CarWash or r/AutoDetailing for car washes, r/HomeImprovement for contractors, r/DogAdvice for dog trainers.
- **Local** (0 to 2, only if the directory is for one city): the city's main subreddits. Examples: r/AskLosAngeles, r/LosAngeles, r/Austin, r/AskNYC.

Rules for choosing:
- Prefer subreddits where **customers** ask questions over subreddits where **workers** chat. Worker subreddits are full of career talk.
- An "ask" subreddit (r/askfuneraldirectors) is usually the best one. It is customers asking professionals.

Write your candidates down, then check them:

```
python3 $S/check_subreddits.py askfuneraldirectors funeral FuneralDirectors AskLosAngeles
```

Read the output:
- `NOT FOUND or empty` means remove it.
- `ARCHIVE TIMEOUT` means wait one minute and run again.
- Focused subreddits with fewer than about 0.5 posts a day give very little data. Keep them only if nothing better exists.

**Show the human the list with the activity numbers. Ask them to approve or edit it.** Then put the approved names in `research.json` (`focused` and `local`).

---

---

## R3. Downloads (posts and comments)

### Step 3: Download posts

```
python3 $S/pull_posts.py
```

- Takes 5 to 20 minutes. Free. Do not run anything else against the archive while it runs.
- It prints how many posts came from each subreddit, then a TOTAL.
- **Expected:** focused subreddits give up to 4,000 posts each. Local title searches give 0 to 100 each.
- If a subreddit gives fewer than 100 posts, that is fine. It is just a small subreddit.
- If TOTAL is under 300, tell the human and suggest 1 to 2 more focused subreddits (repeat Step 2).

---
### Step 5: Download comments

```
python3 $S/pull_comments.py
```

- About 8 seconds per thread. 250 threads takes about 35 minutes. Free.
- **If it stops for any reason, run the exact same command again.** It continues where it left off.
- A few failed threads (under 5%) are normal. Ignore them.
- **Expected result for 250 threads:** roughly 4,000 to 6,000 comments.

---

---

## R4. Filtering thin niches (plan B)

**If the niche is thin** (after one widening round you still have under about 40 on-topic conversations): widen once more to big general subreddits where customers ask (for example r/dogs, r/HomeImprovement, r/personalfinance, r/AskWomen, r/AskMen, r/weddingplanning, whichever fit) using ONE title word for the business type (`local_title_words` style, e.g. "groomer"). Still thin → stop and tell the owner plainly: "There aren't enough real conversations about choosing a <business type> for me to trust the results. I'll use the questions people type into Google instead." Then build the field list from Google's "People also ask" and autocomplete questions (a few web searches) and mark the report "based on Google questions, not Reddit". Never pad fields from a handful of threads.

---

## R6. Reading batches: format and rules

### 6b. Read each batch and write one JSON file per batch

For **each** batch file, read the whole file, then write `extractions/batch_001.json` (same number). Use this exact format: a list with one object per thread.

```json
[
  {
    "thread_id": "1abc234",
    "relevant": true,
    "factors": [
      {"factor": "price of direct cremation", "quote": "Is $2200 normal for a direct cremation?"},
      {"factor": "can we see the body before cremation", "quote": "My biggest regret is not seeing my dad before cremation."}
    ],
    "prices": ["direct cremation $2,200, Los Angeles"],
    "red_flags": ["funeral home held the death certificate until the family paid $7,000"]
  }
]
```

**Reading rules. Follow all of them:**

1. A **factor** is something a person cares about, worries about, compares, or wishes they had known **before choosing a business**. Write it as a short plain phrase, 3 to 8 words.
2. Only include factors that relate to **choosing between businesses**. Skip grief, family drama, history, jokes, and workers talking about their jobs.
3. If the whole thread is off topic, write `"relevant": false` and empty lists.
4. `quote` must be copied **exactly** from the batch text, under 25 words. Never paraphrase inside a quote.
5. `prices`: only real numbers someone wrote. Include what it was for and the place if given. Never estimate.
6. `red_flags`: bad things a business actually did, in one short sentence each.
7. Do not count anything. Code counts later.
8. Do not write anything except the JSON.
9. Long posts and comments are shortened and end with `[...]`. Quote only words you can see; never finish a cut-off sentence.

### 6c. Check your quotes

```
python3 $S/check_batches.py
```

Every quote must be found word for word in its batch. Fix each `FIX` line (copy the exact words) and run it again until it prints `OK`.

**Budget check:** after the first 3 batches (or after all of them, if there are 3 or fewer), check your AI usage in Hermes (or your AI provider's usage page) and tell the human the before/after and the likely total for all batches. Never estimate from memory; if you can't see usage, say "I can't see the usage meter; please check it" and ask before continuing. If the likely total is over `max_ai_spend_usd`, stop and ask. 🛑

---

---

## R7. Merging factors

### 7b. Group them into one short list

The same idea will be written many ways ("cost of cremation", "cremation price", "how much is cremation"). Write `factor_map.json` that maps **every** name printed in 7a to one canonical factor:

```json
{
  "cost of cremation": "Direct cremation price",
  "cremation price": "Direct cremation price",
  "how much is cremation": "Direct cremation price",
  "can we see the body before cremation": "Viewing before cremation",
  "sad about my dad": "DROP"
}
```

Rules:
- Aim for **12 to 25 canonical factors**. Not more.
- Canonical names are short and specific ("Owns its own crematory", not "Quality").
- Map anything that is not about choosing a business to `"DROP"`.
- Every name from 7a must appear in the file. Copy them exactly.

### 7c. Build the report

```
python3 $S/build_report.py
```

This counts **threads** (not comments) per factor and writes `output/research_report.md`.

---

---

## R8. Listing fields: format, money fields, ordering

Read `output/research_report.md`. For each canonical factor, decide if it can become a **field on a listing page**. Write `output/fields.json`:

```json
[
  {
    "field": "direct_cremation_price",
    "label": "Direct cremation price",
    "type": "price",
    "why": "Raised in 25 threads. The number one question.",
    "found_on_site": "likely",
    "where_to_look": "pricing page, price list PDF, cremation services page",
    "threads": 25
  }
]
```

Allowed `type` values: `yes_no`, `price`, `number`, `short_text`, `list`.

**Money fields:** add `"money": true` to every field that holds an amount that can change (prices, pay, bonuses, fees, promotions), even when its type is `short_text` ("Up to $775 in the first month"). The checker then (a) never takes it from a chain's company pages, only from this location's own page, and (b) stamps it with an "as of" date, which Step 12 shows to visitors ("$45 (as of Nov 2026)").

Allowed `found_on_site` values:
- `likely`: businesses usually state this on their own website (prices, services offered, hours, ownership).
- `sometimes`: some do, many don't.
- `never`: only found in reviews or by calling. **Do not make these fields.** Put them in a separate list called `not_extractable` so the human sees them. They are still useful for writing guides.

**Order the fields using the money model from Step 0:**

| Money model | Put these fields first |
|---|---|
| **Lead gen or paid listings** | Fields that help someone pick and contact a business: prices, services offered, availability, service area. These make leads better. |
| **Affiliate** | Fields that connect to products people buy: brands carried, products used, what to bring or buy. |
| **Ads** | Fields that make many unique, useful pages: lots of comparable facts per listing. |
| **Own product** | Fields that show the problem your product solves. |
| **Not yet** | Order by number of threads only. |

Keep **5 to 15 fields**. Fewer good fields beat padding: never add a field just to reach a number.

**Thin evidence:** a field raised in only 1 thread is weak. Keep it only if it's clearly useful AND likely on business websites, and mark it "(1 thread)" when you show the owner. If fewer than 80 threads were read in total, say so: "This is a small sample; the ranking may change with more data."

Save the `never` fields as `output/not_extractable.json`: `[{"factor": "...", "threads": 3, "why": "only in reviews"}]`.

**Show the human the field list, with thread counts and the `not_extractable` list. Ask them to approve, remove, or add fields.** Do not continue until they approve.

---

---

## R8b. Making room for the fields (click by click)

Values need a place to live and a place to show. Tell the owner first, in plain words: "These details need a spot in your listings before I can save them. It's a one-time setup of a few clicks in Supabase. Want me to walk you through it?"

1. **A column per field in the listings table.** Check which fields already have a column (`db.py select --limit 1` shows the column names). For each approved field without one, walk the owner through it, one click at a time, never SQL:
   1. Open `https://supabase.com/dashboard/project/<project ref>/editor` (project ref = the part before `.supabase.co` in `database.url`) and click the listings table.
   2. Click **Insert** → **Insert column**.
   3. Name: the field name from `output/fields.json` (for example `direct_cremation_price`). Type: **text** (use **bool** only for yes/no fields if they prefer). Leave "Default value" empty. Click **Save**.
   4. Repeat for each field, then tell you "done". Check with `db.py select --limit 1` that every column now exists.
   If a field should go into an existing column with a different name, add `"column": "<that name>"` to that field in `output/fields.json`, but only if that column means the same thing and holds the same kind of value (never put a yes/no into a list or text column that means something else).
   Not on Supabase: the owner adds the columns in their own tool, then imports `output/approved.csv` (Step 12).
2. **Show them on the listing page.** New columns don't appear on the website by themselves. Hermes can't edit website code, so give the owner this prompt once, for Claude Code or their developer, in the website's project:

```
On each listing page, add a "Good to know" section that shows these fields from the listings table when they have a value: <field: label list from output/fields.json>. Show nothing for empty or "unknown" values. Keep the page's existing layout, URLs, titles and headings. Build on a branch and give me the preview link before merging.
```

Continue when the columns exist. The website section can come later; the data waits safely in the table.

**If the owner can't or won't add columns now:** continue anyway. Step 12 saves every approved value in `output/approved.csv` and tells you which columns are missing; the values can be written later with one command.

---

---

## R9. Exporting listings and fetching sites

The listings file must be at `data/listings.csv` with the columns `id,name,website`. Make it with the export helper:

- **Supabase sites** (column names from the site config):
  ```
  python3 /data/skills/directory-ops/directory-db/db.py select --site-url <database.url> --key-env <database.key_env> \
      --table <listings table> --columns <id col>,<name col>,<website col>,<address col> --all > data/listings.json
  python3 $S/export_listings.py data/listings.json --id <id col> --name <name col> --website <website col> --address <address col>
  (The address lets the checker tell whether a chain's website page is about THIS location.)
  ```
- **Any other site:** ask the owner for a CSV export of their listings (any column names), save it in `data/`, then
  `python3 $S/export_listings.py data/<their file>.csv --id <col> --name <col> --website <col>`.

It prints how many listings have a website. Only those can be enriched; tell the owner the number.

```
python3 $S/fetch_sites.py --limit 5
```

This downloads the text of each business's own website (homepage plus up to 4 useful pages) into `sites/<id>.txt`. Free. No AI. `--limit 5` keeps going until 5 sites actually worked; sites that block, error, or show only "Loading..." (they need JavaScript) are listed in `sites/_failed.txt` and skipped. Tell the owner how many failed. Lines ending in `blocked_by_security_<name>` are sites whose security turns away simple scanners (not broken): read them with your built-in web reader (mandatory, SKILL.md Rule 7; never ask the owner to paste pages) and save the text in the same `sites/<id>.txt` format (`=== PAGE: <url>` then the text), at most 20 per run because each one uses AI credits.

### Step 9b: Chains (when many listings share one website)

Chain location pages are often thin (hours, phone, address); the useful facts (how you get paid, walk ins, what to bring, who can use it) sit on the chain's company pages. Read those ONCE per chain instead of guessing per location:

```
python3 $S/chain_pages.py            (chains with 5+ listings; --min 3 for small directories)
```

It saves each chain's FAQ, first visit, requirements and payment pages to `sites/_chains/<domain>.txt` (it reads the sitemap when the menu is built by JavaScript). Tested: it took a 3-listing preview from 6 of 21 values filled to 14 of 21.

Then do **Step 10** for only these 5 listings (write the staging files yourself, by reading each site file; never generate them with a script), then run the check in **Step 11**.

**Show the human the 5 results as a preview of the finished listing, not just the sheet.** For the best of the 5, write it the way it would look on the page:

```
<Business name>: Good to know
- Direct cremation price: $1,095 (from their price list)
- Owns its own crematory: Yes
- Viewing before cremation: unknown
```

Then the 5 rows of `output/review.csv` with quotes and links. Ask: "Is this what you want your listings to show, and are these correct?" If not, fix the field list or the extraction rules first. Only then run everything.

---

---

## R10. Extraction format and rules

For each listing that has a `sites/<id>.txt` file, read that file and write `staging/<id>.json`. Long site files: you may search the file for each field's words (`grep -i -n "<word>" sites/<id>.txt`) instead of reading every line, but every quote must still be copied exactly from the file:

```json
{
  "id": "123",
  "name": "Example Mortuary",
  "fields": {
    "direct_cremation_price": {
      "value": "$1,095",
      "quote": "Direct Cremation Package $1,095",
      "source_url": "https://example-mortuary.com/pricing"
    },
    "owns_crematory": {
      "value": "unknown",
      "quote": "",
      "source_url": ""
    }
  }
}
```

**Extraction rules. Follow all of them:**

1. Include **every** approved field, in every file, even when unknown.
2. A value is allowed **only if the website text states it**. Copy the exact words into `quote`. Copy the `=== PAGE:` URL it appeared under into `source_url`.
3. If it is not stated, write `"value": "unknown"`. Do not guess from similar businesses. Do not use what you "know". Do not use Reddit.
4. `yes_no` fields: write `yes` only if the site clearly says so. If the site does not mention it, it is `unknown`, **not** `no`.
5. `price` fields: copy the price exactly as written, including "starting at" or "from". Do not average or convert.
6. If the site text is empty or is an error page, write every field as `unknown`.
7. **Only facts about THIS location, or a company rule that covers every location.** Look in this order:
   1. This location's own page (`sites/<id>.txt`). Always first.
   2. Still unknown and the listing belongs to a chain in `sites/_chains/`: the chain's company pages. Use them only for **rules that are the same everywhere** (payment method, walk ins or appointments, what to bring, age and weight rules, how the visit works), and add `"scope": "chain"` to that value with the company page URL as `source_url`. The owner sees it labeled "company policy, all <Chain> locations".
   3. **Never take an amount from company pages** (prices, pay, bonuses, fees): they change by location and month. The checker marks those NOT USED.
   Chain websites often say "at select locations", "participating locations" or "may vary". Those don't prove this location has it: write `unknown` unless this location's own page confirms it. (The checker flags these as CHECK SCOPE.)
8. `value` is the plain fact only ("Yes", "$12", "Free vacuums"). No comments or explanations inside the value.

Run the full set in batches of `max_listings_per_run`:

```
python3 $S/fetch_sites.py
```

Then extract as above for each new `sites/<id>.txt`.

---

---

## R11. Approval details

This checks that every quote really appears on the business's downloaded website (or, for `"scope": "chain"` values, on that chain's company pages), that prices and numbers in the value appear in the quote, and flags "select locations" style quotes as `CHECK SCOPE`. Quotes not found are `REJECTED`. It writes `output/review.csv`. Treat CHECK SCOPE like unknown unless the owner confirms it for that location.

- If it prints the **WARNING** (more than 15% rejected), stop. Re read the Step 10 rules, redo the rejected listings, and run the check again.
- Tell the human: how many listings, how many values VERIFIED (and how many of those are company policy), REJECTED, UNKNOWN, the FILL RATE line, and which fields are most often unknown.
- **Company facts question (once, in the approval sheet, with your recommendation):** "Some details come from each chain's company pages, not the location's own page (for example how you get paid, and what to bring). I label them 'company policy, all <Chain> locations'. Use them? I recommend yes: they're the same at every location. I never use company-wide prices or pay, because those change by location and month." Their answer goes in `research.json` as `"company_facts": "allow"` or `"never"` (then run the check again).
- Money values show their "as of" date in the sheet; say once: "Prices and pay show the date I read them, so visitors know how fresh they are." 

**Show the verified values in chat** (numbered: listing, detail, value, the quote, the link) and ask: "Reply 'approve all', 'approve all except 3 and 7', or ask about any number." Then write `y` / `n` in the approve column of `output/review.csv` yourself from their answer (owners who prefer a spreadsheet can mark the file directly). "approve all" = every VERIFIED row. Never approve REJECTED or UNKNOWN values.

---

---

## R12. Writing approved values

Supabase sites, through the safe database helper (dry run first, then show the owner what will change):

```
python3 $S/apply_approved.py --db-py /data/skills/directory-ops/directory-db/db.py --site-url <database.url> \
    --key-env <database.key_env> --table <listings table> --id-column <id col> --slug <slug>
```

If it looks right, run the same command with `--apply`. Money values keep their "as of" date: in a `<column>_as_of` column if the table has one, otherwise inside the value ("Up to $775 in the first month (as of Nov 2026)"). It only writes VERIFIED + approved values, only into empty cells (it never replaces something the owner already wrote; `--overwrite` only if the owner asks), one update per listing, each logged with its source URL in `notes/<slug>/db-changes.jsonl`. If the site config has a revalidate URL, call it so pages update now.

Other sites: give the owner `output/review.csv` filtered to approved rows (save it as `output/approved.csv`) to import.

**Later runs:** new listings can be enriched any time by re-running Steps 9 to 12 (the research and fields from Steps 2 to 8 stay valid for about a year). This job is not scheduled; run it when the owner asks.

---

---

## RT. Troubleshooting

| What you see | What it means | What to do |
|---|---|---|
| `403` from reddit.com | Reddit blocks AI tools | You broke Rule 1. Use the scripts. |
| `ARCHIVE TIMEOUT` or `Timeout. Maybe slow down a bit` | Archive is busy | Wait 1 to 2 minutes, run the same command again |
| `pull_posts.py` gives 0 posts for a local word | Nobody used that word in a title, or the archive timed out | Fine. Move on. Try a different single word if all are 0. |
| `pull_comments.py` stopped halfway | Network hiccup | Run the same command again. It resumes. |
| JSON error when reading archive data | Text was copied through the shell and got mangled | Never pass archive data through `echo`. The scripts save it directly. |
| Kept threads are mostly off topic | Word lists too loose | Add to `exclude_words`, run Step 4 again |
| City subreddit threads are about a different kind of business (personal trainers instead of dog trainers) | `local_title_words` too general | Use a more specific single word, add the look alike to `exclude_words`, run Step 3 and Step 4 again |
| Under 80 threads kept | Word lists too tight, or subreddits too small | Add `decision_words`, or add a focused subreddit |
| `fetch_sites.py` FAIL for many sites | Sites block simple downloads or need JavaScript | Report the count to the human. `blocked_by_security` ones can be read with your built-in web reader (max 20 per run). Never use tricks like fake browsers to get around blocks. |
| `discover_subs.py` PRIMARY is off topic (a TV or physics community for "plasma") | One niche word matches other topics | Pass the customer word too (`--words plasma donor`) and add names from a web search with `--also` |
| Few or 0 threads from the niche's own community | It's quiet (under 2 comments per post) or the wrong one | Run `discover_subs.py` and use its PRIMARY community |
| Chain listings mostly `unknown` | The facts are on the chain's company pages | Run `chain_pages.py` (Step 9b) and use company rules with `"scope": "chain"` |
| Many fields `unknown` | Businesses don't publish it | That is a real finding. Tell the human. It may be a reason to call businesses or ask them to claim their listing. |
| More than 15% REJECTED | The AI is paraphrasing or guessing | Redo Step 10 for those listings. Quote exact words only. |

---

## RC. Costs and time

On Hermes, "AI cost" means Hostinger AI credits. Report credits used after the first 3 batches (Step 6 budget check).

| Step | Time | Cost |
|---|---|---|
| Download 5,480 posts, filter to 250 threads | ~15 minutes | Free |
| Download 5,691 comments | ~35 minutes | Free |
| AI reads all threads | depends on model | the main AI cost of the research half |
| Download business websites | ~5 seconds per listing | Free |
| AI extracts fields | depends on model | the main AI cost of the listing half |
