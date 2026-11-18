#!/usr/bin/env python3
"""Turn a crawl into a site checkup report. Free, no API keys.

    python3 checkup.py crawl.json [--old old.json] [--brand "Example Directory"] > report.json

Needs the output of site_crawl.py crawl (and optionally site_crawl.py old-urls).
Finds, in order of impact:
  1. broken_links        internal links pointing at pages that error (fix the link or redirect the target)
  2. dead_old_urls       URLs that used to work (Wayback Machine) and now 404, with a suggested redirect target
  3. keyword_fights      2+ indexable pages with nearly the same title or H1 (Google can't tell which to rank)
  4. stale_years         a past year in a title ("Best X 2023")
  5. title_problems      missing, duplicate, or over 65 characters
  6. h1_problems         missing or more than one H1
  7. meta_problems       missing or duplicate meta descriptions
  8. thin_pages          indexable pages under 300 words of main content
  9. sitemap_problems    noindex or broken pages in the sitemap; live pages missing from it
Every finding is a suggestion. The skill decides what to fix and asks the owner where its rules say so.
"""
import argparse
import datetime
import difflib
import json
import re
import sys
import urllib.parse
from collections import defaultdict

STOP = set("the a an and or of in for to near me my your our is are best by with at on from all how what".split())


def clean_title(t, brand):
    t = re.split(r"\s[|–—-]\s", t)[0] if t else ""
    if brand:
        t = t.replace(brand, "")
    return re.sub(r"\s+", " ", t).strip().lower()


def words(t):
    return {w for w in re.findall(r"[a-z0-9]+", t.lower()) if w not in STOP and len(w) > 1}


def path(u):
    return urllib.parse.urlparse(u).path or "/"


US_STATES = {"al": "alabama", "ak": "alaska", "az": "arizona", "ar": "arkansas", "ca": "california", "co": "colorado",
             "ct": "connecticut", "de": "delaware", "dc": "district-of-columbia", "fl": "florida", "ga": "georgia",
             "hi": "hawaii", "id": "idaho", "il": "illinois", "in": "indiana", "ia": "iowa", "ks": "kansas",
             "ky": "kentucky", "la": "louisiana", "me": "maine", "md": "maryland", "ma": "massachusetts",
             "mi": "michigan", "mn": "minnesota", "ms": "mississippi", "mo": "missouri", "mt": "montana",
             "ne": "nebraska", "nv": "nevada", "nh": "new-hampshire", "nj": "new-jersey", "nm": "new-mexico",
             "ny": "new-york", "nc": "north-carolina", "nd": "north-dakota", "oh": "ohio", "ok": "oklahoma",
             "or": "oregon", "pa": "pennsylvania", "ri": "rhode-island", "sc": "south-carolina", "sd": "south-dakota",
             "tn": "tennessee", "tx": "texas", "ut": "utah", "vt": "vermont", "va": "virginia", "wa": "washington",
             "wv": "west-virginia", "wi": "wisconsin", "wy": "wyoming"}


