"""Step 9/10. Download the text of each business's own website. Free (no AI, no credits).
Input: data/listings.csv with at least the columns: id,name,website
Usage: python3 scripts/fetch_sites.py --limit 5        (pilot)   [--max-minutes 20: stop starting new sites after N minutes; rerun continues]
       python3 scripts/fetch_sites.py                  (all listings)
For each listing: fetches the homepage, then up to (max_pages_per_site - 1) internal pages whose
link text or URL contains a hint word (pricing, services, faq, about, hours, plus page_hint_words
from research.json). Saves plain text to sites/<id>.txt with a "=== PAGE: <url>" header per page.
Skips listings already fetched. Writes sites/_failed.txt for sites that blocked or errored.
"blocked_by_security_<vercel|cloudflare|other>" = the site's security wall answered, not the page: read that site
with your built-in web reader instead and save its text in the same sites/<id>.txt format (=== PAGE: <url>)."""
import csv, json, os, re, socket, sys, time, urllib.error, urllib.request
socket.setdefaulttimeout(20)   # backstop: a slow site can never stall the run
DEAD_HOSTS = set()             # failed to connect or timed out once: skipped for the rest of the run
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from common import load_config

cfg = load_config()
MAX_PAGES = cfg["limits"]["max_pages_per_site"]
HINTS = ["pric", "cost", "rate", "fee", "package", "service", "faq", "question", "about",
         "hour", "contact", "location", "plan", "menu"] + [w.lower() for w in cfg.get("page_hint_words", [])]
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



class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.out, self.links, self.skip, self.a = [], [], 0, None
    def handle_starttag(self, t, a):
        if t in ("script", "style", "noscript", "svg"): self.skip += 1
        if t == "a": self.a = [dict(a).get("href") or "", ""]
    def handle_endtag(self, t):
        if t in ("script", "style", "noscript", "svg") and self.skip: self.skip -= 1
        if t == "a" and self.a: self.links.append(self.a); self.a = None
        if t in ("p", "div", "li", "tr", "h1", "h2", "h3", "h4", "br", "section"): self.out.append("\n")
    def handle_data(self, d):
        if not self.skip:
            self.out.append(d)
            if self.a is not None: self.a[1] += d


def get(url, first=False):
    host = urlparse(url).netloc
    if host in DEAD_HOSTS:
        raise ValueError("site_did_not_answer_earlier_this_run")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        raw = urllib.request.urlopen(req, timeout=20).read(2_000_000).decode("utf8", "ignore")
    except urllib.error.HTTPError as e:
        try:
            body = e.read(20000).decode("utf8", "ignore")
        except Exception:
            body = ""
        b = security_block(e.code, dict(e.headers or {}), body, first=first)
        if b:
            raise ValueError(f"blocked_by_security_{b}") from None
        raise
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError):
        DEAD_HOSTS.add(host)
        raise
    p = Text(); p.feed(raw)
    text = re.sub(r"\n\s*\n+", "\n", re.sub(r"[ \t]+", " ", "".join(p.out))).strip()
    return text, p.links


limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
# --max-minutes N = stop starting new sites after N minutes (default 20); a rerun continues where it stopped
max_minutes = float(sys.argv[sys.argv.index("--max-minutes") + 1]) if "--max-minutes" in sys.argv else 20.0
T0 = time.time()
rows = list(csv.DictReader(open("data/listings.csv")))
rows = [r for r in rows if (r.get("website") or "").startswith("http")]
# --limit N = stop after N usable sites (failed or empty sites don't count toward the pilot)
os.makedirs("sites", exist_ok=True)
failed = []
usable = sum(1 for r in rows if os.path.exists(f"sites/{r['id']}.txt"))
old_failed = set(open("sites/_failed.txt").read().splitlines()) if os.path.exists("sites/_failed.txt") else set()
for n_row, r in enumerate(rows):
    if limit and usable >= limit:
        break
    path = f"sites/{r['id']}.txt"
    if os.path.exists(path):
        continue
    if time.time() - T0 > max_minutes * 60:
        left = sum(1 for x in rows[n_row:] if not os.path.exists(f"sites/{x['id']}.txt"))
        print(f"STOP time budget reached: {left} items not checked (rerun to continue)")
        break
    try:
        home = r["website"].strip()
        text, links = get(home, first=True)
        pages, seen = [(home, text)], {home.rstrip("/")}
        host = urlparse(home).netloc
        for href, label in links:
            if len(pages) >= MAX_PAGES:
                break
            u = urljoin(home, href).split("#")[0]
            if urlparse(u).netloc != host or u.rstrip("/") in seen:
                continue
            if any(h in (u + " " + label).lower() for h in HINTS):
                seen.add(u.rstrip("/"))
                try:
                    pages.append((u, get(u)[0]))
                except Exception:
                    pass
                time.sleep(1)
        if sum(len(t) for _, t in pages) < 300:
            raise ValueError("page_needs_javascript_or_empty")
        with open(path, "w") as f:
            for u, t in pages:
                f.write(f"=== PAGE: {u}\n{t[:12000]}\n\n")
        usable += 1
        print(f"ok   {r['id']} {r['name'][:40]}: {len(pages)} pages")
    except Exception as e:
        why = str(e) if isinstance(e, ValueError) else type(e).__name__
        failed.append(f"{r['id']},{r['website']},{why}")
        if failed[-1] not in old_failed:   # saved as it goes, so a stopped run keeps its list
            with open("sites/_failed.txt", "a") as ff:
                ff.write(failed[-1] + "\n")
            old_failed.add(failed[-1])
        print(f"FAIL {r['id']} {r['name'][:40]}: {why}")
    time.sleep(1)
blocked = sum(1 for x in failed if "blocked_by_security" in x)
print(f"DONE. {len(failed)} failed (see sites/_failed.txt)"
      + (f"; {blocked} of them have security that blocks automated visitors: read those with your built-in web reader "
         "(copy exact quotes into sites/<id>.txt with '=== PAGE: <url>' headers)" if blocked else ""))
