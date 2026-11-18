#!/usr/bin/env python3
"""STEPS 5 and 7. Make the search-results template, then score every tool idea out of 100.

Step 5 (template):
  python3 score.py candidates.csv --decisions review.txt --make-serp-template 10
Step 7 (score):
  python3 score.py candidates.csv --decisions review.txt --serp serp.csv [--trends trends.csv] --out scored.csv

review.txt    : from classify.py, with every ?? replaced by yes or no. "no" ideas are removed.
serp.csv      : keyword,rank,url[,dr]   top 5 web results per keyword. The optional dr column
                (Domain Rating / Domain Authority from Ahrefs, Moz, Semrush...) makes the
                "small site" test exact. Without it a big-site list is used.
trends.csv    : keyword,trend   trend = up | flat | down (from Google Trends, 5-year view). Optional.

Score out of 100 (all fixed rules, no judgment):
  demand        0-30  rank among all ideas (percentile). Volume if supplied, else autocomplete hits
                      plus number of keyword variants.
  small sites   0-25  top-5 results that are small sites: 0=0, 1=10, 2=18, 3+=25
  tool proof    0-15  top-5 results that are already tool pages (calculator/estimator/... in URL):
                      0=0, 1=10, 2+=15. Proves Google wants a tool for this search.
  forum results 0-5   reddit/quora/forums in top 5 = people can't find a good answer = 5
  shopping      -15   3+ of the top 5 are store/category/home pages = people want to buy, not a tool
  fit           0-15  seed bucket: core 15, next 12, entity 10
  fresh data    0-5   tool type keeps changing data (fees, prices, schedules) = moat
  easy build    0-5   by tool type
  trend         -10..+5 down = -10, up = +5 (only if trends.csv given)
Confidence: HIGH = real volume + 5 results with dr, MEDIUM = volume OR all 5 results, LOW = otherwise.
"""
import argparse, csv, re, sys
from urllib.parse import urlparse

FRESH = {"fee calculator": 5, "cost estimator": 5, "schedule tool": 5, "value lookup": 3,
         "checker": 3, "comparison tool": 3, "calculator": 2, "converter or sizing": 0, "generator": 0, "quiz": 0}
EASE = {"fee calculator": 5, "calculator": 5, "converter or sizing": 5, "generator": 4, "quiz": 4,
        "cost estimator": 3, "schedule tool": 3, "checker": 3, "comparison tool": 3, "value lookup": 1}
FIT = {"core": 15, "next": 12, "entity": 10}
BIG = {"angi.com", "homeadvisor.com", "thumbtack.com", "houzz.com", "consumerreports.org", "which.co.uk",
       "thisoldhouse.com", "bobvila.com", "familyhandyman.com", "forbes.com", "fixr.com", "reddit.com", "youtube.com", "facebook.com", "instagram.com", "tiktok.com", "pinterest.com",
       "quora.com", "wikipedia.org", "amazon.com", "yelp.com", "linkedin.com", "x.com", "twitter.com",
       "forbes.com", "investopedia.com", "nerdwallet.com", "bankrate.com", "wikihow.com", "nytimes.com",
       "cnbc.com", "businessinsider.com", "apple.com", "google.com", "microsoft.com", "indeed.com",
       "glassdoor.com", "zillow.com", "realtor.com", "healthline.com", "webmd.com", "mayoclinic.org",
       "clevelandclinic.org", "trustpilot.com", "medium.com", "walmart.com", "target.com", "homedepot.com",
       "lowes.com", "etsy.com", "shopify.com", "hubspot.com", "usnews.com", "cnet.com",
       "theverge.com", "wsj.com", "bloomberg.com", "reuters.com", "cnn.com", "bbc.co.uk", "bbc.com",
       "theguardian.com", "huffpost.com", "buzzfeed.com", "omnicalculator.com", "calculator.net",
       "kbb.com", "edmunds.com", "carfax.com", "tripadvisor.com", "expedia.com", "booking.com",
       "allrecipes.com", "thespruce.com", "bobvila.com", "angi.com", "homeguide.com", "thumbtack.com",
       "fixr.com", "costhelper.com", "alibaba.com", "petsmart.com", "petco.com", "chewy.com", "wayfair.com", "wayfair.ca", "thesprucepets.com", "walmart.ca", "amazon.co.uk", "ikea.com", "bestbuy.com", "costco.com", "lifehacker.com", "printify.com", "wellkeptwallet.com", "statista.com", "github.com", "stackexchange.com", "stackoverflow.com"}
