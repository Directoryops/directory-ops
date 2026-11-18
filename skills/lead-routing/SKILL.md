---
name: lead-routing
description: Turns new leads on a lead gen directory into money. Checks each lead is real, emails it to the matching business (first lead free), follows up once, reroutes to nearby businesses if there is no response, and auto replies to businesses that want more leads. Use when the owner says "route leads", "run lead routing", or on its schedule.
---

# Lead Routing

## Playbook card (show this to the owner)

Show this card before setting the helper up (onboarding plan or "add a helper"), so the owner sees and approves the process.

**What it does:** sends each real customer request from your site to the right business, first one free, so businesses learn your leads are worth paying for.
**Why it works:** a free, well-matched lead is the best sales pitch. Bad leads and wrong recipients kill trust, so quality and the customer's consent come first.
**How I work:**
1. I check each new request is real: email, phone, date, not spam.
2. I pick the closest business that actually offers what was asked for, respecting who the customer chose.
3. I email that business the lead with a short, honest intro.
4. One follow-up; if no answer, the next closest business (only if the customer allowed sharing).
5. Interested replies go to you to close the deal.
**You approve:** the first emails (drafts), until you trust it to send on its own.
**Cadence:** every couple of hours, because leads go cold fast. Runs with nothing new stop in seconds.
**What you get:** every lead routed within hours, plus a list of businesses that want more.
**What I need from you:** your leads, business emails (I can find missing ones from their websites), a mailbox to send from, your first name and your business postal address (email law).
**Make it yours:** "first lead free, then $25", "never email national chains", "skip leads under 50 guests".

**Onboarding sample:** the email inventory (how many businesses I can reach, before and after the email finder on a sample of 10), and 2 example lead emails drafted from real leads, only to confirmed addresses.

**If a step fails** (blocked site, thin data): use the fallback documented here or in REFERENCE.md and still deliver the best honest sample. Never end with less without telling the owner, in plain words, what blocked it and the fix.

## Hard rules (scripts enforce the first four)

1. **Only confirmed addresses.** `send_mail.py --routable-file` refuses any address not in the routable list or on `notes/<slug>/questionable-emails.txt`. Never draft or send to an address you're asking the owner about. When refused: pick the next confirmed business or hold the lead; never work around it.
2. **One free lead per business, drafts included.** Template A is sent with `--free`; `send_mail.py` refuses a second free email (sent or drafted) to the same address. Use Template B/B2 instead, or hold.
3. **Never invent the sender's name or postal address.** Missing → `[NEEDED: …]` in the draft (a real send is refused) and ask once in the summary.
4. **Copy rules:** no em dashes, no hyphen ranges, stop line and postal address in every email, no unfilled `{placeholders}`.
5. **Consent:** reroute to a business the customer didn't pick only when the consent column is true.
6. **Service fit before distance.** Never claim a fit you didn't see.
7. **Very first run ever:** show the emails and wait for "go", even if `auto_send` is true.
8. All database access through `directory-db/db.py` with `--allowed-tables` (REFERENCE.md § Allowed writes). All files under `$DIROPS_REPO/notes/<slug>/` (default `/data/workspace/directory-ops/notes/<slug>/`), never `/tmp`.

Read `sites/<slug>.yaml` (section `lead_routing`) and `notes/<slug>.md` before every run (missing notes file: create it with a 3 line header: site name, URL, "Owner rules go here"). Follow the `## Send leads to businesses rules` section of the notes; this skill's safety rules still win. Missing config section: run Step 0 (never copy `sites/example.yaml` wholesale). A value missing or `TBD` during a scheduled run: skip that part, finish, and put the question at the top of the summary.

## Step 0: One time setup (only if not done)

Quick mode (onboarding): ask only `[essential]` questions onboarding hasn't answered, one per message; use defaults for the rest and list them in one line ("Defaults I used: …").

