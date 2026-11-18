---
name: directory-db
description: Shared helper that every directory-ops skill uses to read and change the site's listings safely, whether they live in Supabase or in files in a GitHub repo (only allowed tables, never deletes, logs old and new values, dry run). You rarely call it directly; other skills tell you when to use it. Use it whenever a skill says "read from" or "write to" the database.
---

# directory-db (shared helper)

Other skills use this instead of writing their own database code. It keeps a weaker model from making a mess: it refuses tables the job isn't allowed to touch, never deletes anything, needs an exact row match for every update, and logs every change so it can be undone.

The script is `db.py` in this skill's folder: `<skills folder>/directory-db/db.py` (on Hostinger the skills folder is `/data/skills/directory-ops`). Other skills call it by that path.

## Rules for every skill

1. **All database reads and writes go through `db.py`.** Never write your own API calls, SQL or curl commands for the site's data.
2. **`--key-env` (or, for a GitHub repo, `--backend repo --repo ... --token-env ...`) always comes from the site config's `database` section** (e.g. `SCW_SUPABASE_KEY`, or whatever name the owner used). Never guess it from the slug.
3. **Pass the job's allowed tables** with `--allowed-tables`: the job's `allowed_tables` in the site config (if missing: that job's own table list, else `database.listings_table`). The script refuses anything else.
4. **Update one row at a time,** matched by its id: `--match "id=eq.123"`. The script refuses an update that hits more than one row unless you raise `--max-rows` on purpose.
5. **Always pass `--slug`, `--why` and `--source`** on writes, so the owner can see why something changed.
6. **New kind of change? Run it with `--dry-run` first** and look at the output.
7. **Applying an approved proposal:** pass `--expect` with the old values from the proposal. If someone changed the row since, it refuses instead of overwriting.
8. **Moving the site's "last updated" date:** pass `--touch <column>` (the config's `database.updated_at_column`) only when the site wants real data changes to move it. `--touch` only fires when something actually changed.
9. **Counting rows:** `db.py count --table <t> [--where ...]` gives the exact total. `select` returns 100 rows by default and says so in `"warning"` when there are more; use `--all` to get every row.
10. **There is no delete.** Closed businesses are marked closed in the site's own way, never deleted.

## Examples

```
# read
python3 db.py select --site-url https://<ref>.supabase.co --key-env <key_env from the site config> \
  --table listings --where "state=eq.Ohio" --columns "id,name,phone,updated_at" --order "updated_at.asc" --limit 20

# how many rows
python3 db.py count --site-url https://<ref>.supabase.co --key-env <key_env from the site config> --table listings

# change one field on one listing (applying an approved proposal: --expect the old value)
python3 db.py update --site-url https://<ref>.supabase.co --key-env <key_env from the site config> \
  --allowed-tables listings --table listings --match "id=eq.123" \
  --set '{"phone": "(555) 010-2000"}' --expect '{"phone": "(555) 010-1000"}' --touch updated_at \
  --slug example --why "phone changed" --source https://sunrisecarwash.example/contact

# add a listing
python3 db.py insert ... --allowed-tables listings --table listings --row '{"name": "Sunrise Car Wash", "city": "Dayton"}' --slug example --why "owner email" --source <link>
```

Filters use Supabase's format `column=op.value`: `eq`, `neq`, `lt`, `gt`, `is.null`, `in.(1,2,3)`, `ilike.*wash*`.

## Listings in a GitHub repo (no database)

Many directories built with Claude Code keep their listings in files inside the site's code: `data/listings.json`, `data/listings.csv`, `data/listings.yaml`, or one Markdown file per listing (`content/listings/*.md`). The same commands work with `--backend repo`. The difference: **changes never go live directly. They arrive as one pull request on GitHub, and the owner merges it to publish.** Merging is the approval; closing it rejects the changes. A day's changes all land in the same pull request.

**Two ways to work with listings in GitHub (offer both; the first needs no setup):**

