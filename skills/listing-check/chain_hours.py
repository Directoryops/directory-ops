#!/usr/bin/env python3
"""Read opening hours from a chain's own location pages, many at once. Free, standard library only.

Used by listing-check's chain sweep: when several listings of one chain drift the same way, read every location
page of that chain once and propose one bulk fix list.

    python3 chain_hours.py urls.txt [--out hours.jsonl] [--max 300] [--delay 1.5]
    python3 chain_hours.py --url https://brand.example/locations/texas/springfield

urls.txt: one URL per line, optionally "<listing id><TAB><url>". Output, one JSON line per URL:
  {"id": "...", "url": "...", "final_url": "...", "status": "ok|no_hours|failed|blocked_by_security",
   "hours": {"monday": "6AM-7PM", ..., "sunday": "Closed"},   # gmaps_lookup format, feeds hours_style.py render
   "source": "schema openingHours|schema openingHoursSpecification|page data|page text",
   "quote": "<the exact text the hours came from, for the owner>", "note": "..."}

Where it looks, strongest first:
  1. schema.org data in the page (openingHours strings like "Mo-Fr 06:00-19:00", or openingHoursSpecification),
     including copies embedded in the page's script data. Days the schema leaves out are closed (schema rule).
  2. embedded page data shaped {"openingHours": {"0": ["0700","1500"], ...}} (day 0 = Sunday, JavaScript style).
  3. visible text lines like "Monday: 6:00 AM - 7:00 PM" or "Monday Closed".
Never guesses: no hours found = status no_hours. Polite: one request at a time, --delay seconds between them,
at most --max URLs per run (default 300).
"""
import argparse
import html as htmlmod
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; directory-ops/1.0; listing check)"
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
OSM = {"mo": 0, "tu": 1, "we": 2, "th": 3, "fr": 4, "sa": 5, "su": 6}
FULL = {d: i for i, d in enumerate(DAYS)}
BLOCK_MARKERS = ("x-vercel-mitigated", "cf-mitigated", "Just a moment...", "Attention Required! | Cloudflare",
                 "Vercel Security Checkpoint")


def ampm(hhmm):
    m = re.match(r"(\d{1,2}):?(\d{2})", hhmm.strip())
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if h == 24:
        h = 0
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}{':%02d' % mi if mi else ''}{suffix}"


def span(o, c):
    a, b = ampm(o), ampm(c)
    if not a or not b:
        return None
    if o.replace(":", "") in ("0000",) and c.replace(":", "") in ("0000", "2359", "2400"):
        return "Open 24 hours"
    return f"{a}-{b}"


def day_range(spec):
    """'Mo-Fr' / 'Sa,Su' / 'Mo' -> list of day indexes."""
    out = []
    for part in spec.split(","):
        part = part.strip().lower()
        if "-" in part:
            a, b = part.split("-", 1)
            if a[:2] in OSM and b[:2] in OSM:
                i, j = OSM[a[:2]], OSM[b[:2]]
                k = i
                while True:
                    out.append(k)
                    if k == j:
                        break
                    k = (k + 1) % 7
        elif part[:2] in OSM:
            out.append(OSM[part[:2]])
    return out


def from_osm_list(items):
    hours = {}
    for it in items:
        it = str(it).strip()
        if re.fullmatch(r"(?i)mo-su 00:00-(24:00|23:59)|24/7", it):
            return {d: "Open 24 hours" for d in DAYS}
        m = re.match(r"([A-Za-z,\- ]+?)\s+(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})", it)
        if not m:
            continue
        val = span(m.group(2), m.group(3))
        for i in day_range(m.group(1)):
            if val:
                hours[DAYS[i]] = val
    if not hours:
        return None
    return {d: hours.get(d, "Closed") for d in DAYS}


def from_spec(specs):
    hours = {}
    for s in specs if isinstance(specs, list) else [specs]:
        if not isinstance(s, dict):
            continue
        days = s.get("dayOfWeek") or []
        days = days if isinstance(days, list) else [days]
        val = span(str(s.get("opens", "")), str(s.get("closes", "")))
        if not val:
            continue
        for d in days:
            name = str(d).rstrip("/").split("/")[-1].lower()
            if name in FULL:
                hours[name] = val
    if not hours:
        return None
    return {d: hours.get(d, "Closed") for d in DAYS}


