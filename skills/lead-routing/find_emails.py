#!/usr/bin/env python3
"""Find each business's own published email address on its own website, so lead routing has someone to email.
Free (no AI reading, no paid tools): a quick, polite look at each site's homepage and up to 4 contact-like pages.
Writes NOTHING to the database. Results go to a JSON lines file; the owner approves, then the skill saves them
through directory-db/db.py.

    python3 find_emails.py listings.json --out emails.jsonl [--limit 100] [--skip-done]
        [--id id --name name --website website]

listings.json = output of `db.py select --all` ({"rows": [...]}) or a plain JSON list; a .csv file also works.

Per listing it prints one JSON line:
  {"id", "name", "website", "status", "best_email", "emails": [{"email", "source_url", "rank", "mx_ok"}],
   "contact_form_url", "social": [...], "checked_at"}
status: found | contact_form_only | social_only | no_website | site_failed | needs_browser | blocked_by_security
        (blocked_by_security = the site's security wall answered, not the page; read that site with your built-in
        web reader instead, or for the owner's OWN site offer setup-guides/guides/let-hermes-past-security.md)
At the end it prints a plain summary line for the owner.

Rules built in (the skill repeats them): only addresses published on the business's OWN website; never guessed
patterns (firstname@...), never other directories or bought lists; every email keeps the page it came from.
"""
import argparse
import csv
import datetime
import html
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from check_lead import has_mx  # DNS over HTTPS MX lookup, shared with the lead checker
except Exception:  # noqa: BLE001
    def has_mx(domain):
        return None

UA = "Mozilla/5.0 (compatible; directory-ops/1.0; +https://github.com/Directoryops/directory-ops)"


class BlockedError(Exception):
    """The site's security (Vercel/Cloudflare challenge, Sucuri, Wordfence, Akamai) answered instead of the page."""


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
EMAIL = re.compile(r"[A-Za-z0-9._%+'-]+@(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,24}")
OBFUSCATED = re.compile(
    r"([A-Za-z0-9._%+'-]+)\s*(?:\[\s*at\s*\]|\(\s*at\s*\)|\{\s*at\s*\}|\s+at\s+)\s*"
    r"([A-Za-z0-9-]+(?:\s*(?:\[\s*dot\s*\]|\(\s*dot\s*\)|\{\s*dot\s*\}|\s+dot\s+|\.)\s*[A-Za-z0-9-]+)+)", re.I)
PAGE_WORDS = ["contact", "about", "team", "staff", "location", "get-in-touch", "get in touch", "reach", "connect",
              "visit", "find-us", "find us", "info"]
ROLE = ["info", "contact", "hello", "help", "care", "customerservice", "customercare", "guest", "guestservices", "members", "membership", "wash", "manager", "owner", "office", "sales", "bookings", "booking", "reservations", "service", "support",
        "team", "admin", "inquiries", "enquiries", "general", "mail", "appointments", "schedule", "frontdesk"]
LOW_ROLE = ["privacy", "abuse", "legal", "dmca", "webmaster", "postmaster", "hostmaster", "careers", "jobs", "hr",
            "accessibility", "unsubscribe", "billing"]
NOREPLY = re.compile(r"^(no-?reply|do-?not-?reply|donotreply|mailer-daemon|bounce)", re.I)
FREE_MAIL = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com", "live.com", "msn.com",
             "me.com", "comcast.net", "att.net", "sbcglobal.net", "protonmail.com", "proton.me", "ymail.com", "gmx.com"}
JUNK_DOMAINS = re.compile(r"(^|\.)(sentry\.io|sentry-next\.wixpress\.com|wixpress\.com|wix\.com|example\.(com|org|net)|"
                          r"test\.com|domain\.com|email\.com|yourdomain\.com|yoursite\.com|company\.com|"
                          r"sentry\.wixpress\.com|squarespace\.com|godaddy\.com|wordpress\.(com|org)|"
                          r"weebly\.com|shopify\.com|mysite\.com|website\.com|latofonts\.com|ingest\.sentry\.io)$", re.I)
JUNK_LOCAL = re.compile(r"^(user|username|name|email|your\.?name|yourname|john\.?doe|jane\.?doe|first\.?last|"
                        r"example|test|someone|you)$", re.I)
FILE_TLD = re.compile(r"\.(png|jpe?g|gif|svg|webp|avif|ico|css|js|json|xml|pdf|mp4|woff2?)$", re.I)
# website builders / agencies that put their own address in client footers
BUILDER_HINT = re.compile(r"(design|designs|digital|media|marketing|agency|studio|studios|web|websites|webdesign|"
                          r"seo|creative|solutions|interactive|hosting|labs)", re.I)
