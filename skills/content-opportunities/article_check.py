#!/usr/bin/env python3
"""Quality gate for content-opportunities. An article may not be published until this passes.

    python3 article_check.py article.json [--site https://example.com] [--no-http]

article.json:
    {"title": "...", "meta_title": "...", "meta_description": "...",
     "body_md": "...",                       # markdown, no H1, no FAQ
     "faq": [{"q": "...", "a": "..."}],
     "facts": ["Example Directory lists 214 car washes", "...", "source: ..."],  # Step 1 facts + public sources used
     "brand": "Example Directory",
     "internal_names": ["business_listings", "EXD"],   # table names, site codes: must never appear
     "never_link": ["competitor-directory.com"]}       # competitors and other directories

Checks (any failure = fix the article by hand, then run again):
  1. Shape: 4 to 8 H2 headings, quick answer paragraph before the first H2, 3 to 6 FAQ, meta lengths.
  2. Headings are reader questions or phrases, never about our data or method.
  3. Banned phrases (AI tells, hedges) and internal names.
  4. Every number in the article appears in the facts (no invented numbers).
  5. Links: 3 to 6 internal links that load; outbound links only to sources, never to never_link
     domains, other directories, or more than 4 outbound links in total.
  6. Repetition: a 6 word phrase used 3+ times, or a sentence over 45 words.
  7. Brand named 2 to 4 times in the title and body (exact capitalization; FAQ not counted).
  6b. The same sentence twice, or the same set of numbers stated twice in different sentences, fails.
  8. More than one "check before you go" sentence (call ahead, hours can change, may vary...) fails.
  9. Warning (not a failure): "N of the M" pairs that disagree, so the agent checks the numbers agree.
Prints JSON {"pass": bool, "failures": [...]} and exits 1 on failure.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from urllib.parse import urlparse

BANNED = [
    "nestled", "boasts", "treasure trove", "look no further", "whether you're a seasoned", "in today's",
    "one-stop", "hidden gem", "plethora", "myriad", "delve", "dive into", "navigate the world",
    "game changer", "game-changer", "unlock", "elevate your", "in conclusion", "it's important to note",
    "it is important to note", "ultimate guide", "comprehensive guide", "when it comes to",
    "verified discussion", "according to our database", "our data shows", "queried", "records show",
    "rows", "listings in our table", "active listings",
]
DATA_HEADINGS = ["our data", "our directory", "our listings", "our method", "methodology", "sources",
                 "quick answer", "what's listed", "what is listed", "in the directory", "key facts"]
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

BLOCKED_LINKS = []



def load_ok(url: str, hops: int = 5) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
        return urllib.request.urlopen(req, timeout=20).status < 400
    except urllib.error.HTTPError as e:
        loc = e.headers.get("Location")
        if e.code in (301, 302, 303, 307, 308) and loc and hops:
            return load_ok(urllib.parse.urljoin(url, loc), hops - 1)
        try:
            body = e.read(20000).decode("utf-8", "ignore")
        except Exception:  # noqa: BLE001
            body = ""
        if security_block(e.code, dict(e.headers or {}), body, first=True):
            BLOCKED_LINKS.append(url)
            return True  # the site's security answered, not the page: not counted as broken (checked by web reader)
        return False
    except Exception:  # noqa: BLE001
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("article")
    ap.add_argument("--site", default="", help="site root, e.g. https://example.com (for internal link checks)")
    ap.add_argument("--no-http", action="store_true", help="skip loading internal links")
    a = ap.parse_args()
    art = json.load(open(a.article))
    body = art.get("body_md", "")
    faq = art.get("faq") or []
    brand = art.get("brand", "")
    fails, warnings = [], []

    def fail(check, detail=""):
        fails.append({"check": check, "detail": str(detail)[:160]})

    # 1. shape
    h2 = re.findall(r"^##\s+(.+)$", body, re.M)
    if not 4 <= len(h2) <= 8:
        fail("need 4 to 8 H2 headings", len(h2))
    if re.match(r"\s*#", body) or not body.strip():
        fail("body must open with the quick answer paragraph, not a heading")
    if re.search(r"^#\s", body, re.M):
        fail("no H1 in body_md (the page adds the title)")
    if not 3 <= len(faq) <= 6:
        fail("need 3 to 6 FAQ entries", len(faq))
    if len(art.get("meta_title", "")) > 60 or not art.get("meta_title"):
        fail("meta_title missing or over 60 characters", art.get("meta_title", ""))
    md = art.get("meta_description", "")
    if not 70 <= len(md) <= 155:
        fail("meta_description must be 70 to 155 characters", len(md))
    if re.search(r"^##\s*(faq|frequently asked)", body, re.M | re.I):
        fail("FAQ goes in the faq field, not the body")

    # 2. headings are for the reader
    for h in h2:
        if any(re.search(r"\b" + re.escape(d) + r"\b", h.lower()) for d in DATA_HEADINGS):
            fail("heading is about our data or method, not the reader's question", h)

    full = " ".join([art.get("title", ""), body] + [f"{x.get('q', '')} {x.get('a', '')}" for x in faq])
    low = full.lower()
    plain = re.sub(r"\]\([^)]*\)", "]", low)  # drop link targets

    # 3. banned + internal names
    for b in BANNED:
        if re.search(r"\b" + re.escape(b) + r"\b", plain):
            fail("banned phrase", b)
    if "—" in full:
        fail("em dash used (write two sentences instead)")
    for n in art.get("internal_names", []):
        if n and n.lower() in plain:
            fail("internal name shown to readers", n)

    # 4. numbers come from facts
    facts = " ".join(art.get("facts", [])).lower().replace(",", "")
    if not art.get("facts"):
        fail("no facts given", "include the Step 1 facts and the public sources used")
    for m in set(re.findall(r"\$?\d[\d,]*(?:\.\d+)?%?", re.sub(r"\]\([^)]*\)", "]", full))):
        num = m.rstrip(",").replace(",", "").lower()
        bare = num.strip("$%")
        if len(bare) <= 1 and "%" not in num and "$" not in num:
            continue  # single digits ("3 tips") are fine
        if re.fullmatch(r"20\d\d", bare):
            continue  # years
        if not re.search(r"(?<![\d.])" + re.escape(bare) + r"(?![\d])", facts):
            fail("number not in facts (unverified)", m)

    # 5. links
    links = re.findall(r"\]\(([^)\s]+)\)", body)
    site_host = urlparse(a.site).netloc.replace("www.", "") if a.site else ""
    internal, outbound = [], []
    for l in links:
        host = urlparse(l).netloc.replace("www.", "")
        (internal if (l.startswith("/") or (site_host and host == site_host)) else outbound).append(l)
    if not 3 <= len(internal) <= 6:
        fail("need 3 to 6 internal links", len(internal))
    if len(outbound) > 4:
        fail("more than 4 outbound links", len(outbound))
    for l in outbound:
        host = urlparse(l).netloc.lower().replace("www.", "")
        if any(host == d.lower() or host.endswith("." + d.lower()) for d in art.get("never_link", [])):
            fail("links to a competitor or blocked domain", host)
        if re.search(r"(directory|finder|locator|near-?me|outlets?)\.", host):
            fail("outbound link looks like another directory (check it)", host)
    if a.site and not a.no_http:
        for l in internal:
            url = a.site.rstrip("/") + l if l.startswith("/") else l
            if not load_ok(url):
                fail("internal link does not load", l)

    # 6. repetition and long sentences
    prose = re.sub(r"^#.*$", "", body.lower(), flags=re.M)  # headings repeat the keyword on purpose
    prose = re.sub(r"\]\([^)]*\)", "]", prose)
    words = re.findall(r"[a-z0-9']+", prose)
    grams = Counter(" ".join(words[i:i + 6]) for i in range(len(words) - 5))
    for g, n in grams.items():
        if n >= 3:
            fail("phrase repeated 3+ times", g)
            break
    seen_sent, seen_facts = {}, {}
    prose_lines = "\n".join(l for l in body.splitlines() if not l.lstrip().startswith(("#", "|")))
    for s in re.split(r"(?<=[.!?])\s+", re.sub(r"[#>*|`-]", " ", prose_lines)):
        if len(s.split()) > 45:
            fail("sentence over 45 words", s[:80])
        key = re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()
        key = re.sub(r"\s+", " ", key)
        if len(key.split()) >= 5:
            if key in seen_sent:
                fail("sentence repeated (say it once)", s.strip()[:90])
            seen_sent[key] = True
            nums = tuple(sorted(re.findall(r"\d+(?:\.\d+)?", key)))
            if len(nums) >= 2:
                if nums in seen_facts and seen_facts[nums] != key:
                    fail("same numbers stated twice (say each fact once)", s.strip()[:90])
                seen_facts.setdefault(nums, key)

    # 7. brand mentions
    if brand:  # counted in the title and body only (FAQ mentions are not counted)
        # exact capitalization only, so an ordinary phrase ("austin car washes") isn't counted as the brand
        n = len(re.findall(r"(?<![A-Za-z0-9])" + re.escape(brand) + r"(?![A-Za-z0-9])",
                           art.get("title", "") + " " + body))
        if not 2 <= n <= 4:
            fail("brand (exact capitalization) should appear 2 to 4 times in the title and body (FAQ not counted)", n)

    # 8. hedging: at most one "check before you go" sentence per article
    HEDGE = re.compile(r"call ahead|check before|call before|hours can change|hours change|may vary|"
                       r"hours vary|subject to change")
    hedged = [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n+", plain) if HEDGE.search(x)]
    if len(hedged) >= 2:
        fail("more than one 'check before you go' sentence (keep one clear reminder)", " | ".join(h[:60] for h in hedged))

    # 9. numbers must agree: "N of the M" pairs about the same total that disagree (best effort, warning only)
    pairs = re.findall(r"\b(\d+) of (?:the )?(\d+)\b", plain)
    by_total = {}
    for n_, m_ in pairs:
        by_total.setdefault(m_, set()).add(n_)
    for m_, ns in by_total.items():
        if len(ns) > 1:
            warnings.append(f"'N of the {m_}' used with different numbers ({', '.join(sorted(ns))}): make sure each is about a different thing, or fix it")

    if BLOCKED_LINKS:
        warnings.append(f"{len(BLOCKED_LINKS)} internal links not checked: the site's security blocks automated visitors; "
                        "open them with your built-in web reader to confirm they load")
    print(json.dumps({"pass": not fails, "failures": fails, "warnings": warnings}, ensure_ascii=False, indent=1))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
