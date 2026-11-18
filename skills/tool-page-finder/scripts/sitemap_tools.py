#!/usr/bin/env python3
"""Find a competitor's tool pages from its sitemap (free proof of what works).

Usage: python3 sitemap_tools.py competitor-one.com competitor-two.com
Reads robots.txt -> sitemap(s) -> follows sitemap indexes (max 30 files),
prints URLs whose path looks like a tool page. Stdlib only.
"""
import re, sys, urllib.request, gzip

TOOL = re.compile(r"(calculator|calc|estimator|converter|checker|lookup|finder|generator|"
                  r"tool|tools|chart|quiz|test|compare|fee|fees|cost|price|worth|value|map)", re.I)

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        b = r.read()
    if url.endswith(".gz") or b[:2] == b"\x1f\x8b":
        b = gzip.decompress(b)
    return b.decode("utf-8", "replace")

def sitemaps(domain):
    base = f"https://{domain}"
    found = []
    try:
        found = re.findall(r"(?im)^sitemap:\s*(\S+)", get(base + "/robots.txt"))
    except Exception: pass
    return found or [base + "/sitemap.xml", base + "/sitemap_index.xml"]

def main():
    for domain in sys.argv[1:]:
        queue, seen, urls = sitemaps(domain), set(), set()
        while queue and len(seen) < 30:
            sm = queue.pop(0)
            if sm in seen: continue
            seen.add(sm)
            try: xml = get(sm)
            except Exception as e:
                print(f"  warn {sm}: {e}", file=sys.stderr); continue
            locs = re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", xml)
            if "<sitemapindex" in xml: queue += locs
            else: urls.update(locs)
        tools = sorted(u for u in urls if TOOL.search(u.split("/", 3)[-1]))
        print(f"== {domain}: {len(urls)} URLs, {len(tools)} tool-like")
        for u in tools[:200]: print("  ", u)

if __name__ == "__main__":
    main()
