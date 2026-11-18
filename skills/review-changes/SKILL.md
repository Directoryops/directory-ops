---
name: review-changes
description: Shows the owner every change the jobs proposed and are waiting for approval, in plain words (old → new, why, source), and applies only the ones the owner approves. Use when the owner says "what's waiting", "show pending changes", "approve 1, 3", "reject 2", "approve all", or after any job says changes are waiting.
---

# Review changes

Jobs that aren't allowed to change the database on their own write their proposals to `notes/<slug>/pending.md`. This skill shows them to the owner and applies only what the owner approves. Nothing is applied without a clear "approve".

## The pending.md format (every job writes exactly this)

One block per row (one listing), newest at the bottom. All field changes for the same row go in the SAME block, so "approve 14" approves that whole listing's change. `id` counts up per site and never repeats.

```
### 14
- status: waiting            # waiting | approved | rejected | applied | failed
- date: 2026-11-17
- job: listing-check
- table: listings
- match: id=eq.123
- name: Sunrise Car Wash (Dayton)
- old: {"phone": "(555) 010-1000", "hours": "9AM-5PM"}
- new: {"phone": "(555) 010-2000", "hours": "8AM-6PM"}
- why: The business's own contact page shows a new number and new hours.
- source: https://sunrisecarwash.example/contact
```

`old` and `new` are JSON objects with the same keys (only the fields that change). For a new row: `match: new`, `old: {}`, `new:` the JSON object of the whole row. If the owner wants only part of a block ("approve 14 but not the hours"), apply just those fields and note it in the block.

## Step 1: Show what's waiting

Read `notes/<slug>/pending.md` for every site (or the one the owner named). List only `status: waiting`, grouped by site, numbered by `id`, in plain words:

```
Example Directory: 3 changes waiting
14. Sunrise Car Wash (Dayton): phone (555) 010-1000 → (555) 010-2000; hours 9AM-5PM → 8AM-6PM. Their contact page shows both. [source]
15. Bubbles Car Wash (Akron): mark as closed. Google shows "Permanently closed" and their site is gone. [source]
16. New listing: Shine Auto Spa, 12 Main St, Kent. Suggested by email, confirmed on Google and their website. [source]

Reply "approve all", "approve 14, 16", "reject 15", or ask about any number.
```

If nothing is waiting, say "Nothing waiting for approval" and stop.

## Step 2: Apply the owner's answer

- **"approve all"**, **"approve 14, 16"**, **"yes"** right after the list = approve those (yes = all shown).
- **"approve 12 to 196"** = every waiting block with an id in that range. **"approve <Brand> sweep"** / **"approve link fix"** = every waiting block under that group heading a job wrote in pending.md (`## <Brand> sweep (<n> listings): ids <first>-<last>`, `## Website link fix (<n> listings): ids <first>-<last>`). Say back the count first ("Applying 185 BioLife changes…"), apply them in batches of 50, and report applied / failed counts at the end. A big group shows the pattern and 3 example rows, never every row, in chat.
- **"reject 15"** = mark rejected. If the owner says why, add `- owner: <reason>` to the block.
- **Learn from corrections:** whenever the owner rejects or edits a proposal, or says "no, because …", ask once: "Want me to remember that as a rule for next time? (yes/no)". Yes: add it in plain words with today's date to `notes/<slug>.md` under `## <helper name> rules` for the job that made the proposal (create the section if missing). That job reads its rules every run.
- A question about a number = answer it from the block (and the source), then wait.
- Anything unclear = ask once. Never guess an approval.
- **A proposal is wrong** (wrong value, wrong listing, or the owner corrects it: "the phone is right but the hours are wrong"): reject that block (or just the wrong fields) with `- owner: <what's wrong>`. Never edit a block's `new` values to fix it yourself. The job re-checks that listing on its next run and may propose again with corrected values, in a new block with a new id. If the owner gives the right value directly ("the hours are 8 to 6"), write it as a new block from job `owner`, with `source: owner`, and apply it once they say approve.

For each approved block, apply it with the shared helper (`directory-db/db.py`). **Allowed tables** = the `allowed_tables` of the job named in the block (`listing_check.allowed_tables`, `inbox_triage.allowed_tables`, …) in the site config; if the job has none: the tables in that job's `types[].table` (or `tables`), else `database.listings_table` only. The block's `table` must be in that list, or mark it `failed`: "table not allowed for this job" (tell the owner: "I couldn't apply #<id>: that job isn't allowed to change that part of your site.").

```
python3 /data/skills/directory-ops/directory-db/db.py update --site-url <database.url> \
  --key-env <database.key_env from the site config> \
  --allowed-tables <the job's allowed tables> --table <table> --match "<match>" \
  --set '<new JSON>' --expect '<old JSON>' [--touch <database.updated_at_column>] \
  --slug <slug> --why "approved #<id>: <why>" --source <source>
```

- `--expect` makes the helper refuse if the row no longer has the old values (someone changed it since).
- Add `--touch <database.updated_at_column>` only if the site config sets `database.touch_updated_at: true` (the site shows a "last updated" date from that column and the owner wants real changes to move it).
- New rows use `insert` with the JSON from `new:`.

Then set the block's status: `applied` (with `- applied: <date>`), or `failed` with the helper's error in plain words. If the helper says "the row changed since this was proposed", mark `failed` and tell the owner in plain words: "#<id> wasn't applied: that listing changed since I proposed it. It now says <current value>." (never say "row" or show the helper's raw error).

After applying, read each changed row back with `db.py select --where "<match>"` and confirm the new values are there.

## Step 3: Make it live and summarise

- If the site config has a `revalidate_url`, call it for the pages that changed so they update now.
- Commit `notes/` (CATALOG rule 6).
- Tell the owner in 3 lines max, plain words only: applied (count + numbers), rejected, not applied (with why, e.g. "the listing changed since I proposed it"), still waiting.

## Housekeeping

Once a month, move blocks that are `applied` or `rejected` and older than 60 days to `notes/<slug>/pending-archive.md` so pending.md stays short.
