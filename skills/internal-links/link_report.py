#!/usr/bin/env python3
"""Internal link report from a crawl. Free; Search Console data is an optional power-up.

    python3 link_report.py crawl.json --targets targets.json [--gsc pages.csv] > links.json

crawl.json   output of ../broken-links-and-seo-errors/site_crawl.py crawl
targets.json the pages that deserve more links and the words people use for them (the agent writes this):
    {"/car-washes": {"phrases": ["car washes", "car wash near me"], "anchor": "car washes near you"},
     "/car-wash-cost-calculator": {"phrases": ["car wash cost", "how much is a car wash"], "anchor": "car wash cost calculator"}}
pages.csv    optional Search Console export (Performance → Pages → Export): columns page/Top pages, clicks, impressions, position.

Reports (Google counts every link, so all link types are counted, each separately):
  inbound        per page: content_links (in body text), sitewide_links (menu/header/footer, or the same link on 80%+
                 of pages), breadcrumb_links (breadcrumb trails), total
  weak_pages     indexable pages with at most 1 link of ANY kind pointing at them (true orphans)
  page_types     per page type (URL pattern, 3+ pages): share of sampled pages that have a breadcrumb trail
                 (HTML or schema), link up to their parent page, link to the main hub. Never propose breadcrumbs /
                 a hub link / a "browse all" link for a type where most pages already have it.
  broken_routes  broken internal links grouped: missing pages the site itself expects (target in the sitemap, or
                 siblings of the same page type work) vs plain bad links; the name pattern that breaks
                 (hyphen, apostrophe, accent, space, dot, ampersand in the name) when one explains them
                 --check-sitemap N proves it: status-checks every sitemap URL of that page type the crawl didn't
                 load and lists each one that fails (sitemap_check). Names compared = link text, not the URL.
  menu_broken    broken links in the menu/header/footer (on many pages): ask the owner build-or-remove
  target_coverage per money page: how many pages of each page type link to it at all (0 = template opportunity)
  vague_anchors  ... in_blocks = the real heading of the block those links sit under (use it by name)
  vague_anchors  targets mostly linked with text that doesn't say what the page is ("Florida", "click here")
  suggestions    for each target: pages that already mention its phrases but don't link to it, best donors first.
                 Donor strength = links the donor gets (+ its Search Console clicks if given), times how close
                 its topic is to the target. Contact/about/legal/login/"how this was made" pages are never donors
                 unless nothing else mentions the topic (then flagged weak_donor).
                 Each suggestion includes the exact sentence where the link fits.
"""
import argparse
import csv
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict

NOT_DONOR = re.compile(r"(^|/)(contact(-us)?|about(-us)?|privacy(-policy)?|terms(-of-(service|use)|-and-conditions)?|legal|"
                       r"cookies?(-policy)?|disclaimer|login|log-in|sign-?in|sign-?up|register|account|cart|checkout|search|"
                       r"how-[a-z-]*-(made|built)|thank-?you|unsubscribe)(/|$)", re.I)
UA = "Mozilla/5.0 (compatible; directory-ops/1.0; +https://github.com/Directoryops/directory-ops)"
GENERIC = {"click here", "here", "read more", "learn more", "more", "this", "link", "this page", "website", "view", "see more"}


# sentence ends, but not after abbreviations like "St." "Mt." "Dr." "Ft." "U.S." "No." (a city name is not a sentence end)
_ABBR = r"(?<!\bSt)(?<!\bMt)(?<!\bDr)(?<!\bFt)(?<!\bNo)(?<!\bMr)(?<!\bMs)(?<!\bvs)(?<!\bU\.S)(?<!\b[A-Z])"
END = _ABBR + r"[.!?]\s+"
END_AT = _ABBR + r"[.!?](\s|$)"

def path(u):
    p = urllib.parse.urlparse(u).path or "/"
    return p if p == "/" else p.rstrip("/")


