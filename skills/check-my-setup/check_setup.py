#!/usr/bin/env python3
"""Yes/no setup checks for directory-ops. Read only: never changes anything, never prints secret values.

    python3 check_setup.py --skills-dir /data/skills/directory-ops --repo /data/workspace/directory-ops \
        --env <database.key_env>,<inbox.password_env> \
        --site-url https://<ref>.supabase.co --key-env <database.key_env> --tables listings \
        [--columns listings:id,name,phone,hours --columns leads:id,status] \
        [--optional-tables listing_check_log,listing_place_ids] \
        [--bucket listing-photos] \
        [--mail-host imap.gmail.com --mail-user site@gmail.com --mail-password-env EXAMPLE_MAIL_PASSWORD] \
        [--website https://example.com]

Every check prints {"check", "ok", "detail"}; "detail" says what's wrong in plain words.
Prints JSON {"all_ok": bool, "checks": [...]}.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request


UA = "Mozilla/5.0 (compatible; directory-ops/1.0; +https://github.com/Directoryops/directory-ops)"


def security_block(status, headers, body="", first=False):
    """'vercel' | 'cloudflare' | 'other' when a security wall answered instead of the page, else None."""
    h = {str(k).lower(): str(v).lower() for k, v in (headers or {}).items()}
    b = (body or "")[:6000].lower()
    server = h.get("server", "")
    if "x-vercel-challenge-token" in h or h.get("x-vercel-mitigated") == "challenge":
        return "vercel"
    if h.get("cf-mitigated") == "challenge" or ("cloudflare" in server and status in (403, 429, 503) and any(
            m in b for m in ("just a moment", "attention required", "challenge-platform", "cf-chl", "cf_chl"))):
        return "cloudflare"
    if "x-sucuri-id" in h or "x-sucuri-block" in h or "sucuri website firewall" in b or "access denied - sucuri" in b:
        return "other"
    if status in (403, 503) and "wordfence" in b:
        return "other"
    if status == 403 and ("akamaighost" in server or ("reference #" in b and "access denied" in b)):
        return "other"
    if first and status == 429:
        return "other"
    return None


def read_site(url):
    """(status, blocked_by) for the owner's website homepage."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, None
    except urllib.error.HTTPError as e:
        try:
            body = e.read(20000).decode("utf-8", "ignore")
        except Exception:  # noqa: BLE001
            body = ""
        return e.code, security_block(e.code, dict(e.headers or {}), body, first=True)
    except Exception:  # noqa: BLE001
        return 0, None


