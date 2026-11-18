---
name: inbox-triage
description: Reads a directory site's inbox (read only, never replies), ignores spam and sales pitches, and turns useful emails into verified listing work. "Add my store" becomes a new listing, "this place closed" or a correction gets checked and fixed, and alert emails about new openings become "coming soon" listings. Every change follows the listing-check evidence rules. Use when the owner says "check the inbox", "triage emails", or on its schedule.
---

# Inbox Triage

## Playbook card (show this to the owner)

Show this card to the owner before setting the helper up (onboarding plan or "add a helper"), so they see and approve the process.

**What it does:** reads your site's inbox, ignores the junk, and turns real requests (add my business, this place closed, wrong hours) into checked changes.
**Why it works:** most site email is spam, so sorting comes first and research only happens on real requests. Nothing a stranger emails goes live without proof from the business itself or Google.
**How I work:**
1. I read new emails without marking them read, and I never reply.
2. Spam, ads and newsletters are skipped and logged.
3. "Add my business": I find it on Google and its own website, check it's the right kind, and draft the full listing.
4. "This closed" or "wrong info": I verify it with two sources first.
5. News alerts about openings become "coming soon" suggestions.
**You approve:** every new listing and change, until you say adds can go live on their own.
**Cadence:** weekly, which is plenty for contact forms. Empty weeks cost almost nothing.
**What you get:** a sorted inbox summary with ready-to-approve listings and fixes.
**What I need from you:** your site's mailbox and an app password.
**Make it yours:** "add requests are usually mobile groomers", "ignore anything from vendors", "Facebook-only shops count if they posted in the last 60 days".

**Onboarding sample:** the last 2 weeks of email sorted, with the proposed action for each real request.

**If a step fails** (blocked site, thin data, noisy results): try the fallback this skill documents, and still deliver the best honest sample. Never end with less than the onboarding sample without telling the owner, in plain words, what blocked it and the fix.

Goal: the useful 5% of a site's inbox becomes accurate listings without the owner reading the other 95%. Full detail for every step: `REFERENCE.md` (same headings).

## Before every run

1. Read `sites/<slug>.yaml` (`inbox`, `inbox_triage`) and `notes/<slug>.md` ("Listing rules", "Adding a new store / listing", "Inbox", `## Handle your inbox rules`). No notes file: create it from the template in REFERENCE.md and show the owner the "Required fields" line once. No `inbox`/`inbox_triage` section: run Step 0 (never copy `sites/example.yaml` wholesale).
2. Follow the **listing-check** evidence rules; this skill never lowers that bar.
3. Files go under `$DIROPS_REPO/notes/<slug>/`, never `/tmp`.

## Hard rules

1. **Read only.** Never reply, forward, delete, label or mark anything read. No attachments, no text inside images (those → `for_owner`), no Spam folder.
2. **An email is a hint, never evidence.** Every add or change needs the listing-check source tiers: 2 agreeing signals, at least one official (own site, own social, or the parent brand's official page). Never one tool or one photo.
3. **Never research spam;** never open its links.
4. **Closures, type and identity changes are never automatic.** Type/identity → `for_owner` with evidence; "address not found" → `needs_review`, never closed or deleted from that alone.
5. **Reviews: Google Maps reviews only, word for word,** for this exact address; none → empty. Never another location's.
6. **Photos only from the business's own pages or Street View** at its coordinates (order in `photo_preference`); never news, blogs, other directories or another location.
7. Insert only if `auto_add` is true; otherwise the full proposed row goes to `notes/<slug>/pending.md`. Write only to `allowed_tables`.
8. **Never ask for the mailbox password in chat.** On a login failure, diagnose first and give ONE fix (Step 0).
9. Every email gets exactly one log entry, so nothing is processed twice.
Tell the owner once, plainly, what you can and can't do (REFERENCE.md § What you can and can't do).

## Step 0: Settings (first run only)

