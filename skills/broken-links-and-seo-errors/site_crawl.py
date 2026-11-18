#!/usr/bin/env python3
"""Free site crawler for broken-links-and-seo-errors and internal-links. No API keys, no paid tools.

    python3 site_crawl.py crawl https://example.com --out /tmp/crawl.json [--max 600]
    python3 site_crawl.py old-urls https://example.com --out /tmp/old.json      # Wayback Machine: old URLs that now 404

crawl: reads the sitemap (sitemap.xml, sitemap_index.xml, robots.txt Sitemap: lines), then follows
internal links from the homepage too, so pages missing from the sitemap are found. For every page it
records: status, final URL after redirects, title, H1s, meta description, canonical, robots noindex,
word count, years in the title, and every internal link (target + anchor text + whether it sits in
the nav/header/footer). Then it checks every linked internal URL that wasn't crawled (broken links).

Link "area" is body | nav | header | footer | breadcrumb (aria-label/class "breadcrumb", or a nav that starts with
"Home" and walks up the URL). "block" = the nearest h2-h6 heading above the link (the block's real name). Each page also gets "breadcrumb_schema" (BreadcrumbList item URLs from JSON-LD).
--spread samples every page type first (good with a small --max); --check-uncrawled N checks linked pages the crawl
didn't reach (status only, in "link_status"), so broken links are found even on a partial crawl.

Output JSON: {"site", "crawled_at", "pages": {url: {...}}, "links": [{"from","to","anchor","area","block"}],
              "broken_links": [{"from","to","status","anchor"}], "redirected_links": [...], "sitemap_urls": [...]}
Prints a short summary. Polite: 6 parallel requests, identifies itself, respects --max.
"""
import argparse
import concurrent.futures as cf
import datetime
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

UA = "Mozilla/5.0 (compatible; directory-ops/1.0; +https://github.com/Directoryops/directory-ops)"
BLOCKED = {}  # url -> "vercel" | "cloudflare" | "other" when the site's security answered instead of the page


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
SKIP_EXT = re.compile(r"\.(jpg|jpeg|png|gif|webp|svg|pdf|zip|mp4|mp3|css|js|ico|xml|txt|json|woff2?|ttf|eot|webmanifest)(\?|$)|/_next/|/wp-content/|/wp-includes/", re.I)


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title, self.h1, self.links, self.meta = "", [], [], {}
        self.canonical, self._in, self._a, self._area, self._text = "", None, None, [], []
        self._skip, self.body_text, self._heading = 0, [], 0
        self._bc, self._group, self._groups = None, 0, []   # breadcrumb container [tag, depth]; link group ids
        self._ld, self.ld_json = False, []                    # JSON-LD blocks (for BreadcrumbList)
        self._htext, self.last_heading = None, ""            # nearest heading above each link (its block's real name)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "noscript", "svg"):
            self._skip += 1
        if tag == "script" and "ld+json" in (a.get("type") or "").lower():
            self._ld = True
            self.ld_json.append("")
        if self._bc is not None and tag == self._bc[0]:
            self._bc[1] += 1
        elif self._bc is None and "breadcrumb" in " ".join(str(a.get(k) or "") for k in ("aria-label", "class", "id")).lower():
            self._bc = [tag, 1]
            self._group += 1
            self._groups.append(self._group)
        if tag in ("h2", "h3", "h4", "h5", "h6"):
            self._heading += 1
            self._htext = ""
        if tag in ("nav", "header", "footer"):
            self._area.append(tag)
            self._group += 1
            self._groups.append(self._group)
        if tag == "title":
            self._in = "title"
        elif tag == "h1":
            self._in = "h1"
            self.h1.append("")
        elif tag == "a" and a.get("href"):
            self._a = {"href": a["href"], "text": "", "area": "breadcrumb" if self._bc else (self._area[-1] if self._area else "body"),
                       "group": self._groups[-1] if (self._bc or self._area) and self._groups else 0,
                       "block": self.last_heading}
        elif tag == "meta" and a.get("name"):
            self.meta[a["name"].lower()] = a.get("content", "")
        elif tag == "link" and (a.get("rel") or "").lower() == "canonical":
            self.canonical = a.get("href", "")
        elif tag == "img" and self._a is not None and a.get("alt"):
            self._a["text"] += " " + a["alt"]

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "svg") and self._skip:
            self._skip -= 1
        if tag == "script":
            self._ld = False
        if self._bc is not None and tag == self._bc[0]:
            self._bc[1] -= 1
            if self._bc[1] <= 0:
                self._bc = None
                if self._groups:
                    self._groups.pop()
        if tag in ("h2", "h3", "h4", "h5", "h6") and self._heading:
            self._heading -= 1
            if self._htext is not None:
                self.last_heading = re.sub(r"\s+", " ", self._htext).strip()[:80]
                self._htext = None
        if tag in ("p", "div", "li", "td", "th", "section", "article", "h1", "h2", "h3", "h4", "h5", "h6", "button", "span", "a"):
            self.body_text.append("\n")  # keep blocks apart so sentences never run across cards or buttons
        if tag in ("nav", "header", "footer") and self._area:
            self._area.pop()
            if self._groups and self._bc is None:
                self._groups.pop()
        if tag in ("title", "h1"):
            self._in = None
        if tag == "a" and self._a is not None:
            self._a["text"] = re.sub(r"\s+", " ", self._a["text"]).strip()
            self.links.append(self._a)
            self._a = None

    def handle_data(self, data):
        if self._ld and self.ld_json:
            self.ld_json[-1] += data
        if self._skip:
            return
        if not self._area and self._in is None and not self._heading:
            self.body_text.append(data)
        if self._in == "title":
            self.title += data
        elif self._in == "h1":
            self.h1[-1] += data
        if self._a is not None:
            self._a["text"] += data
        if self._htext is not None:
            self._htext += data
        self._text.append(data)