SOCIAL = re.compile(r"https?://(www\.)?(facebook\.com|instagram\.com|m\.facebook\.com|fb\.com)/[^\s\"'<>]+", re.I)


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.mailtos, self.cf, self.text = [], [], [], []
        self.form_fields, self.in_form, self.forms_with_email = [], False, 0
        self._a = None
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "noscript"):
            self._skip += 1
        if tag == "a":
            href = a.get("href") or ""
            if href.lower().startswith("mailto:"):
                self.mailtos.append(urllib.parse.unquote(href[7:].split("?")[0]))
            self._a = [href, ""]
        for k in ("data-cfemail",):
            if a.get(k):
                self.cf.append(a[k])
        if a.get("href", "").startswith("/cdn-cgi/l/email-protection#"):
            self.cf.append(a["href"].split("#", 1)[1])
        if tag == "form":
            self.in_form, self.form_fields = True, []
        if self.in_form and tag in ("input", "textarea"):
            self.form_fields.append(" ".join(str(v).lower() for v in (a.get("type"), a.get("name"), a.get("id"),
                                                                      a.get("placeholder"), tag) if v))

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1
        if tag == "a" and self._a is not None:
            self.links.append(tuple(self._a))
            self._a = None
        if tag == "form" and self.in_form:
            joined = " ".join(self.form_fields)
            if "email" in joined and ("message" in joined or "textarea" in joined or "comment" in joined):
                self.forms_with_email += 1
            self.in_form = False

    def handle_data(self, data):
        if not self._skip:
            self.text.append(data)
        if self._a is not None:
            self._a[1] += data


def cf_decode(hexstr):
    """Cloudflare email protection: first byte is the XOR key."""
    try:
        key = int(hexstr[:2], 16)
        return "".join(chr(int(hexstr[i:i + 2], 16) ^ key) for i in range(2, len(hexstr), 2))
    except ValueError:
        return ""


def deobfuscate(text):
    out = []
    for m in OBFUSCATED.finditer(text):
        local = m.group(1)
        dom = re.sub(r"\s*(\[\s*dot\s*\]|\(\s*dot\s*\)|\{\s*dot\s*\}|\s+dot\s+)\s*", ".", m.group(2), flags=re.I)
        dom = re.sub(r"\s+", "", dom)
        cand = f"{local}@{dom}"
        if EMAIL.fullmatch(cand):
            out.append(cand)
    return out


def clean(email):
    e = html.unescape(email).strip().strip(".,;:()[]<>\"'").lower()
    e = re.sub(r"^(mailto:|%20|u003e)", "", e)
    return e


def is_junk(email):
    if not EMAIL.fullmatch(email):
        return True
    local, dom = email.split("@", 1)
    if FILE_TLD.search(email) or re.search(r"@\d+x\.", email):  # image@2x.png
        return True
    if JUNK_DOMAINS.search(dom) or JUNK_LOCAL.match(local) or NOREPLY.match(local):
        return True
    if re.fullmatch(r"[0-9a-f]{16,}", local):  # sentry-style hash ids
        return True
    return False


def base_domain(host):
    host = (host or "").lower().split(":")[0]
    host = host[4:] if host.startswith("www.") else host
    parts = host.split(".")
    if len(parts) > 2 and len(parts[-1]) == 2 and parts[-2] in ("co", "com", "org", "net"):
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def rank(email, site_dom, name):
    local, dom = email.split("@", 1)
    edom = base_domain(dom)
    if edom == site_dom:
        if any(local.startswith(r) for r in LOW_ROLE):
            return 40
        if any(local == r or local.startswith(r + ".") or local.startswith(r) for r in ROLE):
            return 100
        return 90  # a person at the business
    if edom in FREE_MAIL:
        return 60
    # another domain: only the business's if its name is in it (e.g. sunrise-wash.com vs sunrisecarwash.com)
    words = [w for w in re.findall(r"[a-z]+", (name or "").lower()) if len(w) > 3 and w not in ("wash", "car", "the")]
    if any(w in edom for w in words):
        return 70
    if BUILDER_HINT.search(edom):
        return 0  # the web designer's address in the footer
    return 20


socket.setdefaulttimeout(20)   # backstop: a slow site can never stall the run


