#!/usr/bin/env python3
"""Test each listing's stored website link and propose a clean one when it's broken. Free, standard library only.

    python3 link_check.py links.txt [--out links.jsonl] [--max 300] [--delay 1.0]
    python3 link_check.py --url "https://brand.example/locations/texas/springfield?utm_source=google"

links.txt: one URL per line, or "<listing id><TAB><url>". One JSON line per link:
  {"id", "url", "status", "final_url", "code", "suggest": {"url", "why"} or null, "note"}

status (what the visitor gets when they click; redirects are followed):
  ok              the link opens a page for this location (200, not the homepage, not a list of locations)
  tracking_tags   works, but carries tracking text (?utm_source=...); suggest the same link without it (cosmetic)
  glued_tracking  tracking text was glued onto the address without "?" (".../springfield-northutm_source..."), usually broken
  broken          404, 410, other error, or the site could not be reached
  homepage        lands on the brand's homepage, not this location (for chains: when 2+ links share a domain, or --chain)
  index_page      lands on a list page above the location (e.g. /locations/florida) instead of the location itself
  blocked_by_security  the site turns away simple scanners (read it with the built-in web reader instead)

suggest: a cleaned link (tracking text removed) that was tested and opens a real location page. When no clean link
works, suggest is null: use the location page you found during the check (chain sweep final_url, the business's own
page, or Google's website when usable) and test it with --url before proposing it.
"""
import argparse
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; directory-ops/1.0; +https://github.com/Directoryops/directory-ops)"
BLOCK_MARKERS = ("x-vercel-mitigated", "cf-mitigated", "Just a moment...", "Attention Required! | Cloudflare",
                 "Vercel Security Checkpoint")
TRACK_PARAMS = re.compile(r"^(utm_|gclid$|fbclid$|msclkid$|mc_|_ga$|ref$|y_source$)", re.I)
GLUED = re.compile(r"(utm_?source|utm_?medium|utm_?campaign|utm_?content|utm_?term|gclid|fbclid)", re.I)
HOME_PATHS = {"", "/", "/en", "/en/", "/en-us", "/en-us/", "/home", "/index.html"}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


# Run guards: a dead or slow site can never stall the run.
socket.setdefaulttimeout(20)
DEAD_HOSTS = set()   # hosts that failed to connect or timed out (after the one retry): skipped for the rest of the run
SKIPPED = "skipped: this site did not answer earlier in this run"


def _host(url):
    return urllib.parse.urlsplit(url).netloc.lower()


def _get(url):
    if _host(url) in DEAD_HOSTS:
        return 0, SKIPPED, {}
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        r = _OPENER.open(req, timeout=20)
        return r.status, r.read(150_000).decode("utf-8", "ignore"), dict(r.headers)
    except urllib.error.HTTPError as e:
        body = e.read(50_000).decode("utf-8", "ignore") if e.fp else ""
        return e.code, body, dict(e.headers or {})
    except Exception as e:  # noqa: BLE001
        return 0, str(e), {}


def fetch(url, tries=2):
    """GET with redirects followed by hand (301/302/303/307/308, up to 6 hops). One retry on a network error."""
    for attempt in range(tries):
        cur = url
        for _ in range(7):
            code, body, headers = _get(cur)
            loc = headers.get("Location") or headers.get("location")
            if code in (301, 302, 303, 307, 308) and loc:
                cur = urllib.parse.urljoin(cur, loc)
                continue
            break
        if code or body == SKIPPED:
            return code, cur, body, headers
        if attempt == tries - 1:
            DEAD_HOSTS.add(_host(cur))   # connection failure or timeout twice: don't wait on this site again
            return code, cur, body, headers
        time.sleep(2)
    return code, cur, body, headers


def strip_tracking(url):
    """Remove glued tracking text from the path and tracking params from the query. Returns (clean_url, glued?)."""
    p = urllib.parse.urlsplit(url.strip())
    path, glued = p.path, False
    m = GLUED.search(path)
    if m:
        path, glued = path[:m.start()].rstrip("-_/,") or "/", True
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True) if not TRACK_PARAMS.match(k)]
    clean = urllib.parse.urlunsplit((p.scheme or "https", p.netloc, path, urllib.parse.urlencode(q), ""))
    return clean, glued


def where_it_lands(url, final, code, body, headers, chain=False):
    hdrs = " ".join(f"{k}: {v}" for k, v in headers.items()).lower()
    if code in (403, 429, 503) and (any(b.lower() in hdrs for b in BLOCK_MARKERS[:2])
                                     or any(b in body for b in BLOCK_MARKERS[2:])):
        return "blocked_by_security"
    if code != 200:
        return "broken"
    want = urllib.parse.urlsplit(url).path.rstrip("/")
    got = urllib.parse.urlsplit(final).path.rstrip("/")
    if got.lower() in HOME_PATHS and (want.lower() not in HOME_PATHS or chain):
        return "homepage"   # chain listings must open their own location page, not the brand's homepage
    if want and got != want and want.lower().startswith(got.lower() + "/"):
        return "index_page"   # redirected UP the address (/locations/florida/jacksonville -> /locations/florida)
    if re.search(r"(page not found|404 error|we can.t find that page|page you requested)", body[:20000], re.I) \
            and len(body) < 60000:
        return "broken"       # "soft 404": 200 with a not-found page
    return "ok"