1. **A copy of the file (no setup).** The owner downloads the file once ("in GitHub, open the file, click the **Download raw file** button, then attach it here"). Save it under `notes/<slug>/listings/` and read it with `--local-dir notes/<slug>/listings`. Approved changes are written with `--out-dir notes/<slug>/listings/out` (the owner's copy is never changed); then send the owner the updated file: "Here's your updated listings file. Put it back in your project in place of the old one (or ask Claude Code to)." Before each later run, ask for a fresh copy only if they changed listings themselves.
2. **Hands-off (a GitHub access key).** Every week's fixes arrive as one change on GitHub the owner approves with one click. One-time setup below.

**GitHub access key (one source of truth):** walk the owner through `/data/skills/directory-ops/setup-guides/guides/github-access-key.md`, then `/data/skills/directory-ops/setup-guides/guides/add-a-setting-in-hostinger.md` with the setting name `<SLUG>_GITHUB_TOKEN` (fill in the exact name). It only lets you suggest changes to the one project their listings are in; nothing goes live until they approve it. When it worked, say "I can see your listings" and how many there are.

Write into the site config: `database.backend: repo`, `database.repo: owner/name` (from the repo's web address), `database.branch: main` (the branch the site is built from), `database.token_env: <SLUG>_GITHUB_TOKEN`, `database.listings_table: <the data file or folder>`.

**Find the listings file yourself** (don't ask the owner for file names):
```
python3 db.py tables --backend repo --repo <owner/name> --token-env <SLUG>_GITHUB_TOKEN
```
Then ask one yes/no in plain words, without the file path: "I found your list of businesses: 5 car washes. Is that the right one?"

**Examples:**
```
python3 db.py select --backend repo --repo <owner/name> --token-env <SLUG>_GITHUB_TOKEN \
  --table data/listings.json --where "id=eq.3"

python3 db.py update --backend repo --repo <owner/name> --token-env <SLUG>_GITHUB_TOKEN \
  --allowed-tables data/listings.json --table data/listings.json --match "id=eq.3" \
  --set '{"phone": "(555) 010-2000"}' --expect '{"phone": null}' \
  --slug example --why "phone on official site" --source https://sunrisecarwash.example/contact
# a folder of Markdown files: --table "content/listings/*.md", match on a front matter field or the file name (_slug)
```

**What to know:**
- The result includes `"pull_request"`: always give the owner that link with: "I've suggested the changes on GitHub. Open this link and click the green **Merge pull request** button to publish them (or **Close** to say no)."
- Only the changed values change in the file (indentation, key order, quotes and comments are kept). If a file is formatted in a way that can't be kept, it refuses and says so; don't pass `--allow-reformat` unless the owner agrees to a bigger diff.
- Lists, nested values and fields with comments can't be edited this way: it says "change it by hand". Tell the owner.
- In Markdown listings only the front matter (the `---` block at the top) is ever edited, never the page text.
- Filters: `eq`, `neq`, `is.null`, `in.(a,b)`, `lt`, `gt`, `lte`, `gte`, `like`, `ilike` (with `*`).
- Until the owner merges, reads still show the live site's values (that's correct: nothing is published yet). Don't propose the same change again while its pull request is open.

## Reading the result

- `"status": "ok"`: done. Writes say where they were logged (`$DIROPS_REPO/notes/<slug>/db-changes.jsonl`; `DIROPS_REPO` is the repo folder, default `/data/workspace/directory-ops` on Hostinger; set it if your repo lives elsewhere).
- `"status": "unchanged"`: the row already had those values; nothing was written (don't bump any "updated" date).
- `"status": "dry_run"`: shows exactly what would change.
- `"status": "error"`: plain words on what's wrong and how to fix it (missing env var, wrong key, table doesn't exist, too many rows). Stop and tell the owner; don't work around it.

## Undo

Every write is one line in `notes/<slug>/db-changes.jsonl` with the old values. To undo, run an update with the old values and `--why "undo <time>"`.
