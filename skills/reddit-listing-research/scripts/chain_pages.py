"""Step 9b. Chains: read each chain's company pages ONCE (FAQ, first visit, requirements, payment, how it works).
Many listings that share one website (a chain) have thin location pages; the facts live on company pages.
Usage: python3 scripts/chain_pages.py                (chains with 5+ listings, up to 8 pages each)
       python3 scripts/chain_pages.py --min 3 --max-pages 10
Input: data/listings.csv (id,name,website). Output: sites/_chains/<domain>.txt with "=== PAGE: <url>" headers,
and sites/_chains/chains.json: {domain: {"chain": "<name>", "listings": N, "pages": [...]}}. Free, no AI.
It also saves 2 OTHER locations' pages of each chain to sites/_chains/<domain>.siblings.txt, so the checker can tell
chain boilerplate (the same sentence on every location page) from a fact about one location.
A value quoted from these pages is a COMPANY fact: in staging write "scope": "chain" (see Step 10 rule 7).
Never use them for amounts that change by location or month (prices, pay, bonuses)."""
import argparse, csv, json, os, re, socket, time, urllib.error, urllib.request
socket.setdefaulttimeout(15)   # a slow site can never hang the run
from collections import Counter, defaultdict
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from common import load_config

ap = argparse.ArgumentParser()
ap.add_argument("--min", type=int, default=5)
ap.add_argument("--max-pages", type=int, default=8)
ap.add_argument("--max-minutes", type=float, default=10, help="stop starting new chains after this many minutes (biggest chains go first)")
ap.add_argument("--max-chains", type=int, default=12)
a = ap.parse_args()
try:
    extra = [w.lower() for w in load_config().get("page_hint_words", [])]
except Exception:
    extra = []
HINTS = ["faq", "question", "first", "new-donor", "new donor", "what-to-expect", "what to expect", "expect",
         "requirement", "eligib", "qualif", "payment", "compensation", "how-it-works", "how it works",
         "getting-started", "get started", "process", "bring", "donor", "donating", "pricing", "price",
         "services", "visit", "appointment"] + extra
UA = "Mozilla/5.0 (compatible; directory-ops/1.0; +https://github.com/Directoryops/directory-ops)"


class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.out, self.links, self.skip, self.a = [], [], 0, None
    def handle_starttag(self, t, at):
        if t in ("script", "style", "noscript", "svg"): self.skip += 1
        if t == "a": self.a = [dict(at).get("href") or "", ""]
    def handle_endtag(self, t):
        if t in ("script", "style", "noscript", "svg") and self.skip: self.skip -= 1
        if t == "a" and self.a: self.links.append(self.a); self.a = None
        if t in ("p", "div", "li", "tr", "h1", "h2", "h3", "h4", "br", "section", "dt", "dd"): self.out.append("\n")
    def handle_data(self, d):
        if not self.skip:
            self.out.append(d)
            if self.a is not None: self.a[1] += d


CHAIN_DEADLINE = [0.0]   # set per chain: no new fetches after it
DEAD_HOSTS = set()       # a host that failed to connect once is skipped for the rest of the run


def get(url):
    host = urlparse(url).netloc
    if host in DEAD_HOSTS:
        raise OSError("host did not answer earlier")
    if CHAIN_DEADLINE[0] and time.time() > CHAIN_DEADLINE[0]:
        raise TimeoutError("chain time limit reached")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        raw = urllib.request.urlopen(req, timeout=15).read(2_000_000).decode("utf8", "ignore")
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
        if not isinstance(e, urllib.error.HTTPError):
            DEAD_HOSTS.add(host)
        raise
    p = Text(); p.feed(raw)
    return re.sub(r"\n\s*\n+", "\n", re.sub(r"[ \t]+", " ", "".join(p.out))).strip(), p.links


def chain_name(names):
    """The words most listing names of this chain start with ("CSL Plasma Dallas, TX" -> "CSL Plasma")."""
    split = [re.split(r"\s+", n.strip()) for n in names if n.strip()]
    best = ""
    for k in range(1, 5):
        c = Counter(" ".join(s[:k]) for s in split if len(s) >= k).most_common(1)
        if c and c[0][1] >= 0.6 * len(split):
            best = c[0][0]
    return re.sub(r"[,\-|]+$", "", best).strip()


rows = list(csv.DictReader(open("data/listings.csv", newline="")))
by_dom = defaultdict(list)
for r in rows:
    d = urlparse((r.get("website") or "").strip()).netloc.lower().replace("www.", "")
    if d:
        by_dom[d].append(r)
