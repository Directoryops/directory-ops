# Listing Check: reference

Details for `SKILL.md`. Each step there names the section to read here. Nothing in here overrides SKILL.md's hard rules.

## settings

Step 0 in full (first run only).

If `listing_check.settings_done` is not `true`, ask one question per message, each with its default shown (the owner can reply "use the defaults for the rest" at any point). Skip anything the config already answers. Save to `listing_check`, set `settings_done: true`, never ask again (the owner changes a setting by saying so).

**In quick mode (during onboarding), ask only the questions marked `[essential]` that onboarding hasn't already answered, and use the defaults (or what onboarding inferred) for the rest. List the defaults you used in the plan message; the owner changes any of them by saying so.**

```
Questions, one per message (say "use the defaults" anytime to skip the rest):
1. How many listings should I check each week? (default: 20)
2. [essential, unless onboarding already knows what the directory lists, or the owner's description or "Teach me your way" answer says it (e.g. "only real car washes")] What makes a listing valid on your site? e.g. "a touchless car wash, not a hand wash" (default: any open business in your category)
3. Where does the true information for your listings come from? (default: each business's own website, then Google. I never trust other directories or copycat sites; tell me about any you know.)
4. Which details should I keep up to date? (default: hours, phone, website, address, closures, and map location if your listings have one)
5. Should I fix things myself, or show you first? (default: show you first; after a few good runs you can say "fix them yourself")
```

Map to config: `batch_size`, `types[].type_keywords` + the notes' "Listing rules", `untrusted_domains` + notes "Sources of truth", `fields` (include the latitude/longitude columns by default when the table has them), `auto_apply` (default false) and `autonomous` (default false), `report` (default: summary in chat).

**Tell the owner the real cadence** in the confirmation: weeks for a full pass = total active listings ÷ batch size, rounded up (runs are weekly by default). Say "each listing gets checked about every N weeks" (44 listings at 20 a week → about every 3 weeks). Never quote a cadence you didn't compute.

**Proof words (`type_keywords`) come from the owner's own answer to question 2.** Take the nouns that name the kind of business ("a touchless car wash" → `["touchless", "car wash", "carwash"]`; "plasma donation center" → `["plasma", "donation center"]`). Add the one-word spelling if people write it both ways. Show the list in your confirmation ("I'll treat these words as proof: …") so the owner can correct it. Never leave it empty.

**Untrusted domains:** always add the site's own domain (from `site.url` in the config) automatically. Our own pages are our data, not proof.

**Where the run log lives (no setup needed):** by default (`listing_check.log_storage: file`) every check is a JSON line in `notes/<slug>/listing-check/log.jsonl` (`checked_at`, `listing_id`, `result`, `changes`, `sources`, `notes`; `result` is one of `unchanged`, `proposed`, `updated`, `marked_closed`, `opened`, `needs_review`, `not_found`, `wrong_place`) and Google place ids are kept in `notes/<slug>/listing-check/place-ids.json` (`{"<listing id>": {"place_id", "name", "address", "matched_at"}}`). Create the folder and files on the first run. Only if the config says `log_storage: table` use the tables `listing_check_log` and `listing_place_ids` instead (through `directory-db/db.py`). Never ask a beginner to run SQL.

If the listing table has no `updated_at` column that changes on update, tell the owner in plain words: "Your listings don't record when they were last changed, so your site can't show a real 'last updated' date. Your developer can add that if you want it."

## teach-me

This is what makes the helper yours instead of generic. Ask once (in quick mode it replaces settings questions, it doesn't add many):

> Tell me how you keep your listings right today: where you check, what counts as a real listing, any special cases (chains, places inside other stores, seasonal hours), anything I should never do. Ramble or send a voice note; it makes me much better. (Or say "skip".)
> For example:
> - Car wash: "Gas station washes count only if they have a real tunnel. I trust the chain's own location page over Google."
> - Plasma center: "Only licensed donation centers. Hours change around holidays, so check their own site first."
> - Wedding venue: "Never mark a venue closed just because Google says so. Flag it for me instead."

Turn the owner's OWN answer (never invent rules when they said skip) into 3 to 7 short numbered rules in plain words, show them back ("Got it, I'll: 1) … 2) … Anything to change?"; in quick mode end with "Say 'change …' anytime." instead of a question, so onboarding stays short), and save them in `notes/<slug>.md` under `## Keep listings accurate rules` (create the section if it's missing). **Every run reads that section first and follows it; this skill's own safety rules still win** (a rule can't make it skip approval, delete things, or use competitors as sources).

