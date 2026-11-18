# Lead routing: reference

SKILL.md is the core. This file holds the details it points to by section name (e.g. "REFERENCE.md § Mailbox"). Read a section when SKILL.md sends you here.

## Mailbox

- A normal mailbox for the site (Gmail, the host's email product, Google Workspace, Zoho). Non secret settings live in the config (`sender.from_email`, `smtp_host`, `smtp_port`, `imap_host`). The ONLY env var is the password, named in `sender.password_env` (suggested `<SLUG>_MAIL_PASSWORD`; if the owner already used another name, write that exact name into the config), added by the owner on the Hermes host (never in chat). Use an app password if the provider offers one.
- Then confirm you can see it (yes/no only) and send one test email to the owner (`send_mail.py ... --kind owner`).
- **No password yet:** drafts only mode. Set `auto_send: false`, skip the test email, and tell the owner: "Until your mailbox password is added, I'll write each email as a draft and show it to you instead of sending it." Everything else works. Step 5 (reading replies) is skipped and the summary says "Replies not read: no mailbox password yet".
- Owner steps: Gmail → `/data/skills/directory-ops/setup-guides/guides/gmail-app-password.md`; other providers → `/data/skills/directory-ops/setup-guides/guides/other-mailbox-password.md`; then `/data/skills/directory-ops/setup-guides/guides/add-a-setting-in-hostinger.md` with the exact name from `sender.password_env`.
- Gmail settings: SMTP `smtp.gmail.com` port 587, IMAP `imap.gmail.com`; about 500 emails a day.
- Do not use Resend, SendGrid or other "transactional" senders for first contact with businesses. Their rules forbid cold email and the account can be suspended. Only use them if the config says `sender.method: resend` and the owner accepts that risk.

## Logs

- Routing steps: one JSON line each in `notes/<slug>/lead-routing/log.jsonl` (`log_storage: file`, the default, no setup): `{"at", "lead_id", "listing_id", "to_email", "step", "message_id", "notes"}`. Steps: quality_reject, quality_review, first_email, first_email_draft, draft_reminded, followup, reroute, reply_interested, reply_not_interested, reply_question, auto_reply, opt_out, skipped.
- Sites that already have a `lead_routing_log` table set `log_storage: table` and write the same fields there. Never ask the owner to run SQL.
- `send_mail.py` keeps its own mail log in `notes/<slug>/sent-mail.jsonl` (every send or draft, with `free: true` on free leads). It uses it for the daily cap and the one-free-lead rule.
- **Distributions status words** (when a distributions table is configured): `draft`, `sent`, `replied_yes`, `replied_no`, `bounced`.

## Config details

- **Listing columns** for matching: `tables.listing_lat` (default `latitude`), `tables.listing_lng` (default `longitude`), `tables.active_filter` (e.g. `permanently_closed=eq.false`; default none). Read the real column names from the listings table once and save them.
- **Offer:** `offer.price_per_lead_usd` must be set. `offer.unlock_url_template` is optional: blank means Template B2 (business replies "yes", the owner invoices by hand).
- **What a lead looks like:** read the leads table once and fill `lead_fields`: the columns that describe a request, each with a plain label and whether it's required, e.g. `[{name: service, label: "Looking for", required: true}, {name: preferred_date, label: "Date", required: false}, {name: budget, label: "Budget", required: false}]`. If requests have a date the customer needs the service by (event, move, start date), set `needed_by_field` to that column. Set `phone_country` (default `US`). Show the owner one plain line using the labels, not column names ("Each lead email will show: Looking for, Date, Budget. Is that right?").
- **Email wording** under `lead_routing.wording` (plain questions, one per message, each with its default; "use the defaults for the rest" is fine):
  - `site_name` (default: the config `name`)
  - `niche_plural` (what the directory lists, plural: "car washes", "plasma centers")
  - `request_type` (short noun phrase: "car wash", "detailing"; the subject adds "request", so drop a trailing "request")
  - `owner_first_name` (signs the emails) **[essential, never invented]**
  - `ask_phrase` (default "asked for a quote")
  - `sender.from_name` default: `<owner_first_name> at <site_name>`
  - `sender.physical_address` (required by email law) **[essential, never invented]**
- **Draft status:** Step 0 adds `draft: draft` to the lead status values if the leads table's status is a text column; otherwise drafts use the `review` value.
- **No double emails:** check whether the website already emails businesses about new leads by itself (ask the owner, or look in the site repo). If it does, the owner chooses which one does first contact before this job is enabled. `route_leads_created_after` lets you ignore leads the website already handled.

## Email finder

- **Offer** (inventory under 80%): "Want me to find the rest from their own websites? It costs almost nothing (no AI reading, just a quick look at each site) and takes about <minutes> minutes, in the background. I'll show you 5 first." Measured speed: about 6 seconds per site (100 sites ≈ 10 minutes).
- **Export** listings without an email (`db.py select --all --columns <id>,<name>,<website> --where "<email>=is.null"`, or the anti-join for an email table) to `notes/<slug>/tmp/no-email.json`, then:
  ```
  python3 <skills folder>/lead-routing/find_emails.py notes/<slug>/tmp/no-email.json --out notes/<slug>/lead-routing/found-emails.jsonl --limit 5
  ```
  Show the 5 in plain words ("Sunrise Car Wash: info@sunrisewash.com (from their contact page)"). After the owner's OK, run the rest in batches (`--skip-done --limit 100`, one batch per night by default, in the background; say when it will finish).
- **Save only what the owner approves**, through `directory-db/db.py` (insert into the email table with `is_routable: true` and the next `send_order`, or update the listing's email column), dry run first, `--source` = the page it came from. Then tell the owner the new total ("Now 251 of 300 can receive leads").
- **Never save, and say why:** `shared_email` (one address on several listings is a chain's head office; ask once whether head-office inboxes are OK) and `redirected_to` (their website now goes to another company; ask the owner to confirm). Both go on the questionable list while you ask.
- **Result meanings:** `contact_form_only` (only a form; list them for the owner), `social_only`, `no_website`, `site_failed` / `needs_browser` (couldn't read the site), `blocked_by_security` (open the homepage and contact page with your built-in web reader and look for the email there, same rules; at most 20 per run because each one uses AI credits). One summary line, never a long table unless asked.
- **Rules:** only addresses the business publishes on its own website. Never guess patterns (firstname@domain), never take emails from other directories, review sites or bought lists, never scrape personal social profiles. Every saved email keeps the page it came from. When an email bounces, mark it not routable and re-run the finder for that listing once.
- **Listings with no website** (often the biggest gap): find the website first, free:
  ```
  python3 <skills folder>/listing-check/gmaps_lookup.py --listing "<name>" "<full address line>"
  ```
  Use a website only when `usable` is true and it's the business's own site (not a directory, social page or a chain's head office), add it to `no-email.json` and run `find_emails.py`. During onboarding do this for a sample of 10 (about 2 minutes) and report before and after in one line: "Before: 5 of 44 can receive leads. After the finder: 11 of 44 (6 found: 3 from websites you had, 3 from websites I found on Google)." Offer the rest as a background batch. Propose found websites as listing fixes too (pending.md), never write them silently.
- Owners who use Claude Code can run `find_emails.py` on their own computer with their listings file; the results file comes back the same way.

## Picking the business

- **Distance without a geocoding service:** use the latitude/longitude of the listing the lead came from (or of any listing in the lead's city) and compare with each candidate using the haversine formula: miles = 3959 × 2 × asin(√(sin²(Δlat/2) + cos lat1 × cos lat2 × sin²(Δlng/2))), angles in radians. No coordinates: match the same city, then nearby cities the owner named.
- **Service fit evidence:** the listing's service or feature columns first, then words in its name ("Hand Car Wash", "Mobile Detailing"), then its own website if you already read it this run. Never claim a fit you didn't see.
- **Address sanity check.** Skip an email and try the next one if it:
  - points to another country or region (`aunz`, `uk`, `canada`, `.com.au`, `.co.uk`) when the lead is elsewhere,
  - belongs to a national chain, franchise head office or central call center rather than the local location (unless clearly the local location's address),
  - is a no reply, careers, billing or privacy address,
  - is on the questionable list (can't be found on the business's own site, looks personal or like test data, the owner was asked where it came from).
  No good address left: the business is not emailable.
- **The questionable list:** `notes/<slug>/questionable-emails.txt`, one address per line, `# why`. Add an address whenever you ask the owner about it. When the owner answers: confirmed → remove the line (and save it as routable if it wasn't); wrong → remove the line and mark it not routable.

## Quality check details

Hard fails (reject):
- **Name:** gibberish, keyboard mash, a single letter, "test", or obviously fake.
- **Phone / email / date:** whatever `check_lead.py` rejects.
- **Needed-by date** (if `needed_by_field` is set): in the past or more than 18 months away.
- **Location:** city, address or zip cannot be found.
- **Spam:** links, sales pitches, or text unrelated to the niche.
- **Duplicate:** same email or phone in the last 30 days (merge into the earlier lead instead).

Review (hold, ask the owner): `check_lead.py` says review, most `lead_fields` empty, an unusual request, a business pretending to be a customer, or an empty phone AND a vague request (no service or no date). An empty phone with a clear request is NOT a reason to hold.

Write the reason to the log; set the lead's status to the rejected/review value; if `tables.lead_notes_column` is set, write the reason there too.

## Replies

Keep only replies to lead emails (subject starts with "Re:" and matches a subject you sent, or the sender is a business you emailed). Classify:
- **Interested** ("yes", "send more", asks about price): log `reply_interested`, set the lead to the "responded" value. If `auto_reply_interested` is true, send Template D; otherwise list it at the top of the summary for the owner to close by hand.
- **Question** (anything you're unsure how to answer): log `reply_question`, do NOT reply, list it for the owner.
- **Not interested / stop / unsubscribe:** log `opt_out`, never email that business again (mark the email not routable if the config allows), no reply.

## Teach me your way examples

> - Roofing: "Insurance claim jobs go to roofers with 4.5 stars or more first."
> - Wedding venue: "Under 50 guests goes to the smaller venues, not the big halls."
> - Car wash: "Fleet washing requests only go to mobile detailers."

## Allowed writes

All database reads and writes go through `directory-db/db.py` with `--allowed-tables` set to these. This job may write ONLY to: its log (file, or the `lead_routing_log` table when `log_storage: table`), the configured distributions table, the lead's status column (and notes column if `tables.lead_notes_column` is set), the routable/opt out columns of the business email table, and (only after the owner approves the finder's results) new rows in the business email table or the listing's email column. It never edits listings or anything else.