class Fetcher:
    def __init__(self):
        self.last = {}
        self.robots = {}
        self.seen_hosts = set()
        self.dead_hosts = set()   # failed to connect or timed out once: skipped for the rest of the run

    def allowed(self, url):
        p = urllib.parse.urlparse(url)
        root = f"{p.scheme}://{p.netloc}"
        if root not in self.robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                req = urllib.request.Request(root + "/robots.txt", headers={"User-Agent": UA})
                rp.parse(urllib.request.urlopen(req, timeout=10).read().decode("utf-8", "ignore").splitlines())
            except Exception:  # noqa: BLE001
                rp = None
            self.robots[root] = rp
        rp = self.robots[root]
        return True if rp is None else rp.can_fetch(UA, url)

    def get(self, url):
        host = urllib.parse.urlparse(url).netloc
        if host in self.dead_hosts:
            raise urllib.error.URLError("this site did not answer earlier in this run")
        wait = 1.0 - (time.time() - self.last.get(host, 0))
        if wait > 0:
            time.sleep(wait)
        self.last[host] = time.time()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*"})
        first = host not in self.seen_hosts
        self.seen_hosts.add(host)
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                ctype = r.headers.get("Content-Type", "")
                if "html" not in ctype and "text" not in ctype:
                    return r.geturl(), ""
                return r.geturl(), r.read(1_500_000).decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            try:
                body = e.read(20000).decode("utf-8", "ignore")
            except Exception:  # noqa: BLE001
                body = ""
            b = security_block(e.code, dict(e.headers or {}), body, first=first)
            if b:
                raise BlockedError(b) from None
            raise
        except (socket.timeout, TimeoutError, ConnectionError):
            self.dead_hosts.add(host)
            raise
        except urllib.error.URLError as e:
            # Some sites refuse older SSL libraries; curl (if installed) usually gets through.
            if "SSL" not in str(e) or not shutil.which("curl"):
                self.dead_hosts.add(host)
                raise
            res = subprocess.run(["curl", "-sL", "--max-time", "20", "-A", UA, "-w", "\n%{url_effective}", url],
                                 capture_output=True, text=True)
            if res.returncode != 0:
                self.dead_hosts.add(host)
                raise
            body, _, final = res.stdout.rpartition("\n")
            return final or url, body[:1_500_000]


def scan_html(raw):
    p = Page()
    try:
        p.feed(raw)
    except Exception:  # noqa: BLE001
        pass
    text = html.unescape(" ".join(p.text))
    found = [clean(m) for m in p.mailtos]
    found += [clean(cf_decode(h)) for h in p.cf]
    found += [clean(m) for m in EMAIL.findall(text)]
    found += [clean(m) for m in deobfuscate(text)]
    # emails hidden in attributes/JSON (schema.org "email": "...")
    found += [clean(m) for m in re.findall(r'"email"\s*:\s*"([^"]+@[^"]+)"', raw)]
    return p, found, text