FORUM = re.compile(r"(reddit\.com|quora\.com|forum|community\.|/community/|/forums?/|/threads?/|stackexchange|answers\.)")
TOOLURL = re.compile(r"(calculator|calc\b|calc[-/]|estimator|converter|checker|lookup|/tools?/|-tool|generator|quiz)")
SHOPURL = re.compile(r"(/collections?/|/browse/|/product-category/|/products?/|/shop/|/cat/|/category/|/c/|/dp/|/listing/|/aquarium-supplies/|/aquarium-products/)")
URLOK = re.compile(r"^https?://[a-z0-9.-]+\.[a-z]{2,}(/\S*)?$", re.I)

def root(u):
    h = urlparse(u if "//" in u else "https://" + u).netloc.lower().split(":")[0]
    if h.startswith("www."): h = h[4:]
    p = h.split(".")
    return ".".join(p[-3:]) if len(p) > 2 and p[-2] in ("co", "com", "org", "gov", "ac", "net", "edu") and len(p[-1]) == 2 else ".".join(p[-2:])

def is_brand(u, subj):
    """The official site of the brand/organization the tool is about: domain STARTS with a subject word
    (redcross.org for 'red cross'), but not a third-party site that only mentions the name."""
    r = root(u); b = r.split(".")[0]
    for w in subj.split():
        if len(w) <= 3 or w not in b: continue
        if r.endswith(".org"): return True                      # nonprofit chapter, e.g. redcross.org
        rest = b[len(w):] if b.startswith(w) else None
        if rest is not None and (rest == "" or rest not in subj.replace(" ", "")): return True
    return False

def is_small(u, subj, dr):
    if is_brand(u, subj) or FORUM.search(u): return False
    r = root(u)
    if r.endswith(".gov") or r.endswith(".edu") or ".gov." in r or ".ac." in r or ".edu." in r: return False
    if dr is not None: return dr <= 40
    return r not in BIG

def read_decisions(path, C):
    need = {c["id"]: c["main_keyword"] for c in C if c.get("needs_check") == "yes"}
    allc = {c["id"]: c["main_keyword"] for c in C}
    if not need and not path: return set()
    if need and not path: sys.exit(f"ERROR: {len(need)} ideas need a decision. Fill review.txt (step 4) and pass --decisions review.txt")
    got = {}
    for line in open(path, encoding="utf-8"):
        if line.startswith("#") or not line.strip(): continue
        m = re.match(r"\s*(C\d+)\s+(\S+)\s*\|.*main keyword: (.*?) \|", line)
        if not m: continue
        cid, ans, mk = m.group(1), m.group(2).lower(), m.group(3).strip()
        if ans not in ("yes", "no"): sys.exit(f"ERROR: {cid} still says {ans!r}. Write yes or no.")
        if cid not in need and allc.get(cid) == mk and ans == "no":
            got[cid] = "no"   # an extra "no" the agent added for an idea that wasn't flagged (owner-facing, brand page...)
            continue
        if need.get(cid) != mk: sys.exit(f"ERROR: review.txt is out of date ({cid} does not match candidates.csv). Run step 3 again and redo step 4.")
        got[cid] = ans
    missing = sorted(set(need) - set(got))
    if missing: sys.exit(f"ERROR: review.txt has no yes/no for: {', '.join(missing)}")
    return {i for i, v in got.items() if v == "no"}

