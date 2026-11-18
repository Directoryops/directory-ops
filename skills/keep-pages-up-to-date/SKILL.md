---
name: keep-pages-up-to-date
description: Keeps pages whose facts change (fees in a calculator, discount days, coupons, policies, holiday hours, prices) up to date from their official source of truth, on a schedule per page (weekly, monthly, quarterly, yearly). Re-checks each source, updates the same page with a new "Updated" date when something changed, and never creates a second page on the same topic. Use when the owner asks to keep a page current, after a calculator or data page is built, or on its schedule.
---

# Keep pages up to date

## Playbook card (show this to the owner)

Show this card to the owner before setting the helper up (onboarding plan or "add a helper"), so they see and approve the process.

**What it does:** keeps pages with changing facts (fees, prices, discount days, policies) correct, by rechecking each against its official source on its own schedule.
**Why it works:** pages like "X fees" win because they're always right, and lose the moment they're stale. One page per topic, updated in place, beats new pages every year.
**How I work:**
1. I list your pages with facts that change, and you confirm them.
2. For each fact, I note its official source and how often it changes.
3. When it's due, I compare the source with your page, fact by fact.
4. If something changed, I update it (or hand you the exact change) and move the "last checked" date.
5. Blocked or unclear sources are flagged, never guessed.
**You approve:** the page list once, then any change (or let database pages update on their own).
**Cadence:** per page: weekly for things like discount days, monthly for fees, yearly for rules.
**What you get:** pages that are always current, with a real "last checked" date.
**What I need from you:** nothing to start. Pages stored in code need a quick paste into Claude Code when something changes.
**Make it yours:** "check fees on the 1st of each month", "tell me right away when a price goes up".

**Onboarding sample:** the list of pages it would keep current, with the official source and check cadence for each.

**If a step fails** (blocked site, thin data, noisy results): try the fallback this skill documents, and still deliver the best honest sample. Never end with less than the onboarding sample without telling the owner, in plain words, what blocked it and the fix.


