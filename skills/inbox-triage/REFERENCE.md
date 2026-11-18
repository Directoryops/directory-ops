# Inbox Triage: reference

The full detail behind `SKILL.md`. SKILL.md is the lean core you follow every run; open the section it points to when you reach that step. Sections keep their original headings, so "REFERENCE.md § 3A" means the `### 3A` heading below. Nothing here overrides SKILL.md's hard rules.

Goal: the useful 5% of a site's inbox becomes accurate listings without the owner reading the other 95%.

Read `sites/<slug>.yaml` (sections `inbox` and `inbox_triage`) and `notes/<slug>.md` (sections "Listing rules", "Adding a new store / listing", "Inbox") before every run. Also follow the evidence rules in the **listing-check** skill: this skill never lowers that bar. If `notes/<slug>.md` doesn't exist, create it from the template below and continue. If the config has no `inbox` / `inbox_triage` section, run Step 0 (never copy `sites/example.yaml` wholesale). Files this job writes go under `$DIROPS_REPO/notes/<slug>/`, never `/tmp`.

**Notes template** (when `notes/<slug>.md` is missing):

```markdown
# <site name> (<url>)

## Listing rules
- Valid listing: <the owner's own words for a valid listing, from Step 0 or listing-check settings>

## Adding a listing
- Required fields: <the listings table columns that most existing rows have filled, from `db.py select --limit 20`>
- Format: copy the style of the 3 newest rows (casing, phone format, state as name or code). "Newest" = highest `id` (or latest `created_at` if the table has it).
- Coming soon listings don't need hours or any field that only exists once a place is open.

## Inbox
- Address: <inbox.address>
```

Show the owner the "Required fields" line once ("When I add a listing I'll fill these: ... Right?") and save their answer.

## What you can and can't do (tell the owner once)

- You CAN read the inbox (read only), research what emails say, add and update listings, and add an exterior photo.
- You NEVER reply, forward, delete, label or mark anything as read. The inbox looks untouched.
- You CAN'T open attachments or read text inside images. If an email's key info is only in an attachment, log it as `for_owner`.
- You CAN'T read the Spam folder (Gmail already filters the worst of it).
- An email is a **hint, never evidence.** "My store is at X" or "this closed" must be confirmed with the listing-check source tiers before anything changes.

Say it to the owner in plain words, e.g. "I'll read your site's inbox once a week without touching anything: no replies, nothing marked as read. Spam gets ignored. When someone suggests a new business or reports a closure, I check it on Google and the business's own site before suggesting any change."

## Step 0: Settings (first run only)

If `inbox_triage.settings_done` is not `true`, ask one question per message, each with its default shown (the owner can reply "use the defaults for the rest" at any point). Skip anything the config already answers. Save to `inbox` / `inbox_triage`, set `settings_done: true`, never ask again.

**In quick mode (during onboarding), ask only the questions marked `[essential]` that onboarding hasn't already answered, and use the defaults (or what onboarding inferred) for the rest. List the defaults you used in the plan message; the owner changes any of them by saying so.**

```
Questions, one per message (say "use the defaults" anytime to skip the rest):
1. [essential] Which email address do people use to contact your site? Open that inbox, click your profile picture and copy the address exactly. (no default: I need this one)
2. When someone asks to add a business and I can verify it, should I add it myself or show you first? (default: show you first)
3. How many emails should I fully research per run? The rest wait for the next run. (default: 15)
4. New listings: add a photo? (default: a photo from the business's own website or social page, else a street photo of the storefront, else none)
5. Does your site list places that open later ("coming soon")? (default: yes for business directories, no for job boards and lead gen sites)
6. [essential] Have you added your mailbox's app password yet? (yes / not yet; I'll walk you through it if not)
```

**"Not yet"** = this run is read-only planning: say so ("I can't open the mailbox until the app password is added, so this run only plans; nothing is read or changed"), give the owner the one-time password steps below, and stop.