**Learn from corrections:** when the owner rejects or edits one of your proposals, or says "no, because …", ask once: "Want me to remember that as a rule for next time? (yes/no)". Yes: add it to `## Keep listings accurate rules` in plain words with today's date.

## writes

- The run log and place ids (files under `notes/<slug>/listing-check/`, or the two log tables when `log_storage: table`): always.
- All database reads and writes go through `/data/skills/directory-ops/directory-db/db.py` with `--key-env <database.key_env>` and `--allowed-tables <the listing tables>` (plus the log tables when `log_storage: table`).
- Listing tables (`listing_check.allowed_tables`; if missing: every `types[].table`, else `database.listings_table`): only the fields in `listing_check.fields`, only when `auto_apply` is true (or the owner approved the change). Otherwise write proposals to `notes/<slug>/pending.md` in the review-changes format (one block per listing, all its field changes in that block, `old`/`new` as JSON) and tell the owner to reply "approve …". **Block ids continue from the highest id already in pending.md** (start at 1 if the file is new or empty); never reuse an id.
- Never: page URLs or slugs (the listing's own `website` field IS allowed when it's in `fields`), page structure, owner-added photos, reviews, SEO fields, anything under "Never touch" in the notes. Never delete a listing.

## batch

- For each listing type, take active listings by oldest `checked_at` in the log (never checked first), up to `batch_size`. Skip ones checked within `min_days_between_checks`.
- **Short batch:** if fewer listings are due than `batch_size`, check only those. Never re-check a listing inside `min_days_between_checks` just to fill the batch. If nothing or only a few were due, a full pass is done: say "full pass complete" in the summary.
- **No log yet (first runs, or the log file is empty):** order by the listing table's `updated_at` then `id` (`--order "updated_at.asc,id.asc"`; if there is no `updated_at` column, by `id` alone), and skip any id that already has a log line from the last `min_days_between_checks` days. Read the rows with `db.py select --order "updated_at.asc,id.asc" --limit <batch_size × 3>` (or `--all`).
- **"Coming soon" and "temporarily closed" listings are checked EVERY run**, on top of the batch. Find them with the config's `listing_check.coming_soon_column` / `temporarily_closed_column` (skip this if they're empty: the table has no such flag). A "coming soon" badge on a business that's already open is the most visible mistake a directory can make.
  - **Opened** (confirmed by the evidence rules): fill everything at once in the site's format (hours, phone, website, coordinates, Google reviews word for word), clear the coming soon flag and text, set "now open" if the site has it, replace placeholder text. Log `opened`.
  - **Still coming soon:** refresh the expected opening date if an official or news source gives a newer one. Never remove it because nothing new was found.
- **First run ever:** at most 20 listings. It writes nothing to the owner's website or database, even if `auto_apply` is true. Every change goes to `notes/<slug>/pending.md` as a proposal. Tell the owner in plain words: "Nothing on your site changed yet. I found <n> fixes for you to approve:" then the numbered list (review-changes format: name, old → new, why), then "Reply 'approve all', 'approve 1 and 3', or ask about any number."

## sources

| Tier | Source | Can it justify a change? |
|---|---|---|
| 1 | The business's own official page for **this exact location** (its location page, or the parent brand's official locator page for it) | Yes, on its own |
| 2 | The Google Business Profile for this exact location | Hours, phone, website: yes when `usable` is true. Closures: one facet of several. Type: needs a Tier 1 match |
| 3 | The business's own social page with a post in the last 90 days, clearly about this location | Yes |
| 4 | Review sites (Yelp etc.), same exact address | Supporting only, never alone |
| ✗ | Other directories, competitors, listicles, blogs, aggregators, AI summaries | **Never evidence.** A hint of where to look, then confirm at Tier 1 to 3 |