def load_gsc(f):
    out = {}
    if not f:
        return out
    with open(f, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            k = {c.lower().strip(): v for c, v in row.items()}
            page = k.get("top pages") or k.get("page") or k.get("pages") or ""
            try:
                out[path(page)] = {"clicks": int(float(k.get("clicks", 0) or 0)),
                                   "impressions": int(float(k.get("impressions", 0) or 0)),
                                   "position": float(k.get("position", 0) or 0)}
            except ValueError:
                pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("crawl")
    ap.add_argument("--targets", default="")
    ap.add_argument("--gsc", default="")
    ap.add_argument("--per-target", type=int, default=15)
    ap.add_argument("--check-sitemap", type=int, default=0, metavar="N",
                    help="prove broken-page patterns: status-check up to N sitemap URLs of each affected page type that "
                         "the crawl didn't load (polite: one at a time). Lists every one that fails.")
    a = ap.parse_args()
    r = json.load(open(a.crawl))
    pages = {path(u): p for u, p in r["pages"].items() if p["status"] == 200 and not p.get("final_url")}
    idx = {u: p for u, p in pages.items() if not p.get("noindex")}
    gsc = load_gsc(a.gsc)

    content_in, chrome_in, crumb_in = Counter(), Counter(), Counter()
    anchors = defaultdict(Counter)
    anchor_blocks = defaultdict(Counter)   # (target, anchor) -> block headings the link sits under
    links_from = defaultdict(set)      # content links only ("already linked in the text")
    any_from = defaultdict(set)        # every link type
    seen = set()
    crawled_from = {path(l["from"]) for l in r["links"]}
    pair_pages, block_pages = defaultdict(set), defaultdict(set)
    for l in r["links"]:
        pair_pages[path(l["to"])].add(path(l["from"]))
        if l.get("area", "body") == "body":
            block_pages[(path(l["to"]), (l.get("anchor") or "").strip().lower())].add(path(l["from"]))
    n_crawled = max(1, len(crawled_from))
    # the same link (same target + same text) on 80%+ of crawled pages is a sitewide block, even outside <nav>
    sitewide_blocks = {k for k, fs in block_pages.items() if len(fs) >= 0.8 * n_crawled and n_crawled >= 5}
    sitewide_targets = {t for t, fs in pair_pages.items() if len(fs) >= 0.8 * n_crawled and n_crawled >= 5}
    for l in r["links"]:
        f, t = path(l["from"]), path(l["to"])
        area = l.get("area", "body")
        if f == t or (f, t, area) in seen:
            continue
        seen.add((f, t, area))
        any_from[f].add(t)
        if area == "breadcrumb":
            crumb_in[t] += 1
        elif area == "body" and (t, (l.get("anchor") or "").strip().lower()) not in sitewide_blocks:
            links_from[f].add(t)
            content_in[t] += 1
            if l["anchor"]:
                anchors[t][l["anchor"].strip().lower()] += 1
                anchor_blocks[(t, l["anchor"].strip().lower())][(l.get("block") or "").strip()] += 1
        else:
            chrome_in[t] += 1
    for u, p in pages.items():   # JSON-LD breadcrumbs count too (Google reads them)
        for b in p.get("breadcrumb_schema", []) or []:
            if path(b) != u and path(b) not in any_from[u]:
                crumb_in[path(b)] += 1

    def total(u):
        return content_in[u] + chrome_in[u] + crumb_in[u]

    out = {"inbound": sorted([{"page": u, "content_links": content_in[u], "sitewide_links": chrome_in[u],
                               "breadcrumb_links": crumb_in[u], "total_links": total(u),
                               "in_menu_on_most_pages": u in sitewide_targets or chrome_in[u] >= 0.8 * n_crawled,
                               **({"gsc": gsc[u]} if u in gsc else {})} for u in idx], key=lambda x: x["content_links"])}
    out["weak_pages"] = [x for x in out["inbound"] if x["total_links"] <= 1 and x["page"] != "/"
                         and not NOT_DONOR.search(x["page"])]
    if r.get("limit_reached"):
        out["weak_pages_note"] = ("partial crawl: link counts only include the pages crawled, so a page can look weak just "
                                  "because the pages linking to it weren't crawled. Re-crawl without a page limit before "
                                  "calling any page weak.")
    out["page_types"] = page_types(pages, r["links"])
    out["broken_routes"], out["menu_broken"] = broken_routes(r, pages, a.check_sitemap)

    targets = json.load(open(a.targets)) if a.targets else {}
    df = Counter(w for u in idx for w in set(re.findall(r"[a-z]+", u.lower())))
    vague = []
    has_blocks = any("block" in l for l in r["links"][:500])
    for t, cnt in anchors.items():
        if t not in idx or not cnt or len(t.strip("/").split("/")) > 2:
            continue  # listing pages (deep) are linked by business name: that's a clear anchor
        words_t = set(re.findall(r"[a-z]+", " ".join(targets.get(t, {}).get("phrases", [])) + " " + idx[t].get("title", "").lower()))
        topic = {w for w in words_t if len(w) > 3}
        total = sum(cnt.values())
        # an anchor is vague when it shares no topic word with the page (e.g. just a place name)
        own_name = set(re.findall(r"[a-z]+", " ".join(idx[t].get("h1") or []).lower() + " " + idx[t].get("title", "").lower()))
        def vague_anchor(an):
            w = set(re.findall(r"[a-z]+", an))
            if an in GENERIC:
                return True
            if w and w <= own_name and not w <= place_words(t, df):
                return False  # the page's own name (a business or tool name) is a clear anchor
            return not (w & (topic - place_words(t, df)))
        bad = sum(n for an, n in cnt.items() if vague_anchor(an))
        if total >= 3 and bad / total >= 0.6:
            blocks = Counter()
            for an in cnt:
                if vague_anchor(an):
                    blocks.update(anchor_blocks[(t, an)])
            vague.append({"page": t, "links": total, "vague_share": round(bad / total, 2), "top_anchors": cnt.most_common(4),
                          # the real heading of the block these links sit in; use it by name, never invent one
                          "in_blocks": ([b for b, _ in blocks.most_common(3) if b] or ["(no heading above these links)"])
                          if has_blocks else ["unknown: old crawl file, re-crawl to see block headings"]})
    out["vague_anchors"] = sorted(vague, key=lambda x: -x["links"])

    def strength(u):
        return content_in[u] + crumb_in[u] * 0.5 + chrome_in[u] * 0.2 + (gsc.get(u, {}).get("clicks", 0) / 10)

    def closeness(u, t, phrases):
        topic = {w for w in re.findall(r"[a-z]+", " ".join(phrases) + " " + t.lower()) if len(w) > 3}
        mine = set(re.findall(r"[a-z]+", u.lower() + " " + idx.get(u, {}).get("title", "").lower()))
        return len(topic & mine) / max(1, len(topic))

    sugg, no_mentions = {}, []
    for t, spec in targets.items():
        t = path(t)
        phrases = [p.lower() for p in spec.get("phrases", [])]
        rows = []
        for u, p in idx.items():
            if u == t or t in links_from[u] or u.startswith(t.rstrip("/") + "/"):
                continue  # skip the page itself, pages already linking, and its own sub-pages (regional versions)
            text = p.get("text", "")
            low = text.lower()
            hit = next((ph for ph in phrases if ph in low), None)
            if not hit:
                continue
            i = low.find(hit)
            line_start = text.rfind("\n", 0, i) + 1
            line_end = text.find("\n", i)
            block = text[line_start:line_end if line_end != -1 else len(text)]
            j = i - line_start
            starts = [m.end() for m in re.finditer(END, block[:j])]
            start = starts[-1] if starts else 0
            m_end = re.search(END_AT, block[j:])
            sentence = block[start:j + m_end.end()].strip() if m_end else ""
            if len(sentence.split()) < 8:
                continue  # button labels, cards and fragments are not places for a link
            close = closeness(u, t, phrases)
            rows.append({"from": u, "phrase": hit, "sentence": sentence[:300], "donor_strength": round(strength(u), 1),
                         "topic_match": round(close, 2), "score": round(strength(u) * (1 + 2 * close), 1),
                         **({"weak_donor": True} if NOT_DONOR.search(u) else {})})
        good = [x for x in rows if not x.get("weak_donor")]
        rows = good if good else rows   # contact/about/legal pages only when nothing else mentions the topic
        rows.sort(key=lambda x: -x["score"])
        if not rows:
            no_mentions.append({"target": t, "phrases": phrases,
                                "meaning": "no page mentions these words yet: write them into page copy or an article first, then link"})
        sitewide = t in sitewide_targets or chrome_in[t] >= 0.5 * n_crawled
        sugg[t] = {"current_content_links": content_in[t], "sitewide_links": chrome_in[t], "breadcrumb_links": crumb_in[t],
                   "note": "already linked from the menu/header/footer on most pages: never call it weak; add only a few "
                           "strong in-text links from closely related pages" if sitewide else "",
                   "suggested_anchor": spec.get("anchor", ""),
                   "add_links_from": rows[:a.per_target]}
    out["suggestions"] = sugg
    out["no_mentions"] = no_mentions
    # which kinds of page link to each money page at all (any link type): a type at 0 is a template opportunity
    by_type = defaultdict(list)
    for u in idx:
        if u != "/":
            by_type[tkey(u)].append(u)
    cov = {}
    for t in targets:
        t = path(t)
        rows = []
        for k, us in sorted(by_type.items(), key=lambda kv: -len(kv[1])):
            if len(us) < 3 or t in us:
                continue
            n = sum(1 for u in us if t in any_from[u])
            rows.append({"page_type": k, "pages_checked": len(us), "pages_linking": n, "example": us[0]})
        cov[t] = rows
    out["target_coverage"] = cov
    distinct = len({(x["from"], t) for t, v in sugg.items() for x in v["add_links_from"] if not x.get("weak_donor")})
    out["summary"] = {"pages": len(idx), "weak_pages": len(out["weak_pages"]), "vague_anchor_pages": len(vague),
                      "partial_crawl": bool(r.get("limit_reached")),
                      "broken_routes": sum(len(g["targets"]) for g in out["broken_routes"] if g["kind"] == "broken_route"),
                      "missing_pages": sum(len(g["targets"]) for g in out["broken_routes"] if g["kind"] == "missing_page"),
                      "broken_route_patterns": [g["pattern"] for g in out["broken_routes"] if g.get("pattern")],
                      "menu_broken": len(out["menu_broken"]),
                      "strong_opportunities": distinct,
                      "need_more_crawl": bool(targets) and distinct < 10 and bool(r.get("limit_reached")),
                      "targets": {t: len(v["add_links_from"]) for t, v in sugg.items()}, "gsc_used": bool(gsc)}
    print(json.dumps(out, indent=1, ensure_ascii=False))


def tkey(p):
    """Page type from the URL: deep pages by top folder + depth (/hub/*/*), top level pages by the first 3 slug words
    (/plasma-donation-centers-in-*), so siblings of one template land together."""
    parts = p.strip("/").split("/")
    if len(parts) >= 2:
        return "/" + parts[0] + "/*" * (len(parts) - 1)   # /hub/*/* = every city page under the hub
    return "/" + "-".join(re.split(r"[-_]", parts[0])[:3]) + "*"


def siblings_for(t, ok_pages):
    """Working pages of the same kind as t. Deep pages: same top folder and depth. Top level pages: the longest shared
    slug start (2+ words) that 3+ working pages have (/plasma-donation-centers-in-* for .../-in-wilkes-barre-pa)."""
    parts = t.strip("/").split("/")
    if len(parts) >= 2:
        k = tkey(t)
        return k, [u for u in ok_pages if tkey(u) == k]
    toks = [x for x in re.split(r"[-_ ]|%20", parts[0]) if x]
    top = {u: [x for x in re.split(r"[-_ ]|%20", u.strip("/")) if x] for u in ok_pages if u != "/" and "/" not in u.strip("/")}
    for n in range(len(toks) - 1, 1, -1):
        sib = [u for u, tk in top.items() if tk[:n] == toks[:n]]
        if len(sib) >= 3:
            return "/" + "-".join(toks[:n]) + "-*", sib
    return tkey(t), []


def clean_anchor(a):
    return re.sub(r"(?<=[A-Za-z.])\d+.*$", "", a or "").strip()   # "Wilkes-Barre1 center" -> "Wilkes-Barre"


def page_types(pages, links, sample=25):
    """For each page type (URL pattern with 3+ pages): how many sampled pages already have a breadcrumb trail,
    a link up to their parent folder, and a link to the top hub (first URL folder). Read before proposing structure."""
    by = defaultdict(list)
    for u in pages:
        if u != "/":
            by[tkey(u)].append(u)
    out_links = defaultdict(lambda: defaultdict(set))   # from -> area -> {to}
    for l in links:
        out_links[path(l["from"])][l.get("area", "body")].add(path(l["to"]))
    new_crawl = any("breadcrumb_schema" in p for p in pages.values())   # older crawl files can't see breadcrumbs
    res = []
    for k, us in by.items():
        if len(us) < 3:
            continue
        smp = us[:sample]
        def share(f):
            vals = [f(u) for u in smp]
            vals = [v for v in vals if v is not None]
            return round(sum(vals) / len(vals), 2) if vals else "n/a"
        def parent(u):
            return "/" + "/".join(u.strip("/").split("/")[:-1]) if "/" in u.strip("/") else "/"
        def hub(u):
            return "/" + u.strip("/").split("/")[0]
        def links_to(u, t):
            if t not in pages or t == u:
                return None   # no such page (or it's this page): nothing to link to
            return any(t in s for s in out_links[u].values())
        res.append({"type": k,
                    "pages": len(us), "example": us[0],
                    "has_breadcrumb": share(lambda u: bool(out_links[u].get("breadcrumb")) or bool(pages[u].get("breadcrumb_schema")))
                    if new_crawl else "unknown (old crawl file: re-crawl)",
                    "links_to_parent": share(lambda u: None if parent(u) == "/" else links_to(u, parent(u))),
                    "links_to_hub": share(lambda u: links_to(u, hub(u)))})
    return sorted(res, key=lambda x: -x["pages"])


FEATURES = [("a hyphen in the name", lambda a, t: "-" in a),
            ("an apostrophe in the name", lambda a, t: "'" in a or "’" in a),
            ("an accent in the name", lambda a, t: bool(re.search(r"[À-ÿ]", a + t))),
            ("a space in the URL", lambda a, t: " " in t or "%20" in t),
            ("a dot in the name", lambda a, t: bool(re.search(r"\w\.\s?\w", a))),
            ("an ampersand in the name", lambda a, t: "&" in a or "%26" in t),
            ("uppercase letters in the URL", lambda a, t: t != t.lower())]


socket.setdefaulttimeout(20)   # backstop: a slow server can never stall the run
NET_FAILS = [0]                # connection failures/timeouts in a row; 3 in a row = the site stopped answering


def status_of(url):
    """HEAD (GET if the server refuses HEAD). Returns the HTTP status, 0 on a network error."""
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as resp:
                NET_FAILS[0] = 0
                return resp.status
        except urllib.error.HTTPError as e:
            if e.code in (405, 501) and method == "HEAD":
                continue
            return e.code
        except Exception:
            if method == "HEAD":
                continue
            NET_FAILS[0] += 1
            return 0
    return 0


def type_matcher(k):
    """'/plasma-donation-centers-in-*' -> prefix match; '/hub/*/*' -> same folder + depth."""
    if k.endswith("-*") or (k.endswith("*") and "/*" not in k):
        pre = k.rstrip("*")
        return lambda u: u.startswith(pre) and "/" not in u.strip("/")
    parts = k.strip("/").split("/")
    return lambda u: len(u.strip("/").split("/")) == len(parts) and u.strip("/").split("/")[0] == parts[0]


def sitemap_check(r, group, budget):
    """Prove a broken-page pattern: status-check every sitemap URL of this page type that the crawl didn't load.
    Returns (checked, failed list, complete?)."""
    m = type_matcher(group["page_type"])
    crawled = {path(u) for u in r["pages"]}
    known_bad = {it["target"] for it in group["targets"]}
    base = r.get("site") or ""
    todo = [u for u in r.get("sitemap_urls", []) if m(path(u)) and path(u) not in crawled and path(u) not in known_bad]
    checked, failed = 0, []
    t0 = time.time()
    for u in todo[:max(0, budget)]:
        if time.time() - t0 > 10 * 60 or NET_FAILS[0] >= 3:
            why = "the site stopped answering" if NET_FAILS[0] >= 3 else "10 minute limit"
            print(f"STOP time budget reached ({why}): {len(todo) - checked} items not checked (rerun to continue)",
                  file=sys.stderr)
            break
        st = status_of(u if u.startswith("http") else base.rstrip("/") + path(u))
        if st == 0 and NET_FAILS[0]:
            continue  # network error, not a proven broken page
        checked += 1
        if st == 0 or st >= 400:
            failed.append({"target": path(u), "status": st})
        time.sleep(0.2)
    return checked, failed, checked == len(todo)


def broken_routes(r, ok_pages, check_n=0):
    """Group broken internal links. A target the site itself expects (in its own sitemap, or a sibling of a page
    type that works) is a MISSING PAGE / broken route: fix the page, not the link. Then look for the name pattern
    that explains the misses (only reported when every broken one has it and almost no working sibling does)."""
    sm = {path(u) for u in r.get("sitemap_urls", [])}
    broken = defaultdict(list)
    for l in r.get("broken_links", []):
        broken[path(l["to"])].append(l)
    n_from = max(1, len({path(l["from"]) for l in r["links"]}))
    menu = []
    groups = defaultdict(list)
    for t, ls in broken.items():
        anchors = Counter(l.get("anchor", "") for l in ls)
        menu_n = len({path(l["from"]) for l in ls if l.get("area") in ("nav", "header", "footer")})
        if menu_n >= max(3, 0.3 * n_from):
            menu.append({"target": t, "anchor": clean_anchor(anchors.most_common(1)[0][0]), "on_pages": menu_n,
                         "status": ls[0].get("status"), "in_sitemap": t in sm,
                         "ask_owner": "This menu link goes to a page that doesn't exist. Build the page (worth it if it's "
                                      "a popular place or topic people search) or remove the link?"})
        k, siblings_ok = siblings_for(t, ok_pages)
        kind = "missing_page" if (t in sm or len(siblings_ok) >= 3) else "bad_link"
        groups[(kind, k)].append({"target": t, "linked_from_pages": len({path(l["from"]) for l in ls}),
                                  "in_sitemap": t in sm, "anchor": clean_anchor(anchors.most_common(1)[0][0]),
                                  "status": ls[0].get("status"), "_sib": siblings_ok})
    out = []
    for (kind, k), items in groups.items():
        g = {"kind": kind, "page_type": k, "targets": items}
        sib = items[0]["_sib"]
        if kind == "missing_page" and sib:
            sib_anchor = defaultdict(str)
            for l in r["links"]:
                if path(l["to"]) in sib and not sib_anchor[path(l["to"])]:
                    sib_anchor[path(l["to"])] = clean_anchor(l.get("anchor", ""))
            pats = []
            for name, f in FEATURES:
                hit = [it for it in items if f(it["anchor"], it["target"])]
                if len(hit) < 2 and not (hit and name == "a space in the URL"):
                    continue   # one page is not a pattern
                ok_with = [u for u in sib if f(sib_anchor.get(u, ""), u)]
                if len(ok_with) <= 0.02 * len(sib):
                    # say exactly what was compared, so nobody reads "28 work" as "28 with a hyphen work"
                    pats.append(f"Every {g['page_type']} page with {name} gives an error ({len(hit)}: "
                                f"{', '.join(it['anchor'] or it['target'] for it in hit[:6])}). "
                                f"{len(sib)} pages of this type load fine and "
                                f"{'none' if not ok_with else len(ok_with)} of them has {name}"
                                f"{' (' + ', '.join(sib_anchor.get(u, u) for u in ok_with[:3]) + ')' if ok_with else ''}. "
                                f"Fix how the site builds these addresses.")
            if pats:
                g["pattern"] = " ".join(pats)
            g["names_compared"] = "link text of each page (the real place or business name), not the URL"
            expected = [it for it in items if it["in_sitemap"]]
            if expected or pats:
                g["kind"] = "broken_route"
                g["fix"] = ("Your own site expects these pages (they're in its sitemap, or the same kind of page works for "
                            "other names). Fix how the site builds these page addresses so they load; don't remove the links.")
            else:
                g["fix"] = ("These pages don't exist, but the same kind of page does for other places. Ask the owner: build "
                            "them (worth it for places people search) or point the links elsewhere?")
        else:
            g["fix"] = "Point these links at the right page or remove them."
        for it in items:
            it.pop("_sib", None)
        if check_n and g["kind"] in ("missing_page", "broken_route"):
            n, failed, complete = sitemap_check(r, g, check_n)
            g["sitemap_check"] = {"checked": n, "also_failing": failed, "complete": complete,
                                  "note": "every sitemap URL of this page type the crawl didn't load was status-checked"
                                          if complete else f"only {n} checked (budget): say 'at least', never 'only these'"}
            if failed:
                g["kind"] = "broken_route"   # the site's own sitemap lists pages that don't load
                g["pattern"] = (g.get("pattern", "") + f" The sitemap check found {len(failed)} more page(s) of this type "
                                f"that fail ({', '.join(f['target'] for f in failed[:5])}): look up their real names in the "
                                f"listings to confirm they share the pattern.").strip()
                for f in failed:
                    g["targets"].append({"target": f["target"], "linked_from_pages": 0, "in_sitemap": True, "anchor": "",
                                         "status": f["status"], "found_by": "sitemap_check"})
        elif g["kind"] in ("missing_page", "broken_route"):
            g["sitemap_check"] = {"checked": 0, "complete": False,
                                  "note": "not checked: rerun with --check-sitemap 1500 before saying which other pages work"}
        out.append(g)
    order = {"broken_route": 0, "missing_page": 1, "bad_link": 2}
    return sorted(out, key=lambda g: (order[g["kind"]], -sum(i["linked_from_pages"] for i in g["targets"]))), \
        sorted(menu, key=lambda x: -x["on_pages"])


def place_words(page_path, df):
    """Words in the page's URL that few other URLs share are its place or name (florida, new york).
    Words many URLs share are the template, i.e. the topic. An anchor made only of place words
    ("Florida") doesn't tell Google what the page is about."""
    return {w for w in re.findall(r"[a-z]+", page_path.lower()) if df[w] < 3}

if __name__ == "__main__":
    sys.exit(main())