def from_index_dict(obj):
    """{"0": ["0700","1500"], "1": [...]} with 0 = Sunday."""
    hours = {}
    for k, v in obj.items():
        if not str(k).isdigit() or int(k) > 6:
            continue
        name = DAYS[(int(k) - 1) % 7]  # 0 (Sunday) -> index 6
        if isinstance(v, list) and len(v) >= 2 and all(isinstance(x, str) for x in v[:2]):
            val = span(v[0][:2] + ":" + v[0][2:], v[1][:2] + ":" + v[1][2:]) if len(v[0]) == 4 else span(v[0], v[1])
            hours[name] = val or "Closed"
        elif not v:
            hours[name] = "Closed"
    if len(hours) < 5:
        return None
    return {d: hours.get(d, "Closed") for d in DAYS}


def balanced(text, start):
    """Return the JSON value ([...] or {...}) starting at text[start]."""
    open_c = text[start]
    close_c = "]" if open_c == "[" else "}"
    depth, i, in_str, esc = 0, start, False, False
    while i < len(text):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == open_c:
            depth += 1
        elif ch == close_c:
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
        i += 1
    return None


def parse(page):
    """-> (hours, source, quote) or (None, None, None)."""
    # unescape script-embedded JSON (\" and &quot;) so schema copies inside page data are readable too
    text = htmlmod.unescape(page).replace('\\\\"', '"').replace('\\"', '"')
    for key, kind in (("openingHoursSpecification", "schema openingHoursSpecification"), ("openingHours", None)):
        for m in re.finditer(r'"%s"\s*:\s*([\[{"])' % key, text):
            st = m.start(1)
            if text[st] == '"':
                raw = re.match(r'"([^"]*)"', text[st:])
                if raw and key == "openingHours":
                    h = from_osm_list(re.split(r"\s*[;,]\s*(?=[A-Z][a-z])", raw.group(1)))
                    if h:
                        return h, "schema openingHours", raw.group(1)[:200]
                continue
            blob = balanced(text, st)
            if not blob:
                continue
            try:
                val = json.loads(blob)
            except json.JSONDecodeError:
                continue
            if key == "openingHoursSpecification":
                h = from_spec(val)
                if h:
                    return h, kind, blob[:300]
            elif isinstance(val, list) and val and isinstance(val[0], str):
                h = from_osm_list(val)
                if h:
                    return h, "schema openingHours", blob[:300]
            elif isinstance(val, list) and val and isinstance(val[0], dict):
                h = from_spec(val)
                if h:
                    return h, "schema openingHoursSpecification", blob[:300]
            elif isinstance(val, dict):
                h = from_index_dict(val)
                if h:
                    return h, "page data", blob[:300]
    # visible text
    vis = re.sub(r"(?is)<script.*?</script>|<style.*?</style>", " ", page)
    vis = htmlmod.unescape(re.sub(r"<[^>]+>", "\n", vis))
    hours, quotes = {}, []
    t = r"(\d{1,2}(?::\d{2})?\s*[AaPp]\.?[Mm]\.?)"
    for m in re.finditer(r"(?i)\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b\s*:?\s*\n?\s*"
                         r"(?:%s\s*(?:-|–|to)\s*%s|(closed))" % (t, t), vis):
        d = m.group(1).lower()
        if d in hours:
            continue
        if m.group(4):
            hours[d] = "Closed"
        else:
            o = re.sub(r"[.\s]", "", m.group(2)).upper()
            c = re.sub(r"[.\s]", "", m.group(3)).upper()
            hours[d] = f"{o.replace(':00', '')}-{c.replace(':00', '')}"
        quotes.append(re.sub(r"\s+", " ", m.group(0)).strip())
    if len(hours) >= 5:
        return {d: hours.get(d, "Closed") for d in DAYS}, "page text", "; ".join(quotes)[:300]
    return None, None, None


# Run guards: a dead or slow site can never stall the run.
socket.setdefaulttimeout(20)
DEAD_HOSTS = set()   # a host that failed to connect or timed out once is skipped for the rest of the run