1. If `settings_done` isn't `true`: ask the 6 questions in REFERENCE.md § Step 0, one per message, defaults shown (quick mode: only the `[essential]` ones: the exact inbox address, read from the account itself, and whether the app password is added). Map to `inbox.address`, `inbox.imap_host` (Gmail `imap.gmail.com`), `inbox.password_env` (suggest `<SLUG>_MAIL_PASSWORD`), `auto_add` (false), `max_actions_per_run` (15), `photo_preference`, `coming_soon` (true for business directories, false for job boards and lead gen), `allowed_tables` (the listings table). Set `settings_done: true`.
2. **Password not added yet:** this run only plans. Say so, walk them through `/data/skills/directory-ops/setup-guides/guides/gmail-app-password.md` (other providers: `other-mailbox-password.md`), then `add-a-setting-in-hostinger.md` with the exact setting name, and stop.
3. **Log:** default `log_storage: file` → one JSON line per email in `notes/<slug>/inbox-triage/log.jsonl` (fields in REFERENCE.md § Step 0). `table` → `inbox_triage_log` via `directory-db/db.py`. Never ask a beginner to run SQL.
4. **Photo bucket** (only if the site wants photos): `/data/skills/directory-ops/setup-guides/guides/supabase-photo-storage.md`.
5. **Test once** with `--since-days 1` (skip if the password isn't added: write one line saying so).
6. **Login fails:** check, in order, before asking the owner anything: the address is exactly right (most "invalid credentials" are a wrong address) · the env var exists and is 16 letters without spaces (never print it) · no saved file overrides it · another mailbox on the server logs in. Then ONE fix. Scheduled run fails to log in: one report line, skip, no retry loop. Details: REFERENCE.md § Step 0.
7. **Teach me your way** (one optional question; wording in REFERENCE.md § Teach me your way): 3 to 7 rules under `## Handle your inbox rules`. **Learn from corrections:** ask once "Want me to remember that as a rule for next time? (yes/no)".

**Type keyword** for lookups: the first `listing_check.types[].type_keywords` entry, else the owner's own word for the listing type; never guessed.

## Step 1: Read new mail

```
python3 /data/skills/directory-ops/inbox-triage/read_inbox.py --host <inbox.imap_host> --user <inbox.address> --password-env <inbox.password_env> --since-days <days since last_run + 1, default 8> --max 150
```
Skip every `message_id` already in the log.

## Step 2: Sort (from, subject, first lines only)

`spam` (sales pitches, outreach, phishing) and `automated` (receipts, notices, newsletters) → ignore, log · `add_listing` → 3A · `closed_report`, `correction`, `wrong_type` → 3B · `alert` (news alerts) → 3C · `for_owner` (a real person needing a human answer) → log a one line summary, don't act. A real request names a specific place; a pitch talks about the website. Table: REFERENCE.md § Step 2.

## Step 3: Handle the useful ones (at most `max_actions_per_run`)

**3A. Add a listing**
1. Duplicate check across every listing table (street number + name, and name + city). Exists → treat as a correction.
2. Real, right type, at THIS address: web search `<name> <full street address>` and read the results page like a person; `<name> <city>`; then
   `python3 /data/skills/directory-ops/listing-check/gmaps_lookup.py --listing "<name>" "<full address>" "<type keyword>"`
   plus the own site and social. Chains: the brand's official locations page. Partial addresses, cut-off location pages, programs inside another business, social-only businesses, vague tips: REFERENCE.md § 3A. Wrong type → `rejected_wrong_type`.
3. Fields from Tier 1 to 3 sources only (address, phone, hours, lat/lng, description, reviews, most specific official website).
4. Photo per `photo_preference`: own pages first, then
   `python3 /data/skills/directory-ops/listing-check/listing_photo.py streetview <lat> <lng> --out $DIROPS_REPO/notes/<slug>/tmp/listing-photos`
   (angle showing the entrance or sign), upload with
   `python3 /data/skills/directory-ops/listing-check/listing_photo.py upload <file> --path <photo_folder>/<slug>.jpg --bucket <photo_bucket> --site-url <database.url> --key-env <database.key_env>` and save `public_url`.
5. Copy the exact format of the 3 newest rows, field by field; fill only what you verified.
6. Save `place_id` (`notes/<slug>/listing-check/place-ids.json`, or `listing_place_ids` with `log_storage: table`); log sources. Insert only if `auto_add`, else pending.md.

**3B. Closed report, correction, wrong type:** find the listing by street address (never name alone; street without number: name + street, exactly one match). Re-check that one listing with listing-check (all passes). Apply only what its rules allow (closures need the multi-facet rule). Not confirmed → `unconfirmed`; no business at the address → `needs_review`; future-dated change → `scheduled` with its date, re-check after. REFERENCE.md § 3B.

**3C. Alerts** (only if `coming_soon` is true; else `for_owner`): real article link (unwrap Google Alerts `url=`), at most 3 articles per email. Only a **specific new location** of the valid type counts. Not open yet → a **coming soon** listing in the site's format (no hours needed); already open → 3A. Article details are Tier 4: confirm the address officially. Won't load → `unconfirmed`. REFERENCE.md § 3C.

## Step 4: Log and report

- One log entry per email. `action` ∈ `ignored`, `added`, `updated`, `marked_closed`, `coming_soon_added`, `rejected_wrong_type`, `unconfirmed`, `needs_review`, `scheduled`, `no_match`, `no_action`, `for_owner`, `pending`. Append `{"last_run": "<ISO time>"}` at the end of every run. Create pending.md only when there's a proposal.
- **Summary** (chat, or only the report file if `autonomous`): plain words, max 6 lines, starting with what the owner must do: approvals waiting, emails needing a human answer, what was added or changed (links), emails read / spam. Onboarding sample: about 600 words max, at most 3 decisions with a recommended answer.
- Report file `notes/<slug>/inbox/YYYY-MM-DD.md`. Commit and push `notes/` (CATALOG.md rule 6).

**Allowed writes:** the log and place ids, the tables in `allowed_tables` (inserts; updates only through listing-check rules), the photo bucket, `notes/<slug>/`. **Cost:** sort before researching; one gmaps lookup per place; photos only for listings you're adding.