1. **Mailbox** (REFERENCE.md § Mailbox). Only the password is an env var (`sender.password_env`), added by the owner on the Hermes host, never in chat. No password yet: drafts only mode (`auto_send: false`), everything else works.
2. **Price per lead** [essential]: "How much will you charge a business per lead after the free one? (default: $15)" → `offer.price_per_lead_usd`. Unlock link optional (blank = Template B2).
3. **Who signs and the postal address** [essential]: "What first name should sign the emails?" and "What postal address should the emails show? Email law requires one (a business address or PO box)." Never fill these yourself.
4. **What a lead looks like:** read the leads table once, fill `lead_fields`, `needed_by_field`, `phone_country`, and the other wording keys with defaults (REFERENCE.md § Config details). Show one plain line: "Each lead email will show: Looking for, Date, Budget. Is that right?"
5. **No double emails:** if the website already emails businesses about leads, the owner picks which one does first contact before this job is enabled.
6. **Business email inventory:** count listings with a routable email (`db.py count` / `select --all` on `tables.vendor_emails` with `is_routable` true, or `tables.listing_email_column`). Tell the owner: "42 of your 300 businesses have an email I can send leads to." Under 80%: offer the email finder, show 5 first, save only what the owner approves, and run the no-website sample of 10 with the free Google lookup (REFERENCE.md § Email finder). Report before and after in one line.

### Teach me your way (one optional question, right after this helper is accepted)

> Tell me how you handle leads today: what makes a good lead, who should get it first, anything you never want sent. Ramble or send a voice note; it makes me much better. (Or say "skip".)

Add 3 examples from REFERENCE.md § Teach me your way examples. Turn the answer into 3 to 7 short numbered rules, show them back ("Got it, I'll: 1) … 2) …"; in quick mode end with "Say 'change …' anytime."), and save them under `## Send leads to businesses rules` in `notes/<slug>.md`. **Learn from corrections:** when the owner rejects or edits a proposal, ask once "Want me to remember that as a rule for next time? (yes/no)"; yes → add it with today's date.

## Step 1: Find work (keep it cheap)

```
python3 /data/skills/directory-ops/directory-db/db.py count --site-url <database.url> --key-env <database.key_env> \
  --table <tables.leads> --where "<lead_status.column>=eq.<lead_status.new>"
```

Nothing new, no replies, no follow ups due, no draft awaiting its one reminder → one line ("Lead routing: nothing to do") and stop. A draft gets ONE reminder in total (log `draft_reminded`).

New leads = "new" status, created within `lead_max_age_days`, needed-by date (if set) at least `min_days_before` days away, and after `route_leads_created_after` if set. Never route old or past-date leads. First run: report how many older leads were skipped.

Save the routable list for this run:
```
python3 /data/skills/directory-ops/directory-db/db.py select --all ... --columns <email column> --where "is_routable=eq.true" > $DIROPS_REPO/notes/<slug>/tmp/routable.json
```

## Step 2: Quality check every new lead

```
python3 <this skill folder>/check_lead.py --email "<email>" --phone "<phone>" [--needed-by <date>] --phone-country <phone_country>
```

`pass` / `review` / `reject` / `skip` (needed-by date passed: log `skipped`, never route). Then judge name, location, spam and duplicates yourself (REFERENCE.md § Quality check details). **`pass` from the script is final for the phone: an empty phone is never a reason to hold.** A request is clear when it names what they want (even 2 words like "hand wash") and a date or "soon"; route it by email only and say so in one line. Hold only for spam, a fake or unreachable email, a past date, or no request at all. Log `quality_reject` / `quality_review` with the reason and set the lead's status.

## Step 3: Pick the business