def http_get(url, key):
    h = {"apikey": key}
    if not key.startswith("sb_"):  # new-style keys aren't JWTs
        h["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read()[:2000].decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300].decode("utf-8", "ignore")
    except Exception as e:  # noqa: BLE001
        return 0, str(e)[:200]


def key_role(key):
    """What a Supabase key can do, without calling anything: 'write' (service role / sb_secret_),
    'read' (anon / sb_publishable_), or 'unknown'."""
    if key.startswith("sb_secret_"):
        return "write"
    if key.startswith("sb_publishable_"):
        return "read"
    parts = key.split(".")
    if len(parts) == 3:
        import base64
        try:
            pad = parts[1] + "=" * (-len(parts[1]) % 4)
            role = json.loads(base64.urlsafe_b64decode(pad)).get("role", "")
        except Exception:  # noqa: BLE001
            return "unknown"
        return {"service_role": "write", "anon": "read", "authenticated": "read"}.get(role, "unknown")
    return "unknown"


READ_ONLY_SAY = ("This key can only read your list, so I can't save approved fixes yet. "
                 "Want to swap it for the full key? (2 minutes)")


def main():
    ap = argparse.ArgumentParser(description="Read-only yes/no checks of a directory-ops setup.")
    ap.add_argument("--skills-dir", default="/data/skills/directory-ops")
    ap.add_argument("--repo", default="/data/workspace/directory-ops")
    ap.add_argument("--env", default="", help="comma separated env var NAMES to check (values are never printed)")
    ap.add_argument("--site-url", default="")
    ap.add_argument("--key-env", default="")
    ap.add_argument("--tables", default="", help="comma separated tables that must be readable")
    ap.add_argument("--optional-tables", default="",
                    help="tables a job can use but doesn't need (e.g. log tables when logs are kept in files): missing = info, not a failure")
    ap.add_argument("--columns", action="append", default=[],
                    help="table:col1,col2,... every column the site config names for that table (repeatable)")
    ap.add_argument("--bucket", default="", help="public storage bucket for photos, if the site uses one")
    ap.add_argument("--website", default="", help="the owner's website, to check Hermes can read it")
    ap.add_argument("--mail-host", default="")
    ap.add_argument("--mail-user", default="")
    ap.add_argument("--mail-password-env", default="")
    a = ap.parse_args()
    checks = []

    def add(name, ok, detail="", warn=False, say=""):
        """warn=True: not a failure (⚠️), just something to know.
        detail = technical hint for Hermes; say = the plain sentence to show the owner (if given, show only that)."""
        status = "✅" if ok else ("⚠️" if warn else "❌")
        checks.append({"status": status, "check": name, "ok": bool(ok), "detail": detail,
                       **({"warn": True} if warn else {}), **({"say": say} if say else {})})

    # 1. env vars visible (never print values)
    for name in [n.strip() for n in a.env.split(",") if n.strip()]:
        v = os.environ.get(name, "")
        add(f"env var {name} visible", bool(v),
            "" if v else "Not visible. Add it in hPanel → your Hermes app → Environments (exact name), click Save & redeploy, then start a new chat (setup-guides/guides/add-a-setting-in-hostinger.md).")

    # 2. database reachable + tables readable
    if a.site_url and a.key_env:
        key = os.environ.get(a.key_env, "").strip().strip("\"'")  # pasted keys often carry a line break or quotes
        if not key:
            add("database key", False, f"{a.key_env} is not visible (see above).")
        else:
            role = key_role(key)
            if role == "read":
                add("key_can_write", False, "This is a read-only key (anon / publishable). Writes will fail. "
                    "Owner swaps it for the secret / service role key: setup-guides/guides/supabase-key.md.",
                    warn=True, say=READ_ONLY_SAY)
                checks[-1]["owner_message"] = READ_ONLY_SAY
            elif role == "write":
                add("key_can_write", True)
            else:
                add("key_can_write", True, "Couldn't tell the key type from the key itself; a first approved change will show it.",
                    warn=True)
            optional = {t.strip() for t in a.optional_tables.split(",") if t.strip()}
            for t in ([t.strip() for t in a.tables.split(",") if t.strip()] + sorted(optional)) or ["_none_"]:
                if t == "_none_":
                    st, body = http_get(a.site_url.rstrip("/") + "/rest/v1/", key)
                    add("database reachable", st == 200, "" if st == 200 else f"Answer {st}. Check the database URL in the site config and that the key is the service role key.")
                    continue
                st, body = http_get(a.site_url.rstrip("/") + f"/rest/v1/{t}?select=*&limit=1", key)
                hint = {0: "Can't reach the database. Check the database URL in the site config.",
                        401: "The key is wrong. Copy the service role key again (Supabase → Project Settings → API Keys).",
                        404: f"Table {t} doesn't exist. Check the table name in the site config (Supabase → Table Editor shows the real names)."}.get(st, f"Answer {st}: {body[:120]}")
                if t in optional:
                    if st != 200:
                        add(f"optional table {t}", True, "Not there, that's fine: this job keeps its log in files under notes/.")
                    continue
                add(f"table {t} readable", st == 200, "" if st == 200 else hint)

            # 2b. every configured column exists
            for spec in a.columns:
                if ":" not in spec:
                    add(f"columns {spec}", False, "Write it as table:col1,col2")
                    continue
                t, cols = spec.split(":", 1)
                cols = [c.strip() for c in cols.split(",") if c.strip()]
                missing = []
                for c in cols:
                    st, body = http_get(a.site_url.rstrip("/") + f"/rest/v1/{t.strip()}?select={c}&limit=1", key)
                    if st != 200:
                        missing.append(c)
                add(f"columns in {t.strip()} exist ({len(cols)} checked)", not missing,
                    "" if not missing else
                    f"These names in the site config aren't columns in {t.strip()}: {', '.join(missing)}. "
                    "Open Supabase → Table Editor → that table, read the real column headers, and put the real names in "
                    "sites/<slug>.yaml (or delete the line if the table has no such column).")

            # 3. photo bucket
            if a.bucket:
                st, body = http_get(a.site_url.rstrip("/") + f"/storage/v1/bucket/{a.bucket}", key)
                public = '"public":true' in body.replace(" ", "")
                add(f"photo bucket {a.bucket} exists and is public", st == 200 and public,
                    "" if st == 200 and public else ("Bucket exists but is private: Supabase → Storage → the bucket → Edit → turn on Public." if st == 200
                                                     else "Bucket missing: Supabase → Storage → New bucket → name it exactly, turn on Public, Save."))

    # 4. scripts run (--help only)
    for path in sorted(glob.glob(os.path.join(a.skills_dir, "*", "*.py"))):
        try:
            r = subprocess.run([sys.executable, path, "--help"], capture_output=True, text=True, timeout=30)
            ok = r.returncode == 0 and "Traceback" not in r.stderr
            add(f"script {os.path.relpath(path, a.skills_dir)} runs", ok, "" if ok else (r.stderr or r.stdout)[-200:])
        except subprocess.TimeoutExpired:
            add(f"script {os.path.relpath(path, a.skills_dir)} runs", False, "Timed out on --help.")

    # 5. mailbox login (read only, reuses inbox-triage's reader)
    if a.mail_host and a.mail_user and a.mail_password_env:
        reader = os.path.join(a.skills_dir, "inbox-triage", "read_inbox.py")
        r = subprocess.run([sys.executable, reader, "--host", a.mail_host, "--user", a.mail_user,
                            "--password-env", a.mail_password_env, "--since-days", "1", "--max", "1"],
                           capture_output=True, text=True, timeout=60)
        ok = '"status": "ok"' in r.stdout or '"status":"ok"' in r.stdout
        add(f"mailbox {a.mail_user} login", ok, "" if ok else
            "Login failed. First check the address is exactly right (open the mailbox, click your profile picture, read it back). "
            "Then make a new app password (myaccount.google.com/apppasswords for Gmail), paste it in hPanel → Environment, Restart, new chat.")

    # 5b. can I read your site?
    if a.website:
        site = a.website if a.website.startswith("http") else "https://" + a.website
        st, blocked = read_site(site)
        if blocked:
            add("can I read your site", False,
                f"blocked_by_security ({blocked}). Use your built-in web reader for small checks; for jobs that read many "
                "pages, offer setup-guides/guides/let-hermes-past-security.md.", warn=True,
                say="Your site's security blocks simple scanners. I'll use my web reader for small checks; for checking "
                    "every page, letting me in is faster and cheaper (2 minutes). Want to do that?")
        else:
            add("can I read your site", st == 200, "" if st == 200 else
                f"Answer {st or 'no response'}. The site may be down or not live yet.",
                say="" if st == 200 else "I couldn't open your website. Is it live yet?")

    # 6. repo pull works
    if os.path.isdir(os.path.join(a.repo, ".git")):
        r = subprocess.run(["git", "-C", a.repo, "fetch", "--dry-run"], capture_output=True, text=True, timeout=60)
        add("repo can pull from GitHub", r.returncode == 0, "" if r.returncode == 0 else
            "Can't reach GitHub. The deploy key may be missing: GitHub → your repo → Settings → Deploy keys.")
    elif os.path.isdir(a.repo):
        add("repo linked to GitHub", False,
            "No .git in the repo folder: settings and notes can't be committed/pushed. Fix (only if the owner wants "
            "backups): connect the folder to their own copy of the repo on GitHub, see README.", warn=True,
            say="Your settings aren't backed up to GitHub yet (optional). Want me to set that up later? "
                "Just say 'back up my settings'.")
    else:
        add("repo cloned", False, f"No repo at {a.repo}. Run the install prompt from the README.")

    print(json.dumps({"all_ok": all(c["ok"] or c.get("warn") for c in checks),
                      "warnings": sum(1 for c in checks if c.get("warn")), "checks": checks}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