### The one evidence rule

- **Hours, phone, website:** a Google profile with `usable: true`, OR the business's own page for this exact location. If both exist and disagree, use the own location page and say so in the proposal. **Chains:** when the chain has a page for this address, fetch it once and prefer it over Google's hours.
- **Identity (name, address, city), type ("right kind of business") and closure:** 2 agreeing sources, one of them official (Tier 1). Identity is never changed automatically (propose only).
- Anything less: don't change it; log `needs_review` with what you found.
- The evidence link must open the page showing the fact for this exact location (not a homepage or a list of stores).
- Domains in `untrusted_domains` and the notes are ✗.
- **Copies of our own data:** a page matching our listing word for word (same description, same odd formatting, same old hours) was copied from us. It proves nothing.

### Identity fields are locked

Name, street address, city and state identify WHICH business it is. Dense areas have similar locations a few miles apart.

- Never change identity fields automatically. Propose (`needs_review`) only when a Tier 1 source shows the **exact same street address**.
- Don't rename listings to match a brand's new naming unless the owner asks or it moved or closed.
- Match by **full street address** (number + street), never by name or nearby city. No acceptable source = leave it alone.

## google

```
python3 <this skill's folder>/gmaps_lookup.py --listing "<listing name>" "<address line exactly as stored>" "<type keyword>"
```

(Installed path: `/data/skills/directory-ops/listing-check/gmaps_lookup.py`.)

**The listing's address line is the truth.** Pass it exactly as stored; never build it from the title or a city column (titles often name a nearby city). `--listing` tries several wordings before `not_found`, so **one `not_found` means nothing on its own.**

It returns JSON. The fields that decide what you can trust, in plain words:
- `address_match`: Google's address has the same street number and street (and the same ZIP when both have one). City names are ignored on purpose.
- `brand_in_name`: the Google place's name contains the listing's first word (its brand), so it's the same business, not just the same building.
- `single_place`: true = Google showed exactly one place; false = a list of several, so hours or phone may belong to a neighbor.
- `business_details`: false = Google only knows the address as a map point (no name, phone, hours or website there).
- **`usable`**: true only when the three above (`address_match`, `brand_in_name`, `single_place`) are all true. **This is the only flag that lets you use Google's hours, phone or website.** `why_not_usable` says why not, in plain words.