def fetch(url):
    host = urllib.parse.urlparse(url).netloc.lower()
    if host in DEAD_HOSTS:
        return 0, url, "skipped: this site did not answer earlier in this run", {}
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        r = urllib.request.urlopen(req, timeout=20)
        body = r.read(3_000_000).decode("utf-8", "ignore")
        return r.status, r.geturl(), body, dict(r.headers)
    except urllib.error.HTTPError as e:
        body = e.read(200_000).decode("utf-8", "ignore") if e.fp else ""
        return e.code, url, body, dict(e.headers or {})
    except Exception as e:  # noqa: BLE001  (connection failure or timeout: skip this host from now on)
        DEAD_HOSTS.add(host)
        return 0, url, str(e), {}


def check(url, lid=None):
    code, final, body, headers = fetch(url)
    row = {"id": lid, "url": url, "final_url": final, "status": "failed", "hours": None, "source": None,
           "quote": None, "note": ""}
    hdrs = " ".join(f"{k}: {v}" for k, v in headers.items()).lower()
    if code in (403, 429, 503) and (any(b.lower() in hdrs for b in BLOCK_MARKERS[:2])
                                     or any(b in body for b in BLOCK_MARKERS[2:])):
        row.update(status="blocked_by_security", note="the chain's site turns away simple scanners; read this page with the built-in web reader")
        return row
    if code != 200:
        row["note"] = f"page returned {code}" if code else f"could not load: {body[:120]}"
        return row
    h, src, quote = parse(body)
    if not h:
        row.update(status="no_hours", note="no hours found on this page")
        return row
    row.update(status="ok", hours=h, source=src, quote=quote)
    if final.rstrip("/") != url.rstrip("/"):
        row["note"] = "redirected; check the final page is this exact location"
    return row


def main():
    ap = argparse.ArgumentParser(description="Read opening hours from a chain's own location pages.")
    ap.add_argument("urls", nargs="?", help="file: one URL per line, or '<id>\\t<url>'")
    ap.add_argument("--url", help="check one URL")
    ap.add_argument("--out", help="write JSON lines here (default: print)")
    ap.add_argument("--max", type=int, default=300)
    ap.add_argument("--delay", type=float, default=1.5)
    ap.add_argument("--max-minutes", type=float, default=15, help="stop starting new pages after this many minutes")
    ap.add_argument("--resume", action="store_true", help="with --out: keep earlier results and skip URLs already in it")
    a = ap.parse_args()
    if getattr(a, "out", None):  # create the output folder (notes/<site>/...) if it is new
        import os as _os
        _os.makedirs(_os.path.dirname(_os.path.abspath(a.out)), exist_ok=True)
    items = []
    if a.url:
        items = [(None, a.url)]
    elif a.urls:
        for line in open(a.urls):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            items.append((parts[0], parts[1]) if len(parts) > 1 else (None, parts[0]))
    else:
        ap.error("give a urls file or --url")
    if len(items) > a.max:
        print(json.dumps({"warning": f"{len(items)} URLs, checking the first {a.max}; run again for the rest"}), file=sys.stderr)
        items = items[:a.max]
    if a.resume and a.out and os.path.exists(a.out):
        done = set()
        for line in open(a.out):
            try:
                done.add(json.loads(line)["url"])
            except (ValueError, KeyError):
                pass
        items = [(i, u) for i, u in items if u not in done]
    out = open(a.out, "a" if a.resume else "w") if a.out else sys.stdout
    counts = {}
    t0 = time.time()
    for n, (lid, url) in enumerate(items):
        if time.time() - t0 > a.max_minutes * 60:
            print(f"STOP time budget reached: {len(items) - n} items not checked (rerun with --resume to continue)",
                  file=sys.stderr)
            counts["not_checked"] = len(items) - n
            break
        if n:
            time.sleep(a.delay)
        row = check(url, lid)
        counts[row["status"]] = counts.get(row["status"], 0) + 1
        out.write(json.dumps(row) + "\n")
        out.flush()
    if a.out:
        out.close()
        print(json.dumps({"checked": len(items) - counts.get("not_checked", 0), **counts, "out": a.out}))


if __name__ == "__main__":
    sys.exit(main())