1. **Lead came from a listing page:** that business first, if it has a confirmed address.
2. **Otherwise, or if it can't be emailed and consent is true:** among active listings with a confirmed address, keep those whose **service fields, name or website match the request** (REFERENCE.md § Picking the business), then take the closest (haversine on lat/lng). Distance never beats fit: a hand wash 3 miles away doesn't get a membership request when a matching business is 10 miles away.
3. **No business shows a fit:** take the closest confirmed one and write "fit unknown" next to that lead in the summary.
4. **Customer chose a business, it can't be emailed, consent false:** don't route; list the lead with that business's phone or contact form so the owner can pass it on by hand.
5. Address sanity check (wrong country, head office, no-reply, questionable, or one that looks like a placeholder or test address such as `test@`, `demo`, `example`): REFERENCE.md § Picking the business. When you ask the owner about an address, add it to the questionable list first.
6. Tell the owner why in one line when you reroute: "Arbor's email isn't confirmed, so I picked GO Car Wash, 10 miles away, which sells memberships; the customer allowed sharing."

## Step 4: Send (or draft) the first email

Read `TEMPLATES.md`. First email to this business ever (no free email sent or drafted in `sent-mail.jsonl`): Template A with `--free`. Otherwise B (unlock link) or B2 (reply "yes").

```
python3 <this skill folder>/send_mail.py --slug <slug> --host <sender.smtp_host> --port <sender.smtp_port> \
  --from-email <sender.from_email> --from-name "<sender.from_name>" --password-env <sender.password_env> \
  --to <business email> --subject "<subject>" --body-file $DIROPS_REPO/notes/<slug>/tmp/<lead_id>.txt --daily-cap <daily_send_cap> \
  --routable-file $DIROPS_REPO/notes/<slug>/tmp/routable.json --lead-id <lead id> [--free] [--draft] [--reply-to-id <message id>]
```

- **Sent:** log `first_email`, distributions row `sent` (if configured), lead status "sent".
- **Draft** (`auto_send` false or no password): add `--draft`. Log `first_email_draft`, distributions `draft`, lead status `draft` (or `review`). Never "sent" for a draft. **One waiting draft per lead:** before drafting, check the lead's status and the distributions table for a draft already waiting (including drafts made before this setup); pass `--lead-id <id>` so `send_mail.py` refuses a second one. If one is waiting, show "1 draft already waiting" and offer to replace it; only after the owner says replace, use `--replace-draft`.
- **Owner says "send it":** `send_mail.py --send-draft <draft file> --routable-file <routable.json>` (add `--free` if it was the free one, so the log records it). Then status "sent", distribution `sent`, log `first_email`.
- Test emails to the owner: `--kind owner`. Replies to someone who wrote to us: `--kind reply`.

## Step 5: Read replies

No mailbox password: skip and say so. Otherwise read with inbox-triage's read-only reader:

```
python3 /data/skills/directory-ops/inbox-triage/read_inbox.py --host <sender.imap_host> --user <sender.from_email> --password-env <sender.password_env> --since-days 3 --max 100
```

Classify interested / question / not interested (REFERENCE.md § Replies). Questions are never answered automatically. Opt outs are never emailed again.

## Step 6: Follow up and reroute

- No reply after `followup_after_hours`: Template C once, same thread (`--reply-to-id`). Never more than one follow up.
- No reply after `reroute_after_hours`, consent true: up to `max_vendors_per_round` businesses within the first radius, then the next radius; same fit-before-distance rule and same template choice (A only with `--free` if that business never had one). Consent false: stop and note it.

## Owner report (every run that did work)

Max ~600 words for an onboarding sample, max 6 lines for a scheduled run. Start with what the owner must do.

- **At most 3 decisions**, each one question with your recommended answer. Everything else: apply the default silently and list it in ONE line, "Defaults I used: …".
- Then: leads (sent / held / rejected, a short reason each, "fit unknown" where it applies), emails (first emails, follow ups, reroutes, auto replies), replies (interested / questions / opt outs), and the email coverage line ("8 of 44 businesses can receive leads").
- Never list raw database rows, file paths or column names to the owner.
