#!/usr/bin/env python3
"""Safe database helper for every directory-ops skill (Supabase REST, no extra installs).

Every skill that reads or writes the site's database goes through this script instead of writing
its own API calls. It refuses tables the job isn't allowed to touch, never deletes, needs a match
filter for every update, logs old and new values for every write, and has a dry run.

    python3 db.py select --site-url https://<ref>.supabase.co --key-env <key_env from the site config> \
        --table listings --where "state=eq.Ohio" --columns "id,name,phone" --limit 50

    python3 db.py update --site-url ... --key-env ... --allowed-tables listings \
        --table listings --match "id=eq.123" --set '{"phone": "(555) 010-2000"}' \
        --slug example --why "phone changed on official site" --source https://example.com/contact [--dry-run]

    python3 db.py count --site-url ... --key-env ... --table listings [--where "state=eq.Ohio"]
    python3 db.py select ... --all          # every row (pages through 1000 at a time)

    update extras: --expect '{"phone": "(555) 010-1000"}' refuses if the row no longer has those values
    (someone changed it since the proposal); --touch updated_at sets that column to now.

    python3 db.py insert  ... --table listings --row '{"name": "Sunrise Car Wash", ...}'
    python3 db.py upsert  ... --table listings --row '{...}' --on-conflict id

Listings in files in a GitHub repo (JSON, CSV, YAML, or a folder of Markdown files): add
    --backend repo --repo owner/name --token-env <NAME of the GitHub token variable> [--branch main]
and use the file (data/listings.json) or folder (content/listings/*.md) as --table. Writes never touch
the live branch: they go to one pull request per day that the owner merges to publish. See repo_backend.py.

Filters use Supabase's format: column=op.value, e.g. "id=eq.123", "state=eq.Ohio",
"updated_at=lt.2026-01-01", "phone=is.null". Repeat --where / --match for more than one.

Writes (insert, update, upsert) need --allowed-tables, and the table must be in it.
Every write appends one JSON line to --log (default $DIROPS_REPO/notes/<slug>/db-changes.jsonl when
--slug is given; DIROPS_REPO defaults to /data/workspace/directory-ops): time, action, table, match, old values (read first), new values, why, source.
There is no delete command on purpose: directories mark things closed, they never delete.
Output is JSON. Exit code 1 on any error, with a plain-words "error".
"""
import argparse
import datetime
import json
import re
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

WRITE_ACTIONS = ("insert", "update", "upsert")
PAGE = 1000


class DbError(Exception):
    pass


def build_parser():
    ap = argparse.ArgumentParser(description="Safe listings helper for Supabase or a GitHub repo (select, insert, update, upsert; no delete).")
    sub = ap.add_subparsers(dest="action", required=True)

    def backend_args(p):
        p.add_argument("--backend", choices=["supabase", "repo"], default="supabase",
                       help="supabase (default) or repo (listings in files in a GitHub repo; changes arrive as a pull request)")
        p.add_argument("--site-url", default="", help="supabase: https://<project>.supabase.co")
        p.add_argument("--key-env", default="", help="supabase: NAME of the env var holding the key (never the key)")
        p.add_argument("--repo", default="", help='repo: "owner/name" on GitHub')
        p.add_argument("--branch", default="main", help="repo: the branch the live site is built from (default main)")
        p.add_argument("--token-env", default="", help="repo: NAME of the env var holding the GitHub token (never the token)")
        p.add_argument("--local-dir", default="", help="repo: read files from a local folder instead (previews and tests only)")
        p.add_argument("--out-dir", default="", help="repo + --local-dir: save updated files here (the owner's copy is never changed)")

    def common(p, write):
        backend_args(p)
        p.add_argument("--table", required=True, help="supabase: table name. repo: data file (data/listings.json) or folder of .md files (content/listings/*.md)")
        p.add_argument("--id-field", default="id", help="repo: the field that identifies a listing (default id)")
        p.add_argument("--allow-reformat", action="store_true", help="repo: allow rewriting a file whose formatting can't be kept")
        p.add_argument("--allowed-tables", default="", help="comma separated; writes refuse any other table")
        if write:
            p.add_argument("--slug", default="", help="site slug, sets the default log path")
            p.add_argument("--log", default="", help="JSON lines log path (default $DIROPS_REPO/notes/<slug>/db-changes.jsonl)")
            p.add_argument("--why", default="", help="reason, saved in the log")
            p.add_argument("--source", default="", help="evidence URL, saved in the log")
            p.add_argument("--dry-run", action="store_true", help="show what would change, write nothing")

    s = sub.add_parser("select")
    common(s, False)
    s.add_argument("--where", action="append", default=[], help='filter like "state=eq.Ohio" (repeatable)')
    s.add_argument("--columns", default="*")
    s.add_argument("--limit", type=int, default=100)
    s.add_argument("--all", action="store_true", help="return every matching row (ignores --limit)")
    s.add_argument("--order", default="", help='e.g. "updated_at.asc"')

    t = sub.add_parser("tables", help="list the tables (or, in repo mode, the data files) this key can see")
    backend_args(t)
    t.add_argument("--guess", default="", help="extra comma separated names to try, e.g. words from the site's niche")

    c = sub.add_parser("count")
    common(c, False)
    c.add_argument("--where", action="append", default=[], help='filter like "state=eq.Ohio" (repeatable)')

    i = sub.add_parser("insert")
    common(i, True)
    i.add_argument("--row", required=True, help="JSON object, or a JSON list of objects")

    u = sub.add_parser("update")
    common(u, True)
    u.add_argument("--match", action="append", default=[], help='which rows, e.g. "id=eq.123" (required, repeatable)')
    u.add_argument("--set", required=True, help="JSON object of new values")
    u.add_argument("--max-rows", type=int, default=1, help="refuse if the match hits more rows than this (default 1)")
    u.add_argument("--expect", default="", help="JSON of values the row must still have; refuse if any differs")
    u.add_argument("--touch", default="", help="timestamp column to set to now (e.g. updated_at)")

    p = sub.add_parser("upsert")
    common(p, True)
    p.add_argument("--row", required=True, help="JSON object, or a JSON list of objects")
    p.add_argument("--on-conflict", required=True, help="unique column(s) to match on, e.g. id")
    return ap