chains = {d: rs for d, rs in by_dom.items() if len(rs) >= a.min}
os.makedirs("sites/_chains", exist_ok=True)
index = json.load(open("sites/_chains/chains.json")) if os.path.exists("sites/_chains/chains.json") else {}
print(f"{len(chains)} chains with {a.min}+ listings (covering {sum(len(v) for v in chains.values())} of {len(rows)} listings)")
T0 = time.time()
for i, (d, rs) in enumerate(sorted(chains.items(), key=lambda x: -len(x[1]))):
    if i >= a.max_chains or time.time() - T0 > a.max_minutes * 60:
        print(f"STOP time/chain budget reached: {len(chains) - i} smaller chains skipped (rerun with --max-minutes to add them).")
        break
    CHAIN_DEADLINE[0] = time.time() + 120   # at most 2 minutes per chain
    name = chain_name([r.get("name", "") for r in rs]) or d
    sib_path = f"sites/_chains/{d}.siblings.txt"
    if not os.path.exists(sib_path):
        # 2 other location pages of this chain (not the pilot ones) -> boilerplate detection in check_extractions.py
        sib = []
        for r in rs:
            if len(sib) >= 2:
                break
            u = (r.get("website") or "").strip()
            if not u or os.path.exists(f"sites/{r['id']}.txt") or urlparse(u).path.strip("/") == "":
                continue
            try:
                sib.append((u, get(u)[0]))
            except Exception:
                pass
            time.sleep(1)
        with open(sib_path, "w") as f:
            for u, t in sib:
                f.write(f"=== PAGE: {u}\n{t[:12000]}\n\n")
    if d in index and os.path.exists(f"sites/_chains/{d}.txt"):
        print(f"skip {d} ({name}): already read")
        continue
    home = f"https://www.{d}/" if not d.count(".") > 1 else f"https://{d}/"
    pages, seen = [], set()
    try:
        text, links = get(home)
        pages.append((home, text)); seen.add(home.rstrip("/"))
    except Exception as e:
        try:
            home = f"https://{d}/"
            text, links = get(home)
            pages.append((home, text)); seen.add(home.rstrip("/"))
        except Exception as e2:
            print(f"FAIL {d} ({name}): {type(e2).__name__}. Read its FAQ with your built-in web reader instead.")
            continue
    SKIP = re.compile(r"cookie|privacy|terms|accessib|login|sign-?in|register|registration|career|jobs?\b|/blog/|/news/|/es/|/fr/|opt-out|non-discrimination|\.(pdf|jpg|png)$", re.I)
    def sitemap_links():
        """Menus built by JavaScript hide links: read the site's sitemap instead."""
        out = []
        for sm in (f"https://www.{d}/sitemap.xml", f"https://{d}/sitemap.xml"):
            try:
                req = urllib.request.Request(sm, headers={"User-Agent": UA})
                xml = urllib.request.urlopen(req, timeout=15).read(3_000_000).decode("utf8", "ignore")
            except Exception:
                continue
            locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)
            subs = [u for u in locs if u.endswith(".xml")][:5]
            for u in subs:
                try:
                    req = urllib.request.Request(u, headers={"User-Agent": UA})
                    locs += re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", urllib.request.urlopen(req, timeout=15).read(3_000_000).decode("utf8", "ignore"))
                except Exception:
                    pass
            out = [[u, ""] for u in locs if not u.endswith(".xml")]
            if out:
                break
        return out
    scored = []
    for href, label in links + (sitemap_links() if len(links) < 40 or not any(
            any(h in (h2 + l).lower() for h in ("faq", "first", "expect", "requirement")) for h2, l in links) else []):
        u = urljoin(home, href).split("#")[0].split("?")[0]
        host = urlparse(u).netloc.lower().replace("www.", "")
        if host != d or u.rstrip("/") in seen or SKIP.search(u) or re.search(r"/(locations?|center|centers|find)[/-]", u.lower()):
            continue
        hay = (u + " " + label).lower()
        hits = sum(h in hay for h in HINTS)
        if hits:
            scored.append((-hits, u)); seen.add(u.rstrip("/"))
    for _, u in sorted(scored)[: a.max_pages - 1]:
        try:
            pages.append((u, get(u)[0]))
        except Exception:
            pass
        time.sleep(1)
    with open(f"sites/_chains/{d}.txt", "w") as f:
        for u, t in pages:
            f.write(f"=== PAGE: {u}\n{t[:15000]}\n\n")
    index[d] = {"chain": name, "listings": len(rs), "pages": [u for u, _ in pages]}
    print(f"ok   {d} ({name}, {len(rs)} listings): {len(pages)} company pages")
    time.sleep(1)
json.dump(index, open("sites/_chains/chains.json", "w"), indent=1)
print("DONE -> sites/_chains/. Read these once; a fact found here applies to every location of that chain "
      "(label it 'company policy, all <chain> locations'), never amounts that vary by location or month.")
