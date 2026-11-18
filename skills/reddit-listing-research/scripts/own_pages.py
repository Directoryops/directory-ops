"""Step 9c. Read the DIRECTORY'S OWN listing page for each pilot listing, so you can see (a) which detail labels the
page already shows empty (fill targets) and (b) template sentences that contradict what the business's own site says.
Free, no AI. Run it from the research folder after Step 10 (staging/ exists) or after fetch_sites.py.
Usage: python3 scripts/own_pages.py --site https://www.example.com
       python3 scripts/own_pages.py --site https://www.example.com --url 123=https://www.example.com/listing/abc
Finds each listing's page in the site's sitemap by matching its name + city words (or use --url ID=URL),
saves the page text to sites/_own/<id>.txt, then prints, per field in output/fields.json, the page lines that mention
that field's label words. "blocked_by_security" = the site's security wall answered: read the page with your
built-in web reader and save its text in sites/_own/<id>.txt yourself."""
import argparse, csv, json, os, re, socket, time, urllib.error, urllib.request
socket.setdefaulttimeout(20)   # backstop: a slow site can never stall the run
DEAD_HOSTS = set()             # failed to connect or timed out once: skipped for the rest of the run
from html.parser import HTMLParser
from urllib.parse import urlparse
import common  # noqa: F401  (prints this script's help on --help)

UA = "Mozilla/5.0 (compatible; directory-ops/1.0; +https://github.com/Directoryops/directory-ops)"
STOP = {"the", "and", "of", "in", "at", "for", "a", "an", "inc", "llc", "co", "center", "centers", "tx", "ca", "fl"}


class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.out, self.skip = [], 0
    def handle_starttag(self, t, a):
        if t in ("script", "style", "noscript", "svg"): self.skip += 1
    def handle_endtag(self, t):
        if t in ("script", "style", "noscript", "svg") and self.skip: self.skip -= 1
        if t in ("p", "div", "li", "tr", "h1", "h2", "h3", "h4", "br", "section", "dt", "dd", "span"): self.out.append("\n")
    def handle_data(self, d):
        if not self.skip: self.out.append(d)


def fetch(url, n=3_000_000):
    host = urlparse(url).netloc
    if host in DEAD_HOSTS:
        raise ValueError("the site did not answer earlier in this run")
    if time.time() > DEADLINE[0]:
        raise ValueError("time budget reached")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        return urllib.request.urlopen(req, timeout=20).read(n).decode("utf8", "ignore")
    except urllib.error.HTTPError as e:
        h = {k.lower(): str(v).lower() for k, v in (e.headers or {}).items()}
        if e.code in (403, 429, 503) and ("x-vercel-mitigated" in h or "cf-mitigated" in h or "cloudflare" in h.get("server", "")):
            raise ValueError("blocked_by_security") from None
        raise
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError):
        DEAD_HOSTS.add(host)
        raise


def words(s):
    return [w for w in re.findall(r"[a-z0-9]+", (s or "").lower()) if w not in STOP and len(w) > 1]


def sitemap_urls(site):
    urls, todo, seen = [], [site.rstrip("/") + "/sitemap.xml"], set()
    while todo and len(seen) < 25:
        sm = todo.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        try:
            locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", fetch(sm))
        except Exception:
            continue
        todo += [u for u in locs if u.endswith(".xml")]
        urls += [u for u in locs if not u.endswith(".xml")]
    return urls


ap = argparse.ArgumentParser()
ap.add_argument("--site", required=True)
ap.add_argument("--url", action="append", default=[], help="ID=URL when the sitemap match is wrong or missing")
ap.add_argument("--max-minutes", type=float, default=10, help="stop fetching after this many minutes")
a = ap.parse_args()
DEADLINE = [time.time() + a.max_minutes * 60]
given = dict(x.split("=", 1) for x in a.url)
listings = {r["id"]: r for r in csv.DictReader(open("data/listings.csv", newline=""))}
ids = [f[:-5] for f in sorted(os.listdir("staging")) if f.endswith(".json")] if os.path.isdir("staging") else []
ids = ids or [f[:-4] for f in sorted(os.listdir("sites")) if f.endswith(".txt") and not f.startswith("_")]
fields = json.load(open("output/fields.json")) if os.path.exists("output/fields.json") else []
urls = [] if all(i in given for i in ids) else sitemap_urls(a.site)
print(f"{len(ids)} pilot listings | {len(urls)} URLs in the sitemap")
os.makedirs("sites/_own", exist_ok=True)
page_lines = {}   # id -> set of normalized lines, to find site-wide template lines
for n_lid, lid in enumerate(ids):
    if time.time() > DEADLINE[0]:
        print(f"\nSTOP time budget reached: {len(ids) - n_lid} items not checked (rerun to continue)")
        break
    r = listings.get(lid, {})
    want = set(words(r.get("name")) + words((r.get("address") or "").split(",")[1] if "," in (r.get("address") or "") else ""))
    url = given.get(lid)
    if not url and want:
        best = max(urls, key=lambda u: len(want & set(words(urlparse(u).path))), default=None)
        if best and len(want & set(words(urlparse(best).path))) >= max(2, int(0.6 * len(want))):
            url = best
    if not url:
        print(f"\n[{lid}] {r.get('name')}: NOT FOUND in the sitemap. Find its page on the site and rerun with --url {lid}=<url>")
        continue
    try:
        p = Text(); p.feed(fetch(url))
        text = re.sub(r"\n\s*\n+", "\n", re.sub(r"[ \t]+", " ", "".join(p.out))).strip()
    except Exception as e:
        print(f"\n[{lid}] {url}: {e if isinstance(e, ValueError) else type(e).__name__}. Read it with your web reader "
              f"and save the text to sites/_own/{lid}.txt")
        continue
    open(f"sites/_own/{lid}.txt", "w").write(f"=== PAGE: {url}\n{text[:20000]}\n")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    page_lines[lid] = {re.sub(r"\s+", " ", l) for l in lines if len(l.split()) >= 4}
    print(f"\n[{lid}] {r.get('name')} -> {url} ({len(text)} chars)")
    for f in fields:
        keys = [w for w in words(f.get("label")) if len(w) > 3]
        hits = [l for l in lines if any(k in l.lower() for k in keys)][:4]
        print(f"  {f.get('label')}: " + (" | ".join(h[:140] for h in hits) if hits else "(not on the page)"))
    time.sleep(1)
# Template lines: the same sentence on 2+ sampled pages is written by the site's template, so it shows on (almost)
# every page of that type. One wrong template line touches every page: report these FIRST.
if len(page_lines) >= 2:
    from collections import Counter
    cnt = Counter(l for ls in page_lines.values() for l in ls)
    FACTY = re.compile(r"\d|hour|minute|day|week|month|year|walk|appointment|pay|bonus|card|fee|age|weigh|bring|id\b", re.I)
    tmpl = [(c, l) for l, c in cnt.items() if c >= 2 and FACTY.search(l) and len(l) < 300
            and not re.match(r"^[+©]|.*©", l)]
    tmpl.sort(key=lambda x: (-x[0], x[1]))
    print(f"\nTEMPLATE LINES (same sentence on 2+ of {len(page_lines)} sampled pages = appears on every page of this type). "
          "Check each against the VERIFIED values by MEANING; a wrong one is the biggest page fix (it touches every page):")
    for c, l in tmpl[:25]:
        print(f"  [{c}/{len(page_lines)} pages] {l[:200]}")
print("\nNEXT: for each listing, (1) labels shown with no value = fill targets; (2) any sentence that disagrees with a "
      "VERIFIED value from the business's own site = a fix for the owner's page template (quote both).")