def parse_filters(items):
    out = []
    for f in items:
        if "=" not in f or "." not in f.split("=", 1)[1]:
            raise DbError(f'filter "{f}" must look like column=op.value, e.g. "id=eq.123"')
        col, rest = f.split("=", 1)
        if not col.strip():
            raise DbError(f'filter "{f}" has no column name')
        out.append((col.strip(), rest.strip()))
    return out


def parse_json(text, what):
    try:
        v = json.loads(text)
    except json.JSONDecodeError as e:
        raise DbError(f"{what} is not valid JSON: {e.msg}") from None
    return v


def check_args(a):
    """Safety checks that need no network. Returns (filters, payload)."""
    allowed = [t.strip() for t in a.allowed_tables.split(",") if t.strip()]
    if a.action in WRITE_ACTIONS:
        if not allowed:
            raise DbError("writes need --allowed-tables (the tables this job may change, from its config)")
        if a.table not in allowed:
            raise DbError(f'table "{a.table}" is not in this job\'s allowed tables ({", ".join(allowed)})')
    filters, payload = [], None
    if a.action in ("select", "count"):
        filters = parse_filters(a.where)
    elif a.action == "update":
        filters = parse_filters(a.match)
        if not filters:
            raise DbError("update needs --match (which rows). Updating a whole table is not allowed.")
        payload = parse_json(a.set, "--set")
        if not isinstance(payload, dict) or not payload:
            raise DbError("--set must be a JSON object with at least one field")
        if a.expect:
            exp = parse_json(a.expect, "--expect")
            if not isinstance(exp, dict):
                raise DbError("--expect must be a JSON object")
    else:
        payload = parse_json(a.row, "--row")
        if isinstance(payload, dict):
            payload = [payload]
        if not isinstance(payload, list) or not payload or not all(isinstance(r, dict) for r in payload):
            raise DbError("--row must be a JSON object or a list of objects")
    return filters, payload


def log_path(a):
    if a.log:
        return a.log
    if a.slug:
        repo = os.environ.get("DIROPS_REPO", "/data/workspace/directory-ops")
        return os.path.join(repo, "notes", a.slug, "db-changes.jsonl")
    return ""