def check(url, lid=None, delay=0.0, chain=False):
    url = (url or "").strip()
    row = {"id": lid, "url": url, "status": "broken", "final_url": None, "code": None, "suggest": None, "note": ""}
    if not url:
        row["note"] = "no link stored"
        return row
    if not re.match(r"https?://", url, re.I):
        url = "https://" + url
    code, final, body, headers = fetch(url)
    if body == SKIPPED:
        row.update(status="not_checked", note="this site did not answer earlier in this run; check it again later")
        return row
    row.update(final_url=final, code=code, status=where_it_lands(url, final, code, body, headers, chain))
    clean, glued = strip_tracking(url)
    if row["status"] == "blocked_by_security":
        row["note"] = "the site turns away simple scanners; open the link with the built-in web reader"
        return row
    if glued:
        row["status"] = "glued_tracking" if row["status"] != "ok" else "tracking_tags"
    elif row["status"] == "ok" and clean != url:
        row["status"] = "tracking_tags"
    if row["status"] == "ok":
        return row
    if clean != url:
        time.sleep(delay)
        c2, f2, b2, h2 = fetch(clean)
        if where_it_lands(clean, f2, c2, b2, h2) == "ok":
            why = ("removed tracking text glued onto the address" if glued
                   else "removed tracking text (cosmetic, the old link works)")
            row["suggest"] = {"url": f2 if f2 and f2.rstrip("/") != clean.rstrip("/") else clean, "why": why}
    if not row["suggest"] and row["status"] != "tracking_tags":
        row["note"] = ("no clean link works; propose the location page you found during the check "
                       "(test it with --url first)")
    return row


def main():
    ap = argparse.ArgumentParser(description="Test listing website links and suggest clean ones.")
    ap.add_argument("links", nargs="?", help="file: one URL per line, '<id>\\t<url>', or db.py select JSON (.json)")
    ap.add_argument("--column", default="website", help=".json input: the website column (default website)")
    ap.add_argument("--id-field", default="id", help=".json input: the id column (default id)")
    ap.add_argument("--url", help="check one link")
    ap.add_argument("--out", help="write JSON lines here (default: print)")
    ap.add_argument("--max", type=int, default=300)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--chain", action="store_true", help="these are chain locations: a homepage link is wrong "
                    "(automatic in a file when 2+ links share one domain)")
    ap.add_argument("--max-minutes", type=float, default=20, help="stop starting new links after this many minutes")
    ap.add_argument("--resume", action="store_true", help="with --out: keep earlier results and skip links already in it")
    a = ap.parse_args()
    if a.url:
        items = [(None, a.url)]
    elif a.links and a.links.endswith(".json"):
        data = json.load(open(a.links))
        rows = data.get("rows", data.get("data", [])) if isinstance(data, dict) else data
        items = [(str(r.get(a.id_field)), str(r[a.column]).strip()) for r in rows
                 if isinstance(r, dict) and r.get(a.column) and str(r[a.column]).strip()]
    elif a.links:
        items = []
        for line in open(a.links):
            line = line.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split("\t")
            items.append((parts[0], parts[1]) if len(parts) > 1 else (None, parts[0]))
    else:
        ap.error("give a links file or --url")
    if len(items) > a.max:
        print(json.dumps({"warning": f"{len(items)} links, checking the first {a.max}; run again for the rest"}),
              file=sys.stderr)
        items = items[:a.max]
    doms = {}
    for _, u in items:
        d = urllib.parse.urlsplit(u if "://" in u else "https://" + u).netloc.lower().removeprefix("www.")
        doms[d] = doms.get(d, 0) + 1
    if a.resume and a.out and os.path.exists(a.out):
        done = set()
        for line in open(a.out):
            try:
                r = json.loads(line)
                if r.get("status") != "not_checked":
                    done.add(r["url"])
            except (ValueError, KeyError):
                pass
        items = [(i, u) for i, u in items if (u if re.match(r"https?://", u, re.I) else "https://" + u) not in done
                 and u not in done]
    out = open(a.out, "a" if a.resume else "w") if a.out else sys.stdout
    counts = {}
    t0 = time.time()
    for n, (lid, url) in enumerate(items):
        if time.time() - t0 > a.max_minutes * 60:
            print(f"STOP time budget reached: {len(items) - n} items not checked (rerun with --resume to continue)",
                  file=sys.stderr)
            counts["not_checked"] = counts.get("not_checked", 0) + len(items) - n
            break
        if n:
            time.sleep(a.delay)
        d = urllib.parse.urlsplit(url if "://" in url else "https://" + url).netloc.lower().removeprefix("www.")
        row = check(url, lid, a.delay, chain=a.chain or doms.get(d, 0) >= 2)
        counts[row["status"]] = counts.get(row["status"], 0) + 1
        out.write(json.dumps(row) + "\n")
        out.flush()
    if a.out:
        out.close()
        print(json.dumps({"checked": len(items) - counts.get("not_checked", 0), **counts, "out": a.out}))


if __name__ == "__main__":
    sys.exit(main())