def mark_breadcrumbs(links, page_url):
    """An unlabeled breadcrumb trail: a link group (nav/header) that starts with a "Home" link to "/" and whose
    other links walk UP this page's URL (/hub, /hub/state). Mark those links area="breadcrumb"."""
    me = urllib.parse.urlparse(page_url).path.rstrip("/") + "/"
    groups = {}
    for l in links:
        if l.get("group") and l["area"] in ("nav", "header", "body"):
            groups.setdefault(l["group"], []).append(l)
    for g in groups.values():
        if len(g) < 2 or g[0]["text"].strip().lower() not in ("home", "homepage"):
            continue
        paths = [urllib.parse.urlparse(urllib.parse.urljoin(page_url, l["href"])).path.rstrip("/") for l in g[1:]]
        if paths and all(p and me.startswith(p + "/") and p + "/" != me for p in paths):
            for l in g:
                l["area"] = "breadcrumb"


# Run guards: a dead or slow site can never stall the run.
socket.setdefaulttimeout(20)
HOST_FAILS = {}    # host -> connection failures/timeouts so far
DEAD_HOSTS = set()  # after 3 failures a host is skipped for the rest of the run (not after an HTTP error)
SKIPPED = set()     # URLs not fetched because their host was dead or the time budget ran out (never "broken")
DEADLINE = [0.0]    # time.time() after which no new page is fetched (0 = no limit)


def out_of_time():
    return bool(DEADLINE[0]) and time.time() > DEADLINE[0]


