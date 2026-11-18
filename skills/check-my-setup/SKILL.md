---
name: check-my-setup
description: Checks that everything directory-ops needs is working, as a simple yes/no list with the exact fix for anything that isn't (keys visible, database and tables reachable, photo bucket, scripts, mailbox login, GitHub pull, scheduled jobs and their last run). Read only. Use when the owner says "check my setup", "is everything working", "why didn't my job run", after adding a key, or after a Hermes update.
---

# Check my setup

Goal: one message that tells a non-technical owner what works and what to fix, one click at a time. This skill never changes anything and never shows secret values (only "visible" or "not visible").

## Step 1: Gather what to check

For each site in `sites/*.yaml` (skip `example.yaml`), collect:
- every env var NAME the config mentions (every `*_env` field, e.g. `database.key_env`, `inbox.password_env`). Use the exact names in the config; never guess them from the slug,
- `database.url` and the tables each enabled job needs (the listing tables from the job sections). Log tables (`listing_check_log`, `listing_place_ids`, `inbox_triage_log`) go in `--optional-tables` unless the job's `log_storage` is `table`; by default jobs keep logs in files under `notes/<slug>/`, so a missing log table is fine,
- every column name the config uses, per table (`database.id_column`, `closed_column`, `updated_at_column`, `key_fields`, `active_filter`'s column, lead-routing's `lead_fields` and `tables.lead_status.column`, page-copy-refresh `columns`): pass them as `--columns <table>:<col>,<col>`. A wrong column name makes jobs skip or fail silently, so this check matters,
- the photo bucket, if a job uses one,
- the mailbox (`inbox.imap_host`, `inbox.address`, `inbox.password_env`), if inbox-triage or lead-routing is on.

## Step 2: Run the checks

```
python3 <this skill folder>/check_setup.py --skills-dir /data/skills/directory-ops --repo /data/workspace/directory-ops \
  --env <NAMES,comma,separated> --site-url <database.url> --key-env <database.key_env> --tables <tables> \
  --columns <table>:<col>,<col> [--columns <other table>:<cols>] \
  [--optional-tables <log tables>] \
  [--bucket <bucket>] [--mail-host <imap host> --mail-user <address> --mail-password-env <NAME>] \
  [--website https://<their site>]
```

`--website` checks Hermes can read the owner's site. ⚠️ "can I read your site" = the site's security turns away simple scanners (not an outage, never call it a rate limit). Small checks still work with your built-in web reader. Only if a scheduled helper reads many pages (broken links, internal links, page copy, emails on their own site), show its `say` line (one yes/no) and, on yes, `setup-guides/guides/let-hermes-past-security.md`.

Run it once per site.

Then check the schedule:
1. List your scheduled jobs with your scheduler (in Hermes: list your cron jobs). Times there are UTC; give the owner their local time too.
2. Compare with the config's `jobs:` section. A job with `enabled: true` but no scheduled job = ❌ "not scheduled" (fix: create it). A scheduled job whose config says `enabled: false` = ⚠️ "<job> is running on a schedule, but my notes say it should be off. Should it keep running?" (ask which is right).
3. For each scheduled job, the date of its last report in `notes/<slug>/` (the newest dated file or log line for that job).

## Step 3: Report

One short block per site. Each check in the script's output has a `status` symbol: print exactly that symbol (`ok: false` with `warn: true` is ⚠️, never ❌). ✅ / ❌ / ⚠️ per line, fixes only for ❌ (a ⚠️ is something to know, not a failure; e.g. a repo not linked to GitHub is fine for testing):

```
Example Directory
✅ I can connect to your database
✅ I can read your listings and leads
❌ The photo folder for new listings is missing
   Fix: I'll walk you through it (about 1 minute). Then say "check my setup" again.
✅ I can log in to your mailbox
✅ I can get skill updates from GitHub
✅ All my tools work
Jobs: listing check (Mondays 9am your time, last ran Nov 16) · inbox (Mondays 10am your time, last ran Nov 16)
⚠️ Lead routing is scheduled but hasn't reported in 10 days.
```

Rules:
- Write every line in plain words, as in the example: no table, column, env var, script, UTC or error-code words. Translate the script's output (e.g. "env var X not visible" → "I can't see your database key yet"; a missing column → "one of the details I track (<plain name>) isn't in your listings"). Times in the owner's local time.
- Give each fix as numbered clicks with the exact name or value to type. One fix at a time if there are several, starting with the one that blocks the most. Use the shared guides for the clicks, never your own copy: a key or password → `/data/skills/directory-ops/setup-guides/guides/add-a-setting-in-hostinger.md` (with the exact setting name); photo folder → `/data/skills/directory-ops/setup-guides/guides/supabase-photo-storage.md`; Supabase key → `/data/skills/directory-ops/setup-guides/guides/supabase-key.md`; mailbox password → `/data/skills/directory-ops/setup-guides/guides/gmail-app-password.md` or `/data/skills/directory-ops/setup-guides/guides/other-mailbox-password.md`; GitHub access key → `/data/skills/directory-ops/setup-guides/guides/github-access-key.md`.
- After any key or setting change, remind: "Saving with 'Save & redeploy' restarts me. Then start a new chat and say 'continue' so I can see it."
- A job with no report for more than twice its cadence gets a ⚠️ line.
- Not linked to GitHub (no `.git` in the repo folder) is ⚠️, not ❌. Say exactly: "Your settings aren't backed up to GitHub yet (optional). Want me to set that up later? Just say 'back up my settings'."
- **When a check has a `say` field, show the owner only that sentence.** `detail` is a technical hint for you, never for the owner.
- If you can't list the scheduler's jobs, say why in one line ("I couldn't read the schedule list") instead of reporting jobs as "not scheduled".
- Never print, repeat or ask for a key or password in chat.
- Never tell the owner to "ask Hermes to run SQL" or to create tables for logs: logs live in files. If a listing table itself is missing, the config has the wrong table name: try `db.py tables` to find the right one yourself and fix the config; only if that fails, ask the owner to read the names in Supabase → Table Editor.