The rest: `status` (found / not_found / blocked / error), `names`, `addresses`, `phones`, `hours` (one entry per day, e.g. `{"monday": "7AM-7PM", …, "sunday": "Closed"}`), `hours_compact` (the same in one line: `Mon-Sat 7AM-7PM, Sun 8AM-6PM`, `Daily 7:30AM-8PM` or `Open 24 hours`), `categories`, `websites`, `place_id`, `lat`/`lng`, `description` (the business's own Google description), `review_snippets`, `closed_permanently`, `closed_temporarily`, `attempts`.

How to use it (Tier 2):
1. **Read `usable` (and `why_not_usable`), never `status`.** `usable` is true only when `address_match` AND `brand_in_name` AND `single_place` are all true. `status: found` can be a different business or a bare address: it is never a reason to trust anything.
   - **Hours, phone and website from Google count only when `usable` is true.** Otherwise don't use them; look for the business's own page instead, and note `why_not_usable` in the log.
   - A different city name is fine; a different street number, street or ZIP is not (that's `address_match` false).
   - **`business_details` false on every attempt = no business found at that address** (the address may be wrong or the place may not exist). Log `needs_review` with "address not found" for the owner. Never mark it closed and never delete it from this alone.
   - **The name matches somewhere else, but nothing is at our address** (e.g. only a word of the name matched another place, or the brand exists elsewhere): also `needs_review` with "address not found". Never move the listing to the other address.
   - **Google's `websites` value** is used only when `usable` is true AND the domain contains the brand word (e.g. `sunrisecarwash.com` for Sunrise Car Wash). Otherwise ignore it: page text often contains other companies' domains.
2. **Type from the name:** a type keyword in `names` is a signal. A generic organization name ("<Brand> of <Region>", "<Brand> Headquarters") is **neutral**: one address can hold a headquarters, a regular location and the special one. Only a name that clearly says the regular kind counts against, and even then look for Tier 1 first.
3. `blocked`: stop using the script this run, say so, fall back to official pages.
4. Save the Google name and phone in the log `sources`.
5. **place_id lock:** the first time `address_match` AND `brand_in_name` are both true, save `place_id` in the place ids file (or `listing_place_ids` when `log_storage: table`), never on the listing, so "last updated" doesn't move. Later, a different `place_id` = a different place: log `needs_review`.
6. **Closed only when several facets agree:** `not_found` from every wording, AND the official locator no longer lists it (or Google shows "Permanently closed"), AND no recent activity (photos, own posts).

**Optional paid upgrade:** if `listing_check.google_places_key_env` is set, use the official Google Places API instead (Text Search, then Place Details). Never require it.

## check

Step 2 in full.

**Pass 1: Is it still there?**
- Run `gmaps_lookup.py`.
- **Search like a person** when anything is unclear: web search `<name> <full street address>` and read the whole results page (own social pages, news, dated reviews). Then `<name> <city>`. Never call something closed or unconfirmed from one tool.
- **No website?** Its own Facebook/Instagram is the main source: a post in the last 60 days = open; "content isn't available" or nothing for 90+ days = a closure signal (Google must agree).
- Conflicting signals: check one more source (official locator, recent news, own social page).

**Pass 2: Is it still the right kind of business?** Apply the site's definition from the notes. Some addresses host both a regular business and the special one, so evidence must point at the special one.

Type evidence, strongest first:
1. **Official page** naming it with a word from `type_keywords`.
2. **Google name or description** at the exact address (a type keyword in `names`, or `description` saying what it is). Google's category alone proves nothing.
3. **Photos** from `image_check.py`, counted ONLY if the photo's source page is about this exact business. Describe each in one line.
4. **Reviews** mentioning the type keywords (built-in web search: `"<street address>" <city> <type keyword>`, `"<Google name>" <city> reviews`).
5. **Local news** about this exact location (`"<brand> <type keyword>" "<street name>" <city>`).
6. **Regional naming:** some organizations have their own word for the special kind. Read the regional organization's own locations page once per region; if it defines its word, that word is a type keyword for the region. Save it in the notes.

If a script gets a 403 on an official site, read the page with your own web tools.

**Log wording:** write "type confirmed" only when 2 signals agree (one official). One signal = "type consistent". No signal = "type not checked".

**Existing listings are presumed correct.** The owner curated them.
- **Confirmed:** 2 signals agree. Most stop at #1 or #2.
- **OK, no evidence against:** address matches, nothing contradicts, fewer than 2 signals. A pass: log `unchanged`, note "type not re-confirmed".
- **type_mismatch / needs_review** ONLY with actual evidence against (official page lists it as the regular kind only, recent reviews say the special side closed, Google "Permanently closed"). Show the evidence. Never change the type yourself.
- Never mark closed, change the type, or remove a listing just because it couldn't be confirmed.

Photo check:
```
python3 <this skill's folder>/image_check.py "<name> <full street address>" --skip <site's own domain>,<untrusted domains> --max 4 --out <repo>/notes/<slug>/listing-check/photos/<listing id>
```
Always skip the site's own domain (our pages are our data, not proof). **Run the photo check only when adding a listing or when its type is in question.** Field-only checks (hours, phone, website, coordinates) skip it; don't log anything about skipping it.

**Pass 3: Are the details current?**

Evidence needed per field (no exceptions):

| Field | Enough to change it |
|---|---|
| Hours, phone, website | The one evidence rule: own location page, OR Google with `usable: true` (own page wins if they disagree) |
| Website (chains) | Prefer this location's own page (e.g. `brand.com/locations/<city>`). The chain's main domain is acceptable only if no location page exists. Say which one in the proposal ("location page" or "chain homepage, no location page found"). |
| Coordinates | Google `lat`/`lng` with `address_match` true |
| Name, address, city (identity) | Never automatic: propose only, with a Tier 1 source showing the exact street address |
| Type ("right kind of business") | The one evidence rule: 2 signals that agree, one official (Pass 2) |
| Closed | The multi-facet rule above (several facets agree), never one tool |

- Compare each field in `listing_check.fields` with the best source (own website or official page, then Google, then own social).
- **Host business rule:** when the listing is a service inside or beside another business (a car wash at a gas station, a counter inside a store) and the Google place is the host business (its name is the host's, not the listing's, e.g. "Shell", "H-E-B"), the hours and phone Google shows belong to the host. Take the listing's own hours and phone only from its own page or the host's page section about this service. Otherwise leave the field as is and log "host hours, not used". This also applies when the listing itself is named after the host brand (a listing called "Shell" or "Chevron" that is in the directory for its car wash): it's still a valid listing, but its hours and phone come only from its own service page; if there is none, leave them blank.
- **If the business's own page doesn't load** (blocked, empty, error): try the Internet Archive's newest copy (`https://web.archive.org/web/2/<url>`) and note its date; if that fails too, use Google only if `usable` is true, or leave the field and log it.
- Prices, schedules, special days or any other price or schedule fields the site tracks: only from the business's own website or the text of its own recent posts. Only in images: leave as is.
- Social links: open them. Dead page: replace with the current official one if found, else keep and log it.
- Missing coordinates: fill from `lat`/`lng` when `address_match` is true (coordinates are in `fields` by default when the table has latitude/longitude columns).

## chain-sweep

After Step 2, look at the batch: if **3 or more listings that share one website domain** (a chain, e.g. every `brand.example/locations/...` page) have the same kind of change (e.g. Mondays now open at 11, Saturdays now close at 3), the chain probably changed hours everywhere. Don't wait weeks for the batches to reach the rest:

1. Export every active listing of that chain with its id and website (`db.py select --all --columns <id>,<website>,<hours column> --where "<website column>=ilike.*<domain>*"`), one `<id><TAB><url>` per line to `notes/<slug>/tmp/chain-<domain>.txt`. Use each listing's own location page; skip rows that only link to the chain's homepage (list them for the owner).
2. Tell the owner first, in one line, with the cost: "<Brand> changed hours at 9 of 15 locations I checked. Want me to check all <N> <Brand> locations now? It reads their own pages, no AI reading, about <N × 2 ÷ 60> minutes." Run on yes (scheduled runs with `autonomous: true`: run it, max 300 per run).
3. Run `python3 <this skill's folder>/chain_hours.py notes/<slug>/tmp/chain-<domain>.txt --out notes/<slug>/listing-check/chain-<domain>.jsonl` (polite: one page at a time, 1.5 seconds apart, at most 300 per run; it prints how many were ok, had no hours, failed or were blocked). Blocked pages: read up to 20 with your built-in web reader, list the rest.
4. For each `ok` row, render the hours with `hours_style.py render` (Step 3) and compare with the live row using the same 30-minute rule. Same address check: skip any row whose page `final_url` redirected to a different location.
5. Propose **one bulk fix list** in pending.md (one block per listing, as always) and group the blocks under one heading `## <Brand> sweep (<n> listings): ids <first>-<last>` (the ids are consecutive; review-changes approves every waiting block in that range when the owner says "approve <Brand> sweep"). The owner approves the whole sweep with ONE reply: "approve <Brand> sweep" (review-changes applies every block in that group; the owner can still exclude ids: "approve <Brand> sweep except 12, 40"). In chat show only: the pattern ("<n> of <N> <Brand> locations now open Sat and Sun 7 AM to 3 PM"), 3 example rows (old → new, source link, quoted text), and the approval line. Every row with its link and quote stays in pending.md. Never write without approval, even for a chain sweep, unless `auto_apply` covers hours.
6. Test the sweep's stored website links in the same pass (section "links"): use each row's `final_url` as the clean location link when the stored one is broken.

Each sweep row counts as evidence from the business's own page (the one evidence rule). Say in the summary how many of the chain's locations were checked, changed, unchanged, and couldn't be read.

## links

Every listing you check (and every row of a chain sweep) gets its stored website link tested, because a dead or wrong link sends visitors nowhere:

```
python3 <this skill's folder>/link_check.py notes/<slug>/tmp/links.txt --out notes/<slug>/listing-check/links.jsonl
```

`links.txt` is one `<id><TAB><stored website>` per line (for one link: `--url "<link>"`). It follows redirects, waits 1 second between links, and checks at most 300 per run. When 2 or more links share a domain (a chain) it treats them as chain locations, so a homepage link is wrong.

| status | Meaning | What to propose |
|---|---|---|
| `ok` | Opens this location's page | Nothing |
| `tracking_tags` | Works, but has tracking text (`?utm_source=...`) | The `suggest` link, marked "cosmetic" (one bulk line, never one approval each) |
| `glued_tracking` | Tracking text glued onto the address without "?" (".../springfield-northutm_source..."): usually broken or lands on a list page | The `suggest` link (already tested) |
| `broken` | 404, error, or a "page not found" page | The location page you found during the check |
| `homepage` | A chain listing that opens the brand's homepage | The location page you found during the check |
| `index_page` | Lands on a list above the location (e.g. `/locations/florida`) | The location page you found during the check |
| `blocked_by_security` | The site turns away simple scanners | Open it with your built-in web reader (max 20 per run); otherwise leave it and list it |

**The location page you found during the check** = the chain sweep's `final_url` for that listing, the business's own location page you read in Step 2, or Google's `websites` value when `usable` is true and the domain has the brand word. **Test it with `link_check.py --url` before proposing it** (status must be `ok`). If nothing is found, log `needs_review` with "website link is broken, no location page found". Never propose a homepage, a list page, or a link you didn't test.

Website fixes are proposals in the same block as the listing's other changes (field `website`, old → new, source: "tested: opens the <city> location page"). Count them in the summary as "<n> broken website links (fix waiting for approval)".

**Whole-site link check (Step 2d).** Checking only this run's batch hides the real size of the problem: on one tested directory, a 15-listing batch showed 1 broken link while the whole table had 47 links with tracking text glued into the address (most 404 or land on a state list page). So the first run and every 30 days test every listing's link. Bulk fixes live under one `## Website link fix` heading so review-changes applies them with "approve link fix". `blocked_by_security` results (often a whole chain behind Cloudflare) are listed as one line ("<n> links on <domain> couldn't be tested from here"), never proposed as broken.

## decide

| Situation | Action |
|---|---|
| Nothing changed | Don't touch the listing (its date stays honest). Log `unchanged`. |
| Detail changed, confirmed | Update only the changed fields. Log `updated` with old → new and source links. |
| Permanently closed, confirmed (multi-facet rule) | **Never delete.** Set the closed flag and text in the site's format from the notes. Log `marked_closed`. |
| Temporarily closed | Set the temporary flag if the site has one, with a short note. |
| Coming soon has opened | See Step 1. Log `opened`. |
| Sources disagree, or a big change (moved city, name change) | Don't write. Log `needs_review` with the evidence. |
| Can't find it at all | Don't write. Log `not_found`. Two in a row = list for the owner as possibly closed. |
| Google returns a different business of the same brand at another address (e.g. the chain's other location) | Don't write. Log `wrong_place` for the owner: "Google shows <brand> at <other address>, not at ours. Is our address right?" Never change it yourself. |
| Change proposed but not written (first run, or `auto_apply` off) | Write the block to pending.md. Log `proposed` with old → new. |
| No business at the address (`business_details` false on every attempt), or the name only matches a place somewhere else | Don't write. Log `needs_review`: "address not found". Never closed or deleted from this alone. |
| Street alias mismatch (Google uses another name for the same road, e.g. a named street vs a numbered highway) | Don't write. Log `needs_review` with both addresses shown: "Google lists this at <Google address>; we have <our address>. Same place?" Never change it yourself. |
| Two listings share one phone number | Don't write either. Log `needs_review` for both, showing the shared phone. |

Odd values that show badly (e.g. "true" where most rows say "Cash and Card"): use the majority format when the meaning is the same; clear it when the meaning is unknown, never guess.

**Search like a person before any `not_found`, `wrong_place` or `needs_review`:** run one web search of `<listing name> <full address line>` and read the results page (the business's own site, chain location pages, recent reviews). Only if that also comes up empty or contradicts, log the result. Note the search in the log.

**Every proposal shows its evidence, for each source you name.** For each source: the link and the exact value it shows ("sunrisewash.example/locations/springfield: Monday Closed"; "Google: Monday Closed"). If you only have one source, name only that one. Never write "Chain page + Google" (or any two sources) unless both are shown with their values. Proposals without a link and quoted value don't go to the owner.

**Before every proposal or write, read the live row** (`db.py select --where "id=eq.<id>" --limit 1`) and use its CURRENT values as `old`. Never propose a value equal to the current one, and never claim a field is empty when it isn't.

**Formats: copy what the column already uses** (for hours, use `hours_style.py` below instead). Before the first write to a field in a run, read that column for all rows (`db.py select --columns <field> --all`), find the 3 most common formats, and write new values in the most common one (e.g. `Mo-Sa 08:00-18:00; Su 09:00-17:00`, or `9AM-6PM`, or per-day columns). Show the 3 examples in your proposal so the owner sees the format. If the notes define a format, the notes win.

**Hours, the one rule (a script decides the style, never you):** once per run, before the first hours proposal, save the hours column's current values and detect its style:
```
python3 /data/skills/directory-ops/directory-db/db.py select ... --table <listings table> --columns <hours column> --all > notes/<slug>/tmp/hours.json
python3 /data/skills/directory-ops/listing-check/hours_style.py detect notes/<slug>/tmp/hours.json
```
(create `notes/<slug>/tmp/` first). It prints `style` and `h24_word`. For each listing, turn Google's `hours` dict into that style:
```
python3 /data/skills/directory-ops/listing-check/hours_style.py render --style <style> --h24 "<h24_word>" --hours '<the hours dict from gmaps_lookup>'
```
The proposal uses that exact `value`, character for character. Then:
- **Current value empty** → propose the rendered value.
- **Current value differs** by 30 minutes or more on any day (opening or closing), or open vs closed on any day → propose the rendered value. (4:30PM vs 5PM is 30 min = different; 8:45 vs 9:00 isn't.)
- **Otherwise** (same times, or only the format differs) → `unchanged`. Never rewrite hours just to change the format.
Separate per-day columns: write each day as Google gives it, in the format that column's existing rows use (look at 3 filled rows).

## site-check

Wrong hours in the database are bad; wrong hours that the site **publishes to Google** are worse (Google shows them in search and maps). Once per run, open one live listing page you just checked (the URL from the config's `url` plus that listing's page path; find one in the sitemap if needed) and look at what it publishes:
- the structured data (`openingHours` / `openingHoursSpecification` in the page source; `chain_hours.py --url <listing page>` reads it),
- any "open now" / "closed now" text and the time zone it's based on (a `timezone` value in the page),
- the visible hours.

Compare with the database row and with the business's own page, then report **only what really reaches visitors or Google**:

| What you found | How serious | What to say |
|---|---|---|
| The page's structured data (`openingHours` / `openingHoursSpecification`) shows hours the business's own page contradicts | **Real: Google shows wrong hours** | First line of the summary: "Google sees the wrong hours on your pages: <listing> tells Google <published>, but <business> says <real>." Approved hour fixes correct it. |
| "Open now" / "closed now" text that is wrong right now (compute it from the page's hours and the listing's real local time) | **Real: visitors see a wrong status** | Say it in the summary with the page and the wrong status. |
| Visible hours on the page differ from the database | Real (the page isn't showing the latest data, e.g. a cache) | Say so; suggest the site's rebuild or refresh. |
| A wrong time zone label (e.g. an Eastern time zone name on a Texas listing) shown next to correct local hours, with no "open now" logic using it | **Cosmetic** | One line under "Small fixes": "Your pages print the wrong time zone name on <n> listings. The hours themselves are right; it's a label fix." Never call it "wrong hours" or "times are off". |

Check before you claim: open the page source and confirm the time zone is actually USED (an "open now" calculation, or a time zone inside the structured data) before saying it changes any time. If it's only printed as a label, it's cosmetic.

If it's a site-wide setting (the same issue on most rows), say so once with the count, and give the owner a paste-ready one-line instruction for their developer or Claude Code. Never change site code yourself.

## missing

Once per run, across ALL active listings (not just the batch), count what's missing, using `db.py select --all` with only the needed columns:

- For each field in the config's `key_fields` (if missing: `listing_check.fields` plus description and photo, if the table has them): how many rows are empty, null or a placeholder ("N/A", "TBD", "none", "-"). Count "0" as a placeholder only in price, phone and rating fields.
- Thin descriptions (under 40 words) and likely duplicates: **only** the same street address, or the same phone number, on two different listings. Same name + city at different addresses is a chain, not a duplicate (never flag it).
- **Count carefully:** use case-insensitive matches for words in names or fields ("Coming Soon", "coming soon"), count each listing once even if it matches twice, and count the same way every run. Before you report a number, recount it with a second query (e.g. `count` vs `select --all` + count) and report it only if they agree; say what you counted ("13 listings with 'coming soon' in the name").
- Append ONE log line `{"result": "missing_summary", "date": ..., "counts": {field: empty_count, ...}, "duplicates": n}` so the next run can compare. Compare with the previous `missing_summary` line. Put this in the summary as 3 lines: the top gaps (field, % missing), duplicates, change since last run. Never write anything for this part.

## report

If `listing_check.autonomous` is true: apply everything in `auto_apply_fields` that meets the evidence rules, never anything in `never_auto`.

**Every run, attended or not:** write the full report to `notes/<slug>/listing-check/YYYY-MM-DD.md` (all sections below). Then make the **last message of the run** the short summary in SKILL.md Step 5: it's what the scheduler delivers to the owner, so `report: chat` means that message. Step 3b's real problem (wrong hours Google sees, wrong "open now") goes on its first line; a chain sweep adds its approval line ("<Brand>: checked <N> locations, <n> have new hours, say 'approve <Brand> sweep'").

**The owner's message is capped at about 600 words and at most 3 decisions.** Lead with the biggest real problem, then the counts, then up to 3 decisions with your recommended answer each ("Reply 'approve Sunrise sweep' (recommended)"). Everything else (every row, every quote, cosmetic fixes, the missing-details table, blocked sites) goes in the report file and pending.md; end with "Say 'show the full listing report' for every detail". Defaults the owner didn't choose are applied silently and listed in the report, not asked.

Keep the summary in plain words: no file names, field names or codes (say "phone number", not `phone`; "address not found", not `wrong_place`).

The full report has:

- Checked: N (by type). Searches and pages read. Credits used: see Hermes usage (never estimate a number).
- What your site shows Google (Step 3b): the page checked, published vs real hours, real impact vs cosmetic.
- Website links (section "links"): counts by status, each fix with the tested link.
- Chain sweeps: brand, locations checked / changed / unchanged / unreadable.
- Updated: listing, field, old → new, source link + quoted value.
- Closed / temporarily closed / opened: with the source link.
- Needs your review: evidence + a one line question (including "address not found" listings).
- Missing details: top gaps and duplicates (Step 4).
- Next run starts with: the next oldest listings.

Commit and push `notes/` if you changed it (CATALOG.md rule 6). If the repo has no remote (not linked to GitHub), skip the push and say so in one line.

## cost

- Stop a listing once it's clearly unchanged: one search showing open with matching hours is enough.
- Example: 160 listings, batch 40, weekly = each listing about once a month. Always compute this from the real count and batch size before telling the owner a cycle; 1,200 listings at 20 a week is a 60-week cycle, so say so and offer a bigger batch or chain sweeps.
- Credits: don't estimate them; point the owner to their Hermes usage page. If runs feel expensive, offer "I can check fewer listings each week" (lower `batch_size`).