def check_site(fetch, row, id_f, name_f, web_f):
    site = (row.get(web_f) or "").strip()
    out = {"id": row.get(id_f), "name": row.get(name_f), "website": site, "status": "", "best_email": None,
           "emails": [], "contact_form_url": None, "social": [],
           "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    if not site:
        out["status"] = "no_website"
        return out
    if not site.startswith("http"):
        site = "https://" + site
    host = urllib.parse.urlparse(site).netloc
    site_dom = base_domain(host)
    if SOCIAL.match(site):
        out["status"], out["social"] = "social_only", [site]
        return out
    try:
        final, raw = fetch.get(site)
    except BlockedError as e:
        out["status"], out["blocked_by"] = "blocked_by_security", str(e)
        return out
    except Exception as e:  # noqa: BLE001
        out["status"], out["error"] = "site_failed", str(e)[:120]
        return out
    new_dom = base_domain(urllib.parse.urlparse(final).netloc)
    if new_dom and new_dom != site_dom:
        out["redirected_to"] = new_dom  # the website now goes to another company's site: owner should confirm
    site_dom = new_dom or site_dom
    pages = [(final, raw)]
    p, _, text0 = scan_html(raw)
    # pick up to 4 contact-like pages on the same site
    cands = []
    for href, label in p.links:
        u = urllib.parse.urljoin(final, href).split("#")[0]
        if base_domain(urllib.parse.urlparse(u).netloc) != site_dom or u.rstrip("/") == final.rstrip("/"):
            continue
        hay = (u + " " + label).lower()
        score = sum(2 if w in ("contact", "get-in-touch", "get in touch") else 1 for w in PAGE_WORDS if w in hay)
        if score:
            cands.append((score, u))
    seen = {final.rstrip("/")}
    for _, u in sorted(cands, key=lambda x: -x[0]):
        if len(pages) >= 5:
            break
        if u.rstrip("/") in seen or not fetch.allowed(u):
            continue
        seen.add(u.rstrip("/"))
        try:
            pages.append(fetch.get(u))
        except Exception:  # noqa: BLE001
            continue
    best = {}
    total_text = 0
    for url, body in pages:
        if "contact" in url.lower() and not out["contact_form_url"]:
            out["contact_form_url"] = url  # a contact page (forms are often built in JavaScript we can't see)
        pg, emails, text = scan_html(body)
        total_text += len(text.strip())
        if pg.forms_with_email and not out["contact_form_url"]:
            out["contact_form_url"] = url
        out["social"] += [m.group(0) for m in SOCIAL.finditer(body)]
        for e in emails:
            if is_junk(e):
                continue
            r = rank(e, site_dom, row.get(name_f))
            if r <= 0:
                continue
            if e not in best or r > best[e]["rank"]:
                best[e] = {"email": e, "source_url": url, "rank": r}
    out["social"] = sorted(set(s.rstrip("/") for s in out["social"]))[:4]
    emails = sorted(best.values(), key=lambda x: (-x["rank"], x["email"]))
    # other-domain emails only count when they're the only option
    if any(x["rank"] >= 60 for x in emails):
        emails = [x for x in emails if x["rank"] >= 40]
    for x in emails[:5]:
        x["mx_ok"] = has_mx(x["email"].split("@", 1)[1])
    emails = [x for x in emails if x.get("mx_ok") is not False]
    out["emails"] = emails[:5]
    if emails:
        out["status"], out["best_email"] = "found", emails[0]["email"]
    elif total_text < 300:
        out["status"] = "needs_browser"
    elif out["contact_form_url"]:
        out["status"] = "contact_form_only"
    elif out["social"]:
        out["status"] = "social_only"
    else:
        out["status"] = "contact_form_only" if re.search(r"contact", text0, re.I) else "site_failed"
        if out["status"] == "site_failed":
            out["error"] = "no email, form or social link on the site"
    return out


def load_rows(path):
    if path.lower().endswith(".csv"):
        return list(csv.DictReader(open(path, newline="", encoding="utf-8-sig")))
    data = json.load(open(path))
    return data.get("rows", data) if isinstance(data, dict) else data


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("listings")
    ap.add_argument("--out", required=True, help="JSON lines results file (appended; used by --skip-done)")
    ap.add_argument("--limit", type=int, default=0, help="stop after this many sites this run (0 = all)")
    ap.add_argument("--skip-done", action="store_true", help="skip listings already in --out")
    ap.add_argument("--id", default="id")
    ap.add_argument("--name", default="name")
    ap.add_argument("--website", default="website")
    ap.add_argument("--max-minutes", type=float, default=30, help="stop starting new sites after this many minutes "
                    "(rerun with --skip-done to continue)")
    a = ap.parse_args()
    rows = load_rows(a.listings)
    done = set()
    if a.skip_done and os.path.exists(a.out):
        for line in open(a.out):
            try:
                done.add(str(json.loads(line)["id"]))
            except (ValueError, KeyError):
                continue
    todo = [r for r in rows if str(r.get(a.id)) not in done]
    if a.limit:
        todo = todo[:a.limit]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    fetch = Fetcher()
    counts = {}
    t0, stopped = time.time(), 0
    with open(a.out, "a") as f:
        for i, r in enumerate(todo, 1):
            if time.time() - t0 > a.max_minutes * 60:
                stopped = len(todo) - i + 1
                print(f"STOP time budget reached: {stopped} items not checked (rerun with --skip-done to continue)",
                      file=sys.stderr)
                break
            res = check_site(fetch, r, a.id, a.name, a.website)
            counts[res["status"]] = counts.get(res["status"], 0) + 1
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
            f.flush()
            print(f"[{i}/{len(todo)}] {res['status']:<18} {str(res['name'])[:40]:<40} {res['best_email'] or ''}",
                  file=sys.stderr)
    # an address used by several listings is a chain/head office inbox, not the local business: flag it
    if os.path.exists(a.out):
        uses = {}
        lines = [json.loads(l) for l in open(a.out) if l.strip()]
        for r in lines:
            if r.get("best_email"):
                uses[r["best_email"]] = uses.get(r["best_email"], 0) + 1
        for r in lines:
            r["shared_email"] = bool(r.get("best_email") and uses[r["best_email"]] > 1)
        with open(a.out, "w") as f:
            f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in lines)
        shared = sorted({r["best_email"] for r in lines if r.get("shared_email")})
    else:
        shared = []
    n = len(todo) - stopped
    left = len(rows) - len(done) - n
    summary = (f"Found emails for {counts.get('found', 0)} of {n} businesses; "
               f"{counts.get('contact_form_only', 0)} only have a contact form; "
               f"{counts.get('social_only', 0)} only have Facebook/Instagram; "
               f"{counts.get('no_website', 0)} have no website; "
               f"{counts.get('site_failed', 0) + counts.get('needs_browser', 0)} sites wouldn't load or need a full browser."
               + (f" {counts['blocked_by_security']} sites have security that blocks automated visitors (try them with the web reader)." if counts.get("blocked_by_security") else "")
               + (f" {left} still to check." if left > 0 else "")
               + (f" Shared by several listings (a chain's head office, not the local manager): {', '.join(shared[:3])}." if shared else ""))
    print(json.dumps({"status": "ok", "checked": n, "counts": counts, "summary": summary, "out": a.out}))
    # (listings whose website now redirects to another company carry "redirected_to": show them to the owner)
    return 0


if __name__ == "__main__":
    sys.exit(main())