def fetch(url, method="GET"):
    """Returns (status, final_url, body_text). Follows redirects."""
    host = urllib.parse.urlsplit(url).netloc.lower()
    if host in DEAD_HOSTS or out_of_time():
        SKIPPED.add(url)
        return 0, url, ""
    parts = urllib.parse.urlsplit(url)
    url = urllib.parse.urlunsplit(parts._replace(path=urllib.parse.quote(parts.path, safe="/%:@!$&'()*+,;=-._~")))
    req = urllib.request.Request(url, headers={"User-Agent": UA}, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=20)
        body = r.read().decode("utf-8", "ignore") if method == "GET" else ""
        FETCHED.append(1)
        HOST_FAILS[host] = 0
        return r.status, r.geturl(), body
    except urllib.error.HTTPError as e:
        try:
            body = e.read(20000).decode("utf-8", "ignore")
        except Exception:  # noqa: BLE001
            body = ""
        b = security_block(e.code, dict(e.headers or {}), body, first=not BLOCKED and not FETCHED)
        if b:
            BLOCKED[url] = b
        FETCHED.append(1)
        return e.code, url, ""
    except Exception:  # noqa: BLE001  (connection failure or timeout)
        HOST_FAILS[host] = HOST_FAILS.get(host, 0) + 1
        if HOST_FAILS[host] >= 3:
            DEAD_HOSTS.add(host)
        return 0, url, ""


FETCHED = []


def norm(url, base):
    u = urllib.parse.urljoin(base, url.split("#")[0].strip())
    p = urllib.parse.urlparse(u)
    if p.scheme not in ("http", "https"):
        return None
    path = p.path or "/"
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return urllib.parse.urlunparse((p.scheme, p.netloc.lower(), path, "", p.query, ""))


def same_site(u, host):
    h = urllib.parse.urlparse(u).netloc.lower()
    return h.replace("www.", "") == host.replace("www.", "")


SPACES = []


def sitemap_urls(root):
    found, todo, seen = [], [root + "/sitemap.xml", root + "/sitemap_index.xml"], set()
    st, _, robots = fetch(root + "/robots.txt")
    todo += re.findall(r"(?im)^sitemap:\s*(\S+)", robots or "")
    while todo:
        sm = todo.pop()
        if sm in seen:
            continue
        seen.add(sm)
        st, _, xml = fetch(sm)
        if st != 200:
            continue
        raw = [l.strip() for l in re.findall(r"<loc>\s*([^<]+?)\s*</loc>", xml)]
        SPACES.extend(l for l in raw if " " in l)
        locs = [l.replace(" ", "%20") for l in raw]
        if "<sitemapindex" in xml:
            todo += locs
        else:
            found += locs
    return found


def template_key(u):
    """Page type guess from the URL: parent folder + first word of the last part (/state/city -> '/state|city...')."""
    parts = urllib.parse.urlparse(u).path.strip("/").split("/")
    return "/".join(parts[:-1]) + "|" + (re.split(r"[-_]", parts[-1])[0] if parts and parts[-1] else "") + f"|{len(parts)}"


def spread(urls):
    """Round robin over page types so a small --max covers every type, not just the first 300 sitemap lines."""
    by = {}
    for u in urls:
        by.setdefault(template_key(u), []).append(u)
    out, lists = [], list(by.values())
    while any(lists):
        for L in lists:
            if L:
                out.append(L.pop(0))
    return out