Goal: be the page that is always right. Pages like "X fees", "X discount days", "X return policy" or a fee calculator win because they're current, and lose the moment they're stale. This job keeps them current (they're called "living pages" in the log); it doesn't write new pages (content-opportunities does that).

Read `sites/<slug>.yaml` (section `keep_pages_up_to_date`) and `notes/<slug>.md` first. The list of living pages is `notes/<slug>/keep-pages-up-to-date.yaml`. If `notes/<slug>.md` is missing, create it with a 3 line header (site name, URL, "Owner rules:"). If the config has no `keep_pages_up_to_date` section, run Step 0. If the list file is missing, build it (below) before anything else. Files go under `$DIROPS_REPO/notes/<slug>/`, never `/tmp`.

## Step 0: Settings (first run only)

If `keep_pages_up_to_date.settings_done` is not `true`, ask one question per message, each with its default shown (the owner can reply "use the defaults for the rest" at any point), save to `keep_pages_up_to_date`, set `settings_done: true`:

**In quick mode (during onboarding), ask only the questions marked `[essential]` that onboarding hasn't already answered, and use the defaults (or what onboarding inferred) for the rest. List the defaults you used in the plan message; the owner changes any of them by saying so.**

```
Questions, one per message (say "use the defaults" anytime to skip the rest):
1. Which pages have facts that change? (fees, prices, discount days, policies, hours) I'll also look for them myself. (default: I'll find them)
2. When I find a change, should I update the page myself, or ask you first? (default: ask you first)
3. Should I tell you every time something changes, or only in a monthly summary? (default: monthly summary, plus right away for big changes like a fee going up)
```

Map to config: `update_db_pages` (default false), `notify` (`monthly_summary` | `every_change`).

Then show the owner the list you found (Step "build the list" below) and ask: "Are these the pages to keep current? Remove or add any." Save only what they confirm.

### Teach me your way (one optional question, right after this helper is accepted)

This is what makes the helper yours instead of generic. Ask once (in quick mode it replaces settings questions, it doesn't add many):

> Tell me which facts go stale on your site, where the official numbers come from, and how fast you want to hear about changes. Ramble or send a voice note; it makes me much better. (Or say "skip".)
> For example:
> - Plasma center: "Donor pay changes monthly; check each chain's own promotions page."
> - Car wash: "Membership prices usually change in January."
> - Roofing: "Permit fees come from each city's website; tell me right away when one changes."

Turn the answer into 3 to 7 short numbered rules in plain words, show them back ("Got it, I'll: 1) … 2) … Anything to change?"; in quick mode end with "Say 'change …' anytime." instead of a question, so onboarding stays short), and save them in `notes/<slug>.md` under `## Keep fee and price pages current rules` (create the section if it's missing). **Every run reads that section first and follows it; this skill's own safety rules still win** (a rule can't make it skip approval, delete things, or use competitors as sources).

**Learn from corrections:** when the owner rejects or edits one of your proposals, or says "no, because …", ask once: "Want me to remember that as a rule for next time? (yes/no)". Yes: add it to `## Keep fee and price pages current rules` in plain words with today's date.

## Allowed writes

- `notes/<slug>/keep-pages-up-to-date.yaml` and `notes/<slug>/keep-pages-up-to-date/`: always, even when the owner chose "ask first". Updating check dates and adding confirmed entries there is bookkeeping, not a change to the website. "Ask first" only applies to the page itself.
- A page's text, numbers and its "Updated"/"Last checked" date stored in the database: only if `update_db_pages` is true (otherwise write the change to `notes/<slug>/pending.md`). Use the shared database helper `/data/skills/directory-ops/directory-db/db.py` for every database write, so old and new values are logged and can be undone.
- Never: code, URLs, titles, headings, other pages, listings.

## The living pages list

`notes/<slug>/keep-pages-up-to-date.yaml`, one entry per page:

```yaml
- page: /car-wash-membership-prices
  facts: "monthly membership price per chain, what's included"
  stored_in: "database: pages table, slug car-wash-membership-prices, field body_md"   # or "code: lib/prices.ts"
  sources:                                   # official sources only, in order of trust
    - https://www.examplechain.com/memberships
  check_every: monthly                       # weekly | monthly | quarterly | yearly | before <event>
  last_checked: 2026-11-17                   # set only when EVERY source was really read (see "Partial")
  last_changed: 2026-11-17                   # set when any value on the page changed
  source_checked:                            # per source: date its content was really read, and the copy's own date
    https://www.examplechain.com/memberships: {checked: 2026-11-17, copy_date: 2026-11-17}
```

To build the list the first time: look for pages showing a date, a year, prices, fees, "days", "hours", "policy", "coupon" or "discount" in the title, plus every calculator. For each, find where the facts come from: open what ranks on Google for that topic, see which official pages they quote, and use those official pages as `sources`. Never use another directory, blog or competitor as a source; they are copies.

## Each run

1. Pick the entries that are due (`last_checked` + `check_every` is today or earlier; weekly = 7 days, monthly = 30, quarterly = 91, yearly = 365). Weekly ones first. **If the owner says "check now" (or names pages), treat those entries (or all of them) as due.**
2. For each, open every source and read the facts. If a source blocks automated visits, try the Internet Archive's newest copy (`https://web.archive.org/web/2/<url>`, which opens the newest saved copy) and say in the log that you used it and its date. **The copy's date is the 14-digit timestamp in the address it redirects to** (`web.archive.org/web/20261103123456/...` = 2026-11-03); record it as `copy_date`.
   **A source only counts if it shows real content.** Treat it as FAILED if the page text contains "captcha", "verify you are human", "are you a robot", "access denied", "enable JavaScript", "enable JS", "JavaScript is disabled", "please enable cookies", "unusual traffic", or has under 500 characters of readable text. An archive copy older than 45 days doesn't count as checked either (record it as `stale_copy`).
3. Compare with what the page says now (read the live page, and the stored value). Write one row per fact:

| Fact | Page says | Source says | Status |
|---|---|---|---|
| Final value fee, most categories | 13.6% | 13.6% | same |
| Per order fee over $10 | $0.40 | $0.45 | CHANGED |
| Store fees | 12.7% | (source failed: captcha) | not checked |

   - **Fact in the list but not shown on the page:** status `not on page`. Write what the page actually shows ("(not shown)"); never copy the source's value into the "Page says" column.
   - **Wording conflict:** the numbers match but a sentence on the page says something the source contradicts (e.g. "a per order fee is added" where the source says it isn't charged in that case): status `wording conflict`. Give the owner a hand-off prompt quoting the exact sentence and the source's wording.
   - **Two values in the source and it's unclear which applies** (e.g. different rates per plan): status `unresolved`, show both, ask the owner once; never pick one yourself.

   Numbers on the page that have no fact in the list: add them to the list as new facts (ask the owner once: "I'll also keep these current: ...").
4. **No change:** set `last_checked` to today only if every source counted. Don't change the page's text.
   - **Code-stored page with a visible "Last checked" date:** that date goes stale even when nothing changed. Give the owner a one-line prompt that updates ONLY that date ("In <file>, change the fees checked date to <today>. Nothing else."). Once, also recommend making that date come from the data file's newest `checked` value so it moves by itself.
   - **Partial** (some sources failed): advance `source_checked` only for the sources that counted; leave `last_checked` alone so the entry is retried next run; list the failed sources in the summary.
5. **Changed:**
   - **Stored in the database** and `update_db_pages` is true: update the value in the same page, update its "Updated" or "Last checked" date, then make it live (the site's revalidate URL if configured). Open the live page and confirm it shows the new value.
   - **Stored in code** (a calculator's fee file, a template): tell the owner in one plain line what changed ("The state raised the permit fee from $45 to $50. Your calculator needs that one update."), then give ONE prompt to paste into Claude Code or send to their developer (the prompt itself can be technical; it's for the coding tool), in this shape: First time? Walk them through `/data/skills/directory-ops/setup-guides/guides/paste-into-claude-code.md`.

```
Update <page> in the website's code. Change only these values:
- <file>: <fact>: <old> → <new> (source: <URL>, seen <date>)
Also set the page's "Last checked" / "Updated" date to <today>.
Then run <the test command from stored_in, e.g. npm run test:fees> and deploy. Don't change anything else.
```

     Never guess the new value from a news article; only from the official source.
   - Set `last_changed` to today. Log it in `notes/<slug>/keep-pages-up-to-date/changes.md`: page, fact, old → new, source, date.
6. **Source gone or unclear:** don't change the page. Flag it in the summary with what you saw.

## Rules

- One page per topic, forever. Update it; never publish "X fees 2027" next to "X fees 2026". Update the year in the title instead.
- Every number on a living page must trace to a source in its entry.
- The page shows "Last checked <date>" or "Updated <date>" near the top. Change it only when you really checked (checked) or really changed something (updated).
- Big changes (a fee or price going up, a program ending) are worth telling the owner right away: it's a chance for a fresh social post or newsletter.

## Summary

Plain words, max 6 lines, starting with what the owner needs to do:
- Waiting on you: updates to paste into your site (one line each: what changed)
- Changed: page, what changed (old → new), and the official source
- All good: pages checked with nothing new
- Couldn't check: which official pages wouldn't open (I'll retry next time)