Map to config: `inbox.address`, `inbox.imap_host` (Gmail: `imap.gmail.com`), `inbox.password_env` (suggested `<SLUG>_MAIL_PASSWORD`), `inbox_triage.auto_add` (default false), `inbox_triage.max_actions_per_run`, `inbox_triage.photo_preference`, `inbox_triage.coming_soon` (true/false), `inbox_triage.allowed_tables` (default: the listings table).

`photo_preference` is a list, tried in order: `own_site_or_social` (a photo from the business's own website or social page), `streetview_storefront` (a street photo showing the entrance or sign), `streetview_any` (the clearest street photo), `none`. Default `[own_site_or_social, streetview_storefront, streetview_any]`; "no photos" = `[none]`. A site may set this per table, and per-table photo settings under `inbox_triage.tables.<table>` (`photo_field`, `photo_folder`); the site's own names for the steps (e.g. `inside_products`, `storefront_sign`) mean the same order: inside/products from their own pages, then a storefront showing the sign, then any street photo.

**Type keyword** (used in lookups below): the first of `listing_check.types[].type_keywords` for that table; if missing, the owner's own words for the listing type from Step 0 / the notes' "Valid listing" line (e.g. "car wash"). Never guess one; if neither exists, leave the type word out of the lookup.

**Job boards and lead gen inboxes** (`coming_soon: false`): skip Step 3C's "coming soon" listings. Alerts about new openings become `for_owner` one liners instead.

One time setup (only if missing):

1. **Mailbox access.** The inbox needs an app password, saved as a setting in Hostinger whose name is in `inbox.password_env` (suggested `<SLUG>_MAIL_PASSWORD`; if the owner already used another name, write that name into the config). Walk the owner through `/data/skills/directory-ops/setup-guides/guides/gmail-app-password.md` (other providers: `/data/skills/directory-ops/setup-guides/guides/other-mailbox-password.md`), then `/data/skills/directory-ops/setup-guides/guides/add-a-setting-in-hostinger.md` with the exact setting name. Never ask them to paste it in chat.
2. **Log (no setup needed).** By default (`inbox_triage.log_storage: file`) every handled email is one JSON line in `notes/<slug>/inbox-triage/log.jsonl` with `message_id`, `received_at` (= the `date` field from read_inbox.py), `sender`, `subject`, `category`, `action`, `listing_table`, `listing_id`, `notes`, `handled_at`. Create the folder and file on the first run. Only if the config says `log_storage: table`, use the `inbox_triage_log` table instead (through `directory-db/db.py`). Never ask a beginner to run SQL.
3. **Photo bucket** (only if the site wants photos on new listings): tell the owner "I need a place in Supabase to keep listing photos:" then walk them through `/data/skills/directory-ops/setup-guides/guides/supabase-photo-storage.md` (folder name `listing-photos`). If the site's images are configured to load only from certain hosts, the site must allow `<project>.supabase.co/storage/v1/object/public/**` (tell the owner it's a one line change for their developer or AI coding tool, and give them that line to paste).

**If login fails, diagnose it yourself before asking the owner anything** (never send them on guesses):
0. **Is the address exactly right?** "Invalid credentials" most often means the login address is wrong (e.g. a missing word, like `mysite@` vs `themysite@`), not the password. Ask the owner to open Gmail, click their profile picture, and read the address back.
1. Is the env var set, and is it 16 letters after removing spaces? (Never print it.)
2. Is the same name also defined in a saved file that overrides the hPanel value (`/data/.env`, `~/.hermes/.env`, `/data/.hermes/.env`, `/data/config.yaml`, other `*.env` under `/data`, your memory)? If yes, remove that line and tell the owner to restart once.
3. Does another site's mailbox on the same server log in? If yes, the server isn't blocked; the problem is this account.
4. Only then give the owner ONE fix: "check Gmail for a security alert and click Yes it was me" or "create a new app password while signed in as <address> and replace the setting named <ENV NAME> (same steps as `/data/skills/directory-ops/setup-guides/guides/add-a-setting-in-hostinger.md`: edit it, paste, 'Save & redeploy', then a new chat)".