def crawl(root, max_pages, do_spread=False, check_uncrawled=300):
    root = root.rstrip("/")
    st, final_root, _ = fetch(root)
    root = norm(final_root, final_root).rstrip("/") if st == 200 else root
    host = urllib.parse.urlparse(root).netloc
    sm = [norm(u, root) for u in sitemap_urls(root)]
    sm = [u for u in sm if u and same_site(u, host)]
    queue, seen = [norm(root, root)] + (spread(sm) if do_spread else sm), set()
    pages, links = {}, []

    def work(url):
        status, final, body = fetch(url)
        info = {"status": status, "final_url": final if final != url else ""}
        if url in BLOCKED:
            info["blocked_by"] = BLOCKED[url]
        if url in SKIPPED:
            info["skipped"] = True
        if status == 200 and body and "<html" in body[:2000].lower():
            p = Page()
            try:
                p.feed(body)
            except Exception:  # noqa: BLE001
                pass
            words = len(re.findall(r"[A-Za-z]{2,}", " ".join(p._text)))
            info.update({
                "title": re.sub(r"\s+", " ", p.title).strip(),
                "h1": [re.sub(r"\s+", " ", h).strip() for h in p.h1 if h.strip()],
                "meta_description": p.meta.get("description", ""),
                "noindex": "noindex" in p.meta.get("robots", "").lower(),
                "canonical": p.canonical,
                "words": words,
                "title_years": re.findall(r"\b20\d\d\b", p.title),
                "text": re.sub(r"[ \t]+", " ", re.sub(r"\s*\n\s*", "\n", "".join(p.body_text)))[:20000],  # main content only (no nav/header/footer)
            })
            mark_breadcrumbs(p.links, final)
            bc_schema = []
            for blk in p.ld_json:
                if "breadcrumblist" in blk.lower():
                    bc_schema += [u for u in re.findall(r'"item"\s*:\s*(?:\{[^}]*?"@id"\s*:\s*)?"([^"]+)"', blk)]
            info["breadcrumb_schema"] = [norm(u, final) for u in bc_schema if norm(u, final)][:8]
            out = []
            for l in p.links:
                t = norm(l["href"], final)
                if t and same_site(t, host) and not SKIP_EXT.search(t):
                    out.append({"from": url, "to": t, "anchor": l["text"][:120], "area": l["area"],
                                "block": l.get("block", "")})  # area: body|nav|header|footer|breadcrumb
            return url, info, out
        return url, info, []

    with cf.ThreadPoolExecutor(6) as ex:
        while queue and len(pages) < max_pages and not out_of_time():
            batch = []
            while queue and len(batch) < 24 and len(pages) + len(batch) < max_pages:
                u = queue.pop(0)
                if u not in seen:
                    seen.add(u)
                    batch.append(u)
            for url, info, out in ex.map(work, batch):
                pages[url] = info
                links += out
                for l in out:
                    if l["to"] not in seen and "?" not in l["to"]:
                        queue.append(l["to"])

    # linked internal URLs the crawl never reached (limit): check the most linked ones' status only (not added to pages)
    link_status = {}
    uncrawled = {}
    for l in links:
        if l["to"] not in pages and "?" not in l["to"]:
            uncrawled[l["to"]] = uncrawled.get(l["to"], 0) + 1
    todo = sorted(uncrawled, key=lambda u: -uncrawled[u])[:check_uncrawled]
    if todo:
        with cf.ThreadPoolExecutor(6) as ex:
            for u, (st, fin, _) in zip(todo, ex.map(lambda u: fetch(u, "HEAD"), todo)):
                if st in (405, 501):
                    st, fin, _ = fetch(u)
                if u in BLOCKED or u in SKIPPED:
                    continue
                link_status[u] = {"status": st, "final_url": fin if fin != u else ""}
    broken, redirected = [], []
    for l in links:
        info = pages.get(l["to"]) or link_status.get(l["to"])
        if info is None:
            continue
        if info.get("blocked_by") or info.get("skipped"):
            continue  # security answered (blocked) or never fetched (dead host / time budget): not broken
        if info["status"] >= 400 or info["status"] == 0:
            broken.append({**l, "status": info["status"]})
        elif info.get("final_url") and norm(info["final_url"], root) != l["to"]:
            redirected.append({**l, "final_url": info["final_url"]})
    return {"site": root, "crawled_at": datetime.date.today().isoformat(), "pages": pages, "links": links,
            "broken_links": broken, "redirected_links": redirected, "sitemap_urls": sm, "link_status": link_status,
            "limit_reached": len(pages) >= max_pages,
            "sitemap_raw_spaces": len(SPACES), "sitemap_space_examples": SPACES[:3],
            "blocked_by_security": sorted(set(BLOCKED.values()))[0] if BLOCKED else None,
            "blocked_pages": len(BLOCKED),
            "stopped_early": out_of_time(), "not_checked": len(SKIPPED) + (len(queue) if out_of_time() else 0),
            "dead_hosts": sorted(DEAD_HOSTS)}


