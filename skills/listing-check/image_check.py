#!/usr/bin/env python3
"""Free photo check for listing-check (no API key, no browser).

Finds photos of ONE exact location (via Bing Images), skips untrusted sites, and
downloads small thumbnails so the agent can look at them (vision) to confirm what
kind of place it is, e.g. "a touchless wash bay with no brushes" vs "a hand wash station".

Usage:
    python3 image_check.py "Sunrise Car Wash 120 Main St Springfield IL" \
        --skip yourdomain.com,competitor-directory.com,copycat-site \
        --max 4 --out $DIROPS_REPO/notes/<slug>/tmp/listing-photos

Prints JSON: {query, status, images: [{file, title, source_page, source_domain}], titles_seen}
  status: ok | none | blocked | error

Notes for the agent:
- Look at every downloaded file. Describe what you see in one line each.
- Titles of the source pages are signals too (e.g. a Yelp page titled
  "Sunrise Touchless Car Wash" at that address).
- A photo only counts if its source page is about this exact business/address.
- Thumbnails are small on purpose (cheap to look at). Max 4 per listing.
"""
import argparse
import html
import json
import os
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"


socket.setdefaulttimeout(20)   # backstop: a slow image host can never stall the run


def fetch(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US"})
    return urllib.request.urlopen(req, timeout=timeout).read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--skip", default="", help="comma separated domains or name fragments to ignore")
    ap.add_argument("--max", type=int, default=4)
    ap.add_argument("--max-minutes", type=float, default=2, help="stop trying more images after this many minutes")
    ap.add_argument("--out", default=os.path.join(os.environ.get("DIROPS_REPO", "/data/workspace/directory-ops"), "notes", "tmp", "listing-photos"))
    a = ap.parse_args()

    skip = [s.strip().lower() for s in a.skip.split(",") if s.strip()]
    out = {"query": a.query, "status": "error", "images": [], "titles_seen": []}
    url = "https://www.bing.com/images/search?form=HDRSC2&first=1&q=" + urllib.parse.quote_plus(a.query)
    try:
        page = fetch(url).decode("utf-8", "ignore")
    except Exception as e:  # noqa: BLE001
        out["status"] = "blocked" if "429" in str(e) else "error"
        out["error"] = str(e)[:200]
        print(json.dumps(out))
        return

    os.makedirs(a.out, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", a.query.lower()).strip("-")[:60]
    seen_pages, dead_hosts, t0 = set(), set(), time.time()
    for m in re.finditer(r'class="iusc"[^>]*\sm="([^"]+)"', page):
        try:
            meta = json.loads(html.unescape(m.group(1)))
        except ValueError:
            continue
        purl = meta.get("purl") or ""
        title = (meta.get("t") or "").strip()
        domain = urllib.parse.urlparse(purl).netloc.lower().removeprefix("www.")
        if title and title not in out["titles_seen"]:
            out["titles_seen"].append(title)
        if any(s in domain or s in purl.lower() for s in skip):
            continue
        thumb = meta.get("turl") or meta.get("murl")
        if not thumb or purl in seen_pages or urllib.parse.urlparse(thumb).netloc in dead_hosts:
            continue
        if time.time() - t0 > a.max_minutes * 60:
            out["note"] = "STOP time budget reached: stopped trying more images"
            break
        try:
            data = fetch(thumb, timeout=15)
        except urllib.error.HTTPError:
            continue
        except Exception:  # noqa: BLE001  (connection failure or timeout: skip that host from now on)
            dead_hosts.add(urllib.parse.urlparse(thumb).netloc)
            continue
        if len(data) < 2000:
            continue
        seen_pages.add(purl)
        path = os.path.join(a.out, f"{slug}-{len(out['images']) + 1}.jpg")
        with open(path, "wb") as f:
            f.write(data)
        out["images"].append({"file": path, "title": title, "source_page": purl, "source_domain": domain})
        if len(out["images"]) >= a.max:
            break

    out["titles_seen"] = out["titles_seen"][:12]
    out["status"] = "ok" if out["images"] else "none"
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