def request(a, method, table, params, body=None, prefer="", want_headers=False, range_=None):
    key = os.environ.get(a.key_env, "").strip().strip("\"'")  # pasted keys often carry a line break or quotes
    if not key:
        raise DbError(f"env var {a.key_env} is not visible. Add it on your host (hPanel → Environment), restart, start a new chat.")
    url = a.site_url.rstrip("/") + "/rest/v1/" + urllib.parse.quote(table) + ("?" + urllib.parse.urlencode(params) if params else "")
    headers = {"apikey": key, "Content-Type": "application/json"}
    if not key.startswith("sb_"):  # new-style keys (sb_secret_/sb_publishable_) are not JWTs: apikey header only
        headers["Authorization"] = f"Bearer {key}"
    if prefer:
        headers["Prefer"] = prefer
    if range_:
        headers["Range-Unit"] = "items"
        headers["Range"] = range_
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            txt = r.read().decode("utf-8", "ignore")
            data = json.loads(txt) if txt.strip() else []
            return (data, dict(r.headers)) if want_headers else data
    except urllib.error.HTTPError as e:
        msg = e.read()[:300].decode("utf-8", "ignore")
        hint = {401: "the key is wrong or expired", 403: "the key can't do this (use the service role key for writes)",
                404: f'table "{table}" does not exist'}.get(e.code, "")
        raise DbError(f"database said {e.code}{': ' + hint if hint else ''}. {msg}") from None
    except urllib.error.URLError as e:
        raise DbError(f"can't reach {a.site_url} ({e.reason}). Check the site URL in the config.") from None


def total_from(headers):
    """Content-Range "0-99/1234" -> 1234 (None if unknown)."""
    cr = {k.lower(): v for k, v in headers.items()}.get("content-range", "")
    tail = cr.split("/")[-1] if "/" in cr else ""
    return int(tail) if tail.isdigit() else None


def write_log(a, entry):
    path = log_path(a)
    if not path:
        return ""
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return path
    except OSError as e:
        # The database change already happened; never report it as failed. Print the entry so it can be saved by hand.
        print(json.dumps({"warning": f"change saved in the database, but the log file could not be written ({e}). "
                                     "Copy this line into notes/<slug>/db-changes.jsonl:", "entry": entry}, ensure_ascii=False),
              file=sys.stderr)
        return f"NOT LOGGED ({e.strerror})"


COMMON_TABLES = ["listings", "business_listings", "businesses", "companies", "places", "locations", "stores", "shops",
                 "vendors", "providers", "directory", "entries", "items", "profiles", "leads", "inquiries", "quotes",
                 "contacts", "pages", "page_content", "site_pages", "state_page_content", "city_pages", "content",
                 "articles", "posts", "blog_posts", "categories", "reviews", "cities", "states", "jobs", "products"]


def list_tables(a):
    key = os.environ.get(a.key_env, "").strip().strip("\"'")
    if not key:
        raise DbError(f"env var {a.key_env} is not visible. Add it on your host (hPanel → Environment), restart, start a new chat.")
    h = {"apikey": key}
    if not key.startswith("sb_"):
        h["Authorization"] = f"Bearer {key}"
    root = a.site_url.rstrip("/") + "/rest/v1/"
    try:
        with urllib.request.urlopen(urllib.request.Request(root, headers=h), timeout=30) as r:
            spec = json.loads(r.read().decode("utf-8", "ignore"))
        names = sorted(k for k in spec.get("definitions", {}))
        if names:
            return {"status": "ok", "how": "full list (service role key)", "tables": names}
    except Exception:  # noqa: BLE001
        pass
    guesses = COMMON_TABLES + [g.strip().lower().replace(" ", "_") for g in a.guess.split(",") if g.strip()]
    for g in list(guesses):
        if re.search(r"(s|sh|ch|x|z)$", g):
            guesses.append(g + "es")
        elif not g.endswith("s"):
            guesses.append(g + "s")
    found = []
    for name in dict.fromkeys(guesses):
        req = urllib.request.Request(root + urllib.parse.quote(name) + "?select=*&limit=1", headers=h)
        try:
            with urllib.request.urlopen(req, timeout=15):
                found.append(name)
        except Exception:  # noqa: BLE001
            continue
    return {"status": "ok", "how": "guessed common names (this key can't list tables; a service role key can)", "tables": found,
            "note": "If a table is missing, ask the owner to read its name in Supabase → Table Editor."}


def run_repo(a):
    import repo_backend
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    try:
        if a.action == "tables":
            return repo_backend.list_tables(a)
        filters, payload = check_args(a)
        return repo_backend.run(a, filters, payload, now, write_log)
    except repo_backend.RepoError as e:
        raise DbError(str(e)) from None