def read_serp(path):
    serp, errs = {}, []
    for n, r in enumerate(csv.DictReader(open(path, encoding="utf-8-sig")), 2):
        u = (r.get("url") or "").strip()
        if not u: continue
        k = (r.get("keyword") or "").strip().lower()
        if not URLOK.match(u): errs.append(f"line {n}: not a full URL -> {u!r}"); continue
        if "example.com" in u or "..." in u: errs.append(f"line {n}: placeholder URL -> {u!r}"); continue
        dr = r.get("dr", "").strip() if r.get("dr") is not None else ""
        try: dr = float(dr) if dr else None
        except ValueError: errs.append(f"line {n}: dr must be a number -> {dr!r}"); dr = None
        lst = serp.setdefault(k, [])
        if any(x[1].rstrip("/") == u.rstrip("/") for x in lst): errs.append(f"line {n}: same URL twice for '{k}'"); continue
        lst.append((int(r.get("rank") or len(lst) + 1), u, dr))
    return serp, errs

def pct(v, vals):
    if not vals: return 0
    below = sum(1 for x in vals if x < v)
    return below / max(1, len(vals) - 1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates"); ap.add_argument("--out", default="scored.csv")
    ap.add_argument("--decisions"); ap.add_argument("--serp"); ap.add_argument("--trends")
    ap.add_argument("--make-serp-template", type=int, metavar="N")
    a = ap.parse_args()
    if getattr(a, "out", None):  # create the output folder (notes/<site>/...) if it is new
        import os as _os
        _os.makedirs(_os.path.dirname(_os.path.abspath(a.out)), exist_ok=True)
    C = list(csv.DictReader(open(a.candidates, encoding="utf-8")))
    if not C: sys.exit("ERROR: candidates.csv is empty")
    drop = read_decisions(a.decisions, C)
    C = [c for c in C if c["id"] not in drop]
    data_mode = C[0].get("demand_source") == "volume"

    def dval(c):
        d = float(c["demand"])
        return d if data_mode else d + 0.5 * float(c.get("n_keywords") or 0)
    vals = [dval(c) for c in C]

    if a.make_serp_template:
        top = sorted(C, key=lambda c: -dval(c))[:a.make_serp_template]
        with open("serp.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["keyword", "rank", "url", "dr"])
            for c in top:
                for rank in range(1, 6): w.writerow([c["main_keyword"], rank, "", ""])
        print(f"WROTE serp.csv: {len(top)} keywords x 5 empty rows ({len(drop)} ideas removed in review.txt).")
        print("NEXT: step 6. Search each keyword, paste the top 5 result URLs. Leave dr empty unless you have Ahrefs/Moz/Semrush.")
        return

    serp, errs = read_serp(a.serp) if a.serp else ({}, [])
    if errs:
        print("ERROR: serp.csv has problems. Fix these lines and run again:"); [print("  " + e) for e in errs[:20]]; sys.exit(1)
    if a.serp:
        thin = [k for k in {r["keyword"].strip().lower() for r in csv.DictReader(open(a.serp, encoding="utf-8-sig"))} if len(serp.get(k, [])) < 3]
        if thin: print("ERROR: these keywords have fewer than 3 URLs in serp.csv:\n  " + "\n  ".join(thin)); sys.exit(1)
    trends = {}
    if a.trends:
        for r in csv.DictReader(open(a.trends, encoding="utf-8-sig")):
            t = (r.get("trend") or "").strip().lower()
            if t not in ("up", "flat", "down"): sys.exit(f"ERROR: trends.csv trend must be up, flat or down -> {t!r}")
            trends[r["keyword"].strip().lower()] = t

    out = []
    for c in C:
        kw = c["main_keyword"].strip().lower(); subj = c["subject"].strip().lower()
        res = sorted(serp.get(kw, []))[:5]
        dem = round(30 * pct(dval(c), vals))
        if res:
            small = [u for _, u, dr in res if is_small(u, subj, dr)]
            tools = [u for _, u, _ in res if TOOLURL.search(u.lower())]
            forums = [u for _, u, _ in res if FORUM.search(u.lower())]
            official = [u for _, u, _ in res if is_brand(u, subj) or ".gov" in root(u)]
            s_small = [0, 10, 18, 25][min(3, len(small))]
            s_tool = [0, 10, 15][min(2, len(tools))]
            s_forum = 5 if forums else 0
            shops = [u for _, u, _ in res if SHOPURL.search(urlparse(u).path.lower() + "/") or urlparse(u).path in ("", "/")]
            s_shop = -15 if len(shops) >= 3 else 0   # 3+ store/home pages = shopping search, a tool won't rank
            proof = ", ".join(dict.fromkeys(root(u) for u in small)) or "none"
            has_dr = all(dr is not None for _, _, dr in res)
        else:
            s_small, s_tool, s_forum, s_shop, proof, tools, official, has_dr = 0, 0, 0, 0, "NO SERP DATA", [], [], False
        tr = trends.get(kw, "")
        s_tr = {"down": -10, "up": 5}.get(tr, 0)
        fit, fr, ez = FIT.get(c["bucket"], 10), FRESH.get(c["tool_type"], 2), EASE.get(c["tool_type"], 3)
        total = dem + s_small + s_tool + s_forum + s_shop + fit + fr + ez + s_tr
        conf = ("HIGH" if data_mode and len(res) >= 5 and has_dr else
                "MEDIUM" if data_mode or len(res) >= 5 else "LOW") if res else "NOT CHECKED"
        out.append({**c, "score": total, "confidence": conf, "s_demand": dem, "s_small": s_small,
                    "s_tool": s_tool, "s_forum": s_forum, "s_shop": s_shop, "s_fit": fit, "s_fresh": fr, "s_ease": ez,
                    "trend": tr, "small_sites_in_top5": proof, "tool_pages_in_top5": " ".join(tools),
                    "official_urls": " ".join(official), "serp_urls": " ".join(u for _, u, _ in res)})
    out.sort(key=lambda r: (r["confidence"] == "NOT CHECKED", -r["score"], -dval(r)))
    # same search intent = 2+ of the same URLs in the top 5. Keep the higher one, merge keywords.
    keep = []
    for r in out:
        urls = set(r["serp_urls"].split())
        twin = next((k for k in keep if urls and len(urls & set(k["serp_urls"].split())) >= 2), None)
        if twin:
            twin["top_keywords"] += "; " + r["main_keyword"]
            twin["merged"] = (twin.get("merged", "") + " " + r["id"]).strip()
        else:
            keep.append(r)
    if len(keep) < len(out): print(f"MERGED {len(out) - len(keep)} ideas that share 2+ top-5 URLs with a higher idea (same search intent)")
    out = keep
    cols = ["rank", "id", "score", "confidence", "tool_type", "subject", "main_keyword", "demand", "demand_source",
            "s_demand", "s_small", "s_tool", "s_forum", "s_shop", "s_fit", "s_fresh", "s_ease", "trend",
            "small_sites_in_top5", "tool_pages_in_top5", "official_urls", "serp_urls", "merged", "n_keywords", "bucket", "top_keywords"]
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader()
        for i, r in enumerate(out, 1): w.writerow({**r, "rank": i})
    print(f"DONE: scored {len(out)} ideas ({'DATA' if data_mode else 'FREE'} MODE) -> {a.out}")
    for i, r in enumerate(out[:10], 1):
        print(f"  #{i:<2} {r['score']:>3}/100 {r['confidence']:<11} {r['tool_type']:<18} {r['main_keyword']}  [{r['small_sites_in_top5']}]")
    if not a.serp: print("NEXT: run step 5 to make serp.csv, fill it (step 6), then rerun with --serp serp.csv")

if __name__ == "__main__":
    main()