def best_target(dp, live_paths):
    """Closest live page for a dead old URL: same path with other capitals, else the live page whose path
    contains the most of the old URL's meaningful words (a trailing 2-letter state code counts as the state),
    preferring the deepest exact place match (a city page over its state page)."""
    low = [p for p in live_paths if p.lower() == dp.lower()]
    if low:
        return {"suggested_redirect": low[0], "match": "same page, different capitals"}
    slug = re.sub(r"\.(html?|php|aspx?)$", "", dp.lower()).strip("/").split("/")[-1]
    toks = [t for t in re.split(r"[^a-z0-9]+", slug) if t]
    state = US_STATES.get(toks[-1]) if toks else None
    if state:
        toks = toks[:-1]
    df = {}
    for p in live_paths:
        for w in set(re.split(r"[^a-z0-9]+", p.lower())):
            df[w] = df.get(w, 0) + 1
    # words in many URLs ("porta", "potty", "rentals") say nothing about the place: ignore them
    words = [t for t in toks if len(t) > 2 and df.get(t, 0) <= max(3, len(live_paths) * 0.02)]
    best, score = "", 0
    for p in live_paths:
        segs = p.lower().strip("/").split("/")
        if state and state not in segs:
            continue
        if len(segs) > 3:
            continue  # listing pages are never a redirect target for an old place URL
        hits = sum(1 for w in words if w in re.split(r"[^a-z0-9]+", segs[-1]))
        sc = hits * 10 + (5 if state else 0) - len(segs) * (0 if hits else 1)
        if sc > score:
            best, score = p, sc
    if not best and state:
        cands = [p for p in live_paths if p.lower().strip("/").split("/")[-1] == state]
        best = min(cands, key=len) if cands else ""
    if best:
        return {"suggested_redirect": best, "match": "place match" if state else "word match"}
    m = difflib.get_close_matches(dp.lower(), [p.lower() for p in live_paths], 1, 0.6)
    if m:
        return {"suggested_redirect": next(p for p in live_paths if p.lower() == m[0]), "match": "similar"}
    return {"suggested_redirect": "(no close match: pick the nearest topic page or the hub, or leave it if nothing fits)", "match": "none"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("crawl")
    ap.add_argument("--old", default="")
    ap.add_argument("--brand", default="")
    a = ap.parse_args()
    r = json.load(open(a.crawl))
    pages = r["pages"]
    live = {u: p for u, p in pages.items() if p["status"] == 200 and not p.get("final_url")}
    idx = {u: p for u, p in live.items() if not p.get("noindex")}
    year = datetime.date.today().year
    out = {}

    # status 0 = the crawler couldn't connect (timeout, bad characters); recheck these by hand, don't call them broken
    out["unreachable"] = [path(u) for u, p in pages.items() if p["status"] == 0][:30]

    # 1 broken links, grouped by target
    by_target = defaultdict(list)
    for l in r["broken_links"]:
        if l["status"] == 0:
            continue
        by_target[(l["to"], l["status"])].append({"from": path(l["from"]), "anchor": l["anchor"], "area": l.get("area", "body")})
    out["broken_links"] = sorted([{"target": path(t), "status": s, "links": len(v),
                                   "in_menu_or_footer": sum(1 for x in v if x["area"] != "body"),
                                   "linked_from": v[:5]} for (t, s), v in by_target.items()], key=lambda x: -x["links"])

    # 2 dead old URLs with a suggested redirect target (closest live path)
    if a.old:
        dead = json.load(open(a.old)).get("dead", [])
        live_paths = [path(u) for u in idx]
        sug = [{"old": path(d), **best_target(path(d), live_paths)} for d in dead]
        out["dead_old_urls"] = sug

    # 2b internal links that go through a redirect (wasted hop; point them at the final URL)
    red = defaultdict(lambda: {"count": 0, "examples": set()})
    for l in r.get("redirected_links", []):
        if re.search(r"log-?in|sign-?in|auth|account", path(l.get("final_url", ""))):
            continue  # a members-only link that sends visitors to sign in is on purpose
        k = (path(l["to"]), path(l.get("final_url", "")))
        red[k]["count"] += 1
        if len(red[k]["examples"]) < 3:
            red[k]["examples"].add(path(l["from"]))
    out["redirected_links"] = sorted([{"link": a, "goes_to": b, "links": v["count"], "examples": sorted(v["examples"])}
                                      for (a, b), v in red.items()], key=lambda x: -x["links"])[:30]

    # 3 keyword fights: similar titles or H1s between indexable pages
    items = [(u, clean_title(p.get("title", ""), a.brand), (p.get("h1") or [""])[0].lower()) for u, p in idx.items()]
    fights = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            u1, t1, h1 = items[i]
            u2, t2, h2 = items[j]
            for kind, x, y in (("title", t1, t2), ("h1", h1, h2)):
                wx, wy = words(x), words(y)
                if len(wx) >= 2 and len(wy) >= 2:
                    jac = len(wx & wy) / len(wx | wy)
                    diff = (wx ^ wy)
                    sibling = diff and all(w in path(u1).lower() or w in path(u2).lower() for w in diff)
                    if jac >= 0.75 and u1 != u2 and not sibling:
                        fights.append({"pages": [path(u1), path(u2)], "by": kind, "a": x, "b": y, "overlap": round(jac, 2)})
                        break
    # drop families of templated pages (e.g. 40 state pages that differ only by the state name)
    def family(pth):  # same parent folder and depth = pages made from one template (state, city, vendor pages)
        segs = pth.strip("/").split("/")
        return ("/".join(segs[:-1]), len(segs)) if len(segs) > 1 else ("", 1 if pth != "/" else 0)
    def template_siblings(f):
        a, b = f["pages"]
        if family(a) == family(b) and family(a)[1] > 1 and f["a"] != f["b"]:
            return True  # e.g. two city pages from the same template
        sa, sb = a.strip("/").split("/"), b.strip("/").split("/")
        # same name, different place (a state and a city both called "Washington"): not a fight
        if len(sa) > 1 and len(sb) > 1 and sa[-1] == sb[-1] and a != b:
            return True
        if len(sa) >= 3 and len(sb) >= 3:
            return True  # listing pages: the same chain in two cities is normal, not a fight
        # a page and its own regional version (/x and /x/uk): different audiences, not a fight
        short, long_ = (a, b) if len(sa) < len(sb) else (b, a)
        return long_.startswith(short.rstrip("/") + "/") and long_.strip("/").split("/")[-1] in (f["a"] + " " + f["b"])
    kept = [f for f in fights if not template_siblings(f)]
    groups = {}
    for f in kept:
        key = (f["by"], f["a"])
        g = groups.setdefault(key, {"by": f["by"], "text": f["a"], "pages": set()})
        g["pages"].update(f["pages"])
    out["keyword_fights"] = [{"by": g["by"], "text": g["text"], "pages": sorted(g["pages"]),
                              "fix": "decide which ONE page should own this search; give the others their own title/H1"}
                             for g in groups.values()][:50]

    # 4 stale years
    out["stale_years"] = [{"page": path(u), "title": p["title"]} for u, p in idx.items()
                          if any(int(y) < year for y in p.get("title_years", []))]

    # 5 titles, 6 h1, 7 meta
    tcount = defaultdict(list)
    mcount = defaultdict(list)
    tp, hp, mp = [], [], []
    for u, p in idx.items():
        t = p.get("title", "")
        if not t:
            tp.append({"page": path(u), "problem": "missing title"})
        elif len(t) > 70:
            tp.append({"page": path(u), "problem": f"title {len(t)} characters (low priority: Google shows about 60)", "title": t})
        tcount[t].append(path(u))
        h = p.get("h1") or []
        if not h:
            hp.append({"page": path(u), "problem": "no H1"})
        elif len(h) > 1:
            hp.append({"page": path(u), "problem": f"{len(h)} H1s", "h1": h[:3]})
        m = p.get("meta_description", "")
        if not m:
            mp.append({"page": path(u), "problem": "missing meta description"})
        mcount[m].append(path(u))
    long_t = [x for x in tp if x["problem"].startswith("title ")]
    if len(long_t) > 10:
        tp = [x for x in tp if not x["problem"].startswith("title ")] + long_t[:10] + [
            {"problem": f"{len(long_t) - 10} more long titles (low priority; usually one template, fix it once)"}]
    tp += [{"pages": v, "problem": "same title on several pages", "title": t} for t, v in tcount.items() if t and len(v) > 1]
    mp += [{"pages": v[:10], "problem": f"same meta description on {len(v)} pages"} for m, v in mcount.items() if m and len(v) > 1]
    out["title_problems"], out["h1_problems"], out["meta_problems"] = tp, hp, mp

    # 8 thin pages
    out["thin_pages"] = sorted([{"page": path(u), "words": p.get("words", 0)} for u, p in idx.items()
                                if p.get("words", 0) < 300 and path(u) != "/"
                                and not re.search(r"contact|privacy|terms|login|sign-?in|sign-?up|cart|account|^/blog$|/blog/page", path(u))],
                               key=lambda x: x["words"])

    # 9 sitemap
    sm = set(r.get("sitemap_urls", []))
    space_fixed = {path(u).lower().replace("%20", "-") for u in sm if "%20" in u}
    out["sitemap_problems"] = (
        [{"page": path(u), "problem": "in sitemap but noindex"} for u in sm if pages.get(u, {}).get("noindex")]
        + [{"page": path(u), "problem": f"in sitemap but returns {pages[u]['status']}"} for u in sm if u in pages and pages[u]["status"] != 200]
        + [{"page": path(u), "problem": "live and indexable but missing from sitemap"} for u in idx if u not in sm
           and path(u).lower() not in space_fixed
           and not re.search(r"contact|privacy|terms|login|sign-?in|sign-?up|account|cart", path(u))])
    if r.get("sitemap_raw_spaces"):
        out["sitemap_problems"].insert(0, {"problem": f"{r['sitemap_raw_spaces']} sitemap URLs contain spaces (the sitemap writes names, not slugs); "
                                                      "fix the sitemap to use the same slug as the page links",
                                           "examples": r.get("sitemap_space_examples", [])})

    out["summary"] = {k: len(v) for k, v in out.items() if isinstance(v, list)}
    out["pages_checked"] = len(pages)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