def run(a):
    if getattr(a, "backend", "supabase") == "repo":
        if not (a.local_dir or (a.repo and a.token_env)):
            raise DbError("repo mode needs --repo owner/name and --token-env <NAME of the GitHub token variable>")
        return run_repo(a)
    if not a.site_url or not a.key_env:
        raise DbError("needs --site-url and --key-env (the database URL and the NAME of the key variable from the site config)")
    if a.action == "tables":
        return list_tables(a)
    filters, payload = check_args(a)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")

    if a.action == "count":
        params = [(c, v) for c, v in filters] + [("select", "*"), ("limit", "1")]
        _, headers = request(a, "GET", a.table, params, prefer="count=exact", want_headers=True)
        return {"status": "ok", "table": a.table, "total": total_from(headers)}

    if a.action == "select":
        base = [(c, v) for c, v in filters] + [("select", a.columns)]
        if a.order:
            base.append(("order", a.order))
        if a.all:
            rows, start = [], 0
            while True:
                page = request(a, "GET", a.table, base, range_=f"{start}-{start + PAGE - 1}")
                rows += page
                if len(page) < PAGE:
                    break
                start += PAGE
            return {"status": "ok", "rows": rows, "count": len(rows), "total": len(rows)}
        rows, headers = request(a, "GET", a.table, base + [("limit", str(a.limit))], prefer="count=exact",
                                want_headers=True)
        out = {"status": "ok", "rows": rows, "count": len(rows)}
        total = total_from(headers)
        if total is not None:
            out["total"] = total
            if total > len(rows):
                out["warning"] = f"showing {len(rows)} of {total} rows; use --all (or a higher --limit) to get every row"
        return out

    if a.action == "update":
        old = request(a, "GET", a.table, [(c, v) for c, v in filters] + [("select", "*")])
        if not old:
            raise DbError("no row matches; nothing changed. Check the --match filter.")
        if len(old) > a.max_rows:
            raise DbError(f"the match hits {len(old)} rows (limit {a.max_rows}). Match on the row's id, or raise --max-rows on purpose.")
        if a.expect:
            exp = json.loads(a.expect)
            stale = [{k: {"expected": v, "now": r.get(k)}} for r in old for k, v in exp.items() if r.get(k) != v]
            if stale:
                raise DbError("the row changed since this was proposed, so nothing was written. "
                              f"Re-check it: {json.dumps(stale, default=str)[:300]}")
        changes = [{k: {"old": r.get(k), "new": v} for k, v in payload.items() if r.get(k) != v} for r in old]
        if not any(changes):
            return {"status": "unchanged", "note": "the row already has these values"}
        if a.touch:
            payload = dict(payload, **{a.touch: now})
        entry = {"time": now, "action": "update", "table": a.table, "match": dict(filters),
                 "changes": changes, "why": a.why, "source": a.source}
        if a.touch:
            entry["touched"] = a.touch
        if a.dry_run:
            return {"status": "dry_run", "would_change": entry}
        new = request(a, "PATCH", a.table, [(c, v) for c, v in filters], payload, "return=representation")
        entry["rows_changed"] = len(new)
        return {"status": "ok", "rows_changed": len(new), "log": write_log(a, entry), "changes": changes}

    # insert / upsert
    entry = {"time": now, "action": a.action, "table": a.table, "rows": payload, "why": a.why, "source": a.source}
    if a.action == "upsert":
        entry["on_conflict"] = a.on_conflict
        ids = [r.get(a.on_conflict) for r in payload if r.get(a.on_conflict) is not None]
        if ids and not a.dry_run:
            vals = ",".join(json.dumps(i) if isinstance(i, str) else str(i) for i in ids)
            entry["old"] = request(a, "GET", a.table, [(a.on_conflict, f"in.({vals})"), ("select", "*")])
    if a.dry_run:
        return {"status": "dry_run", "would_write": entry}
    params = [("on_conflict", a.on_conflict)] if a.action == "upsert" else []
    prefer = "return=representation" + (",resolution=merge-duplicates" if a.action == "upsert" else "")
    res = request(a, "POST", a.table, params, payload, prefer)
    entry["rows_written"] = len(res)
    return {"status": "ok", "rows_written": len(res), "log": write_log(a, entry), "rows": res}


def main(argv=None):
    a = build_parser().parse_args(argv)
    try:
        out = run(a)
        print(json.dumps(out, ensure_ascii=False, default=str))
        return 0
    except DbError as e:
        print(json.dumps({"status": "error", "error": str(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