**Set up once, then hands off.** After setup, test the connection once with `--since-days 1`. If the owner said the app password isn't added yet, skip this test and write one line: "Mailbox test skipped: app password not added yet." If a scheduled run ever fails to log in, don't retry in a loop: write one line in the report ("Mailbox login failed: <reason>, fix: <one step>"), skip the run, and carry on next time.

### Teach me your way (one optional question, right after this helper is accepted)

This is what makes the helper yours instead of generic. Ask once (in quick mode it replaces settings questions, it doesn't add many):

> Tell me how you handle your site's emails today: which emails matter, how you deal with "add my business" requests, what you ignore, anything I should never do. Ramble or send a voice note; it makes me much better. (Or say "skip".)
> For example:
> - Roofing: "Only add a roofer if they include a license number."
> - Wedding venue: "Venues sending new photos: tell me, don't change anything."
> - Car wash: "Ignore anything selling car wash equipment or soap."

Turn the answer into 3 to 7 short numbered rules in plain words, show them back ("Got it, I'll: 1) … 2) … Anything to change?"; in quick mode end with "Say 'change …' anytime." instead of a question, so onboarding stays short), and save them in `notes/<slug>.md` under `## Handle your inbox rules` (create the section if it's missing). **Every run reads that section first and follows it; this skill's own safety rules still win** (a rule can't make it skip approval, delete things, or use competitors as sources).

**Learn from corrections:** when the owner rejects or edits one of your proposals, or says "no, because …", ask once: "Want me to remember that as a rule for next time? (yes/no)". Yes: add it to `## Handle your inbox rules` in plain words with today's date.

## Step 1: Read new mail (cheap)

```
python3 <this skill's folder>/read_inbox.py --host <inbox.imap_host> --user <inbox.address> --password-env <inbox.password_env> --since-days <days since last run + 1, default 8> --max 150
```

Days since last run: the `last_run` line in the log (every run appends `{"last_run": "<ISO time>"}` at the end). No `last_run` yet → 8.

Skip every `message_id` already in the log (the log file, or `inbox_triage_log` when `log_storage: table`).

## Step 2: Sort every email (use only from, subject and the first lines)

| Category | How to spot it | Action |
|---|---|---|
| `spam` | Sales pitches (SEO, web design, guest posts, link building, "partnership", crypto, loans), cold outreach, mass mailers, phishing | Ignore. Log it. Don't open links. |
| `automated` | Receipts, platform notices, newsletters, security alerts, "no-reply" senders that aren't alerts | Ignore. Log it. |
| `add_listing` | Someone asks to add a place, or says "you're missing X" | Step 3A |
| `closed_report` | "This place closed / moved / is gone" | Step 3B |
| `correction` | Wrong hours, phone, address, prices, link | Step 3B |
| `wrong_type` | "This isn't a real <type>", "this is just a regular store" | Step 3B |
| `alert` | News alert emails (e.g. Google Alerts) about the niche | Step 3C |
| `for_owner` | A real person needing a human answer (partnership the owner might want, press, legal, a business owner upset about their listing) | Don't act. Log with a one line summary. |

When unsure between spam and real: a real request names a specific place, address or listing. Sales pitches talk about the website itself.

## Step 3: Handle the useful ones

### 3A. Add a listing
1. **Duplicate check first:** search every listing table (including closed and coming soon) by street number + street name and by name + city. If it exists, treat the email as a `correction` instead (or nothing, if the data matches).
2. **Is it real, and the right type, at THIS address?** Dig until it's clear, like a person would:
   - Web search `<name> <full street address>` (exact address in the query) and read the whole results page: snippets from guides, the brand's own Instagram/Facebook, news, store lists. A result naming the brand at this exact street address is a strong signal.
   - Web search `<name> <city>` and `<name>` alone to learn what the business is (e.g. "a self-serve wash bay run inside a gas station chain").
   - The free Google lookup (name, description, review snippets) and the business's own site and social.
   - Apply the notes' definition and the listing-check Pass 2 ladder. Needs 2 signals that agree, at least one official (their own site, own social, or the parent brand's official page).
   - Never decide from a single tool or a single photo. A Google profile showing only the host store (e.g. the supermarket) doesn't mean the section inside it isn't there.
   - Not the right type → log `rejected_wrong_type` with the reason.
   - **A chain or brand** (the tip names a brand with several locations): before calling it unconfirmed, web search `<brand> <city> locations` and open the brand's own official location finder or locations page. If it lists a location matching the tip, that's the official signal and gives you the exact address.
   - **Partial address** (a street without a number, "on South Lamar"): search `<name> <street> <city>`. Accept only if exactly one location matches on the official page, or on a Google lookup of that full address whose result has `usable: true`; then use that full address. More than one match or none → `unconfirmed` with what you found.
   - **Official locations page cut off** (it shows only part of the list): open that brand's page for the city or state if one exists (`<brand> <city> location`); if none, log `unconfirmed` with the link.
   - **A program run inside another business** (e.g. a service counter inside a chain store): follow the naming pattern in the site notes if there is one; otherwise use the program's name plus the city. Use the program's official page as the website, the program's or parent brand's official social page, and any schedule or prices the program publishes for all its locations.
3. **Gather the fields** listed in the notes ("Adding a new store / listing"), from Tier 1 to 3 sources only:
   - `python3 /data/skills/directory-ops/listing-check/gmaps_lookup.py --listing "<name>" "<full address>" "<type keyword>"`: address, phone, hours, `lat`/`lng`, `description`, `review_snippets`, `place_id`.
   - Website and official social page: open them; use only live, official ones.
   - **Reviews: Google Maps reviews only, word for word** (`review_snippets`, with their star rating), for the Google profile at this exact address. Honest beats flattering: don't pick only the good ones, don't edit, don't invent authors. If Google has none for this place, leave reviews empty. Never use reviews from another location.
   - Website: the most specific official page for this location or program, never a script/asset file URL (e.g. `index-min.html`, `.js`, `.json`).
4. **Photo** (if the site uses them). Follow the site's `photo_preference` (config). Default order:
   1. **What's inside** (e.g. the products, the space, the service): a photo from the business's OWN website or OWN public social page for this exact location (their page's main image, or `image_check.py` results whose `source_page` is their own site, their own Facebook/Instagram, or their own review page with the same address). Never from news articles, blogs, other directories or another location of the same chain.
   2. **Storefront:** `python3 /data/skills/directory-ops/listing-check/listing_photo.py streetview <lat> <lng> --out $DIROPS_REPO/notes/<slug>/tmp/listing-photos`. Prefer an angle that shows the entrance or the sign.
   3. Last resort: the clearest Street View angle of the building, even if it's not perfect.
   4. Only if Street View has nothing at that spot: no photo.
   Upload the chosen file with `python3 /data/skills/directory-ops/listing-check/listing_photo.py upload <file> --path <inbox_triage.photo_folder>/<slug>.jpg --bucket <inbox_triage.photo_bucket> --site-url <database.url> --key-env <database.key_env>` and save the returned `public_url` in the photo field.
5. **Write it** in the exact format of the 3 newest rows of that table (highest `id`, or latest `created_at` if the table has it; copy their style for every field: casing like `CLOSED` vs `Closed`, state as full name or code, phone format, name pattern). Fill only what you verified; leave the rest empty.
6. Save the `place_id` in listing-check's place ids file (`notes/<slug>/listing-check/place-ids.json`, or `listing_place_ids` when `log_storage: table`) and log the source links.
7. Only insert if `inbox_triage.auto_add` is true. Otherwise write the full proposed row to `notes/<slug>/pending.md`.

**Businesses without a website** (common for small shops that live on Facebook/Instagram): confirm they're real and open with 2 of: Google profile at the exact address with recent reviews, their own social page live with a post in the last 60 days, recent reviews elsewhere. Read the site notes for any stricter rule.

**Vague tips** ("there's one east of <city> on <street>", "some store closed"): worth one quick look, not a big hunt. Search the area once, and for a chain or regional organization, open its official locations page for that region. Compare every location on it with the directory: this often finds the tipped location AND other missing or moved ones. Nothing concrete after that → log `no_match` and move on.

### 3B. Closed report, correction, wrong type
1. Find the listing by street address (never by name alone). If the email gives only a street without a number, match name + street in the listings table; exactly one match = that listing, otherwise `no_match`. Not found → log `no_match`.
2. Re-check it now with the listing-check skill (all passes) on that one listing, treating the email as a hint of where to look.
3. Apply only what listing-check's rules allow. Closures need the multi-facet rule; for social-only businesses that means Google (closed or gone at that address) AND their own page (a closing post, or gone / silent 90+ days). Type and identity changes are never automatic: log them as `for_owner` with the evidence.
4. Not confirmed → log `unconfirmed` with what you checked. Don't change anything. If the listing-check lookup says no business exists at the listing's address, log `needs_review` ("address not found") for the owner: never closed or deleted from that alone. If Google returns a **different business at another address** instead, that's also `needs_review` ("Google shows <other name> at <other address>, nothing at this one").
5. **Future-dated change** ("new hours from December 1"): log `scheduled` with the date and the claimed change. Don't change anything now. On the first run after that date, re-check it like a fresh correction and propose it if confirmed.

### 3C. Alerts (new openings)

Only if `inbox_triage.coming_soon` is true (see Step 0). Otherwise log the alert as `for_owner` with a one line summary.

1. Get the real article link (Google Alerts wraps links as `google.com/url?...&url=<real link>`; use the `url` value). Open at most 3 articles per alert email; skip ones that are obviously off topic from the title.
2. Act only if the article names a **specific new location** of the valid type with at least a city (address if possible). General news, closings of other kinds of stores, opinion pieces → log `no_action`. **Only a city, no business name:** one web search (`new <type> <city>`); if it finds a named business at an address, continue with that; otherwise `no_action`.
3. Not open yet → add a **coming soon** listing in the site's format (from the notes): name, address if known, city, state, coming soon flag and text (e.g. "Coming Soon (Spring 2027)"), no hours (hours and other "once open" fields are never required for coming soon listings, even if the notes list them as required). **No coming soon text column:** set only the flag and put the expected opening date (with its source) in the proposal's `why`. Skip if a coming soon listing for that city and brand already exists.
4. Already open → treat as 3A.
5. The article itself is Tier 4 for details (dates, hours). Confirm the address from an official page or Google before writing it.
6. An article (or its archive copy) that won't load → log `unconfirmed` with the link, for the owner to open. **Exception:** if one web search finds the business anyway, it may be proposed only with 2 sources that agree: a Google lookup with `usable: true` AND the business's own website. Anything less stays `unconfirmed`.

## Step 4: Log and report

- Every email gets one log entry (including spam), so it's never processed twice. `action` is one of: `ignored`, `added`, `updated`, `marked_closed`, `coming_soon_added`, `rejected_wrong_type`, `unconfirmed`, `needs_review` (same meaning as in listing-check: evidence is unclear or contradicts, the owner decides), `scheduled` (a future-dated change, with its date), `no_match`, `no_action`, `for_owner`, `pending`.
- Create `notes/<slug>/pending.md` only when there's at least one proposal. Append `{"last_run": "<ISO time>"}` to the log at the end of every run.
- Summary (to the owner in chat, or only to the report file if `inbox_triage.autonomous` is true), plain words, max 6 lines, starting with what they need to do: changes waiting for their approval, emails that need a human answer (one line each), what was added or changed (with links), how many emails were read and how many were spam.
- Report file: `notes/<slug>/inbox/YYYY-MM-DD.md`. Commit and push `notes/` (CATALOG.md rule 6).

## Allowed writes

The log and place ids (files under `notes/<slug>/`, or the log tables when `log_storage: table`), the listing tables named in `inbox_triage.allowed_tables` (insert new listings; updates only through listing-check rules), the photo bucket, and `notes/<slug>/`.

## Cost control

- Sort by subject and sender first; never research spam.
- Deep work (3A to 3C) on at most `inbox_triage.max_actions_per_run` emails (default 15); the rest wait for next run.
- One gmaps lookup per place; the photo step only for listings you're actually adding.