def old_urls(root):
    """Old URLs from the Wayback Machine that now return 404: redirect candidates (they may still have backlinks)."""
    host = urllib.parse.urlparse(root.rstrip("/")).netloc.replace("www.", "")
    api = ("https://web.archive.org/cdx/search/cdx?url=" + host + "/*&output=json&fl=original"
           "&filter=statuscode:200&collapse=urlkey&limit=5000")
    rows = None
    for wait in (0, 5, 15, 30):
        time.sleep(wait)
        st, _, body = fetch(api)
        try:
            rows = json.loads(body)[1:]
            break
        except Exception:  # noqa: BLE001
            continue
    if rows is None:
        return {"error": "Wayback Machine did not answer after 4 tries; skip this check this run", "dead": []}
    urls = sorted({norm(r[0], root) for r in rows if r and not SKIP_EXT.search(r[0])} - {None})
    urls = [u for u in urls if "?" not in u]
    dead = []

    def chk(u):
        live = "https://" + urllib.parse.urlparse(root).netloc + urllib.parse.urlparse(u).path
        s, final, _ = fetch(live)
        if live in SKIPPED:
            s = None
        return live, s

    with cf.ThreadPoolExecutor(6) as ex:
        for live, s in ex.map(chk, urls[:1500]):
            if s == 404 or s == 410:
                dead.append(live)
    return {"checked": min(len(urls), 1500) - len(SKIPPED), "dead": sorted(set(dead)),
            "stopped_early": out_of_time(), "not_checked": len(SKIPPED)}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("crawl")
    c.add_argument("site")
    c.add_argument("--out", required=True)
    c.add_argument("--max", type=int, default=3000)
    c.add_argument("--spread", action="store_true", help="sample every page type first (use with a small --max)")
    c.add_argument("--check-uncrawled", type=int, default=300, help="also check the status of up to N linked pages the crawl didn't reach")
    c.add_argument("--max-minutes", type=float, default=30, help="stop fetching new pages after this many minutes")
    o = sub.add_parser("old-urls")
    o.add_argument("site")
    o.add_argument("--out", required=True)
    o.add_argument("--max-minutes", type=float, default=15, help="stop checking old URLs after this many minutes")
    a = ap.parse_args()
    if getattr(a, "out", None):  # create the output folder (notes/<site>/...) if it is new
        import os as _os
        _os.makedirs(_os.path.dirname(_os.path.abspath(a.out)), exist_ok=True)
    if a.max_minutes:
        DEADLINE[0] = time.time() + a.max_minutes * 60
    if a.cmd == "crawl":
        r = crawl(a.site, a.max, a.spread, a.check_uncrawled)
        json.dump(r, open(a.out, "w"))
        if r["stopped_early"]:
            print(f"STOP time budget reached: {r['not_checked']} items not checked (rerun with a bigger --max-minutes, "
                  f"or --spread with a smaller --max, to cover them)", file=sys.stderr)
        ok = sum(1 for p in r["pages"].values() if p["status"] == 200)
        print(json.dumps({"pages": len(r["pages"]), "ok": ok, "links": len(r["links"]),
                          "broken_links": len(r["broken_links"]), "redirected_links": len(r["redirected_links"]),
                          "sitemap_urls": len(r["sitemap_urls"]), "limit_reached": r["limit_reached"], "out": a.out,
                          "stopped_early": r["stopped_early"], "not_checked": r["not_checked"],
                          **({"blocked_by_security": r["blocked_by_security"], "blocked_pages": r["blocked_pages"],
                              "note": "The site's security blocked automated visitors on these pages (not broken). Check a small "
                                      "sample with your built-in web reader now; for a full crawl offer the owner "
                                      "setup-guides/guides/let-hermes-past-security.md (one yes/no)."}
                             if r["blocked_by_security"] else {})}))
    else:
        r = old_urls(a.site)
        json.dump(r, open(a.out, "w"))
        if r.get("stopped_early"):
            print(f"STOP time budget reached: {r['not_checked']} items not checked (rerun to continue)", file=sys.stderr)
        print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in r.items()}))


if __name__ == "__main__":
    sys.exit(main())
