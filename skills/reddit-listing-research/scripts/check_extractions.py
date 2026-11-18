"""Step 11. Anti made-up-facts check. For every value the AI filled in staging/<id>.json,
confirm its "quote" really appears in that listing's downloaded website text (sites/<id>.txt).
Values whose quote is not found are marked REJECTED. Free. Instant.
Chain facts: a value with "scope": "chain" is checked against sites/_chains/<domain>.txt (chain_pages.py) and marked
VERIFIED (company policy, all <Chain> locations). Money values (fields with type price, or "money": true) are never
taken from company pages: NOT USED. research.json "company_facts": "never" turns chain facts off.
Every money value gets an "as of" date (the day its page was downloaded).
Chain boilerplate: a quote from a location page that also appears on OTHER locations' pages of the same chain
(sites/_chains/<domain>.siblings.txt, made by chain_pages.py) is labeled "same wording on every <Chain> location page".
At the end it prints CHAIN MULTIPLIER lines: company-wide facts x how many listings that chain has.
Usage: python3 scripts/check_extractions.py
Writes output/review.csv (one row per listing per field) for the human to approve."""
import csv, json, os, re
import common  # noqa: F401  (prints this script's help on --help)


def norm(s):
    # ignore spacing, case, and curly vs straight quotes so formatting never causes a false REJECT
    s = (s or "").lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", "", s)


SCOPE = re.compile(r"select locations?|participating|some locations|most locations|at certain locations|varies by location|may vary|where available", re.I)
import time
types, money = {}, set()
if os.path.exists("output/fields.json"):
    for f in json.load(open("output/fields.json")):
        types[f["field"]] = f.get("type", "")
        if f.get("type") == "price" or f.get("money"):
            money.add(f["field"])
try:
    company_facts = json.load(open("research.json")).get("company_facts", "ask")
except Exception:
    company_facts = "ask"
chains = json.load(open("sites/_chains/chains.json")) if os.path.exists("sites/_chains/chains.json") else {}


def as_of(path):
    return time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(path))) if os.path.exists(path) else time.strftime("%Y-%m-%d")
rows, ok, bad, unknown, scope = [], 0, 0, 0, 0
# Chain websites: a domain used by 2+ listings. A value from it counts only if the quoted page shows this
# listing's street number + street word (so it's about THIS location), otherwise CHECK SCOPE.
from urllib.parse import urlparse
listing = {}
if os.path.exists("data/listings.csv"):
    for r in csv.DictReader(open("data/listings.csv", newline="")):
        listing[str(r.get("id"))] = r
dom_count = {}
for r in listing.values():
    d = urlparse(r.get("website") or "").netloc.replace("www.", "")
    if d:
        dom_count[d] = dom_count.get(d, 0) + 1


def page_text(lid, url):
    if not os.path.exists(f"sites/{lid}.txt"):
        return ""
    t = open(f"sites/{lid}.txt").read()
    parts = t.split("=== PAGE: ")
    for p in parts:
        if p.startswith(url):
            return p
    return t


ADDR = re.compile(r"\b\d{2,6}\s+[A-Za-z0-9.]+(?:\s+[A-Za-z0-9.]+){0,3}\s+(?:st|street|rd|road|ave|avenue|blvd|boulevard|dr|drive|ln|lane|pkwy|parkway|hwy|highway|way|ct|court|pl|place|loop|trail|trl)\b", re.I)


def is_chain_site(lid):
    """A website that lists 3+ different street addresses is a chain (or multi-location) site."""
    if not os.path.exists(f"sites/{lid}.txt"):
        return False
    found = {m.group(0).lower() for m in ADDR.finditer(open(f"sites/{lid}.txt").read())}
    return len(found) >= 3


def on_this_location(lid, url):
    r = listing.get(str(lid), {})
    d = urlparse(r.get("website") or "").netloc.replace("www.", "")
    if dom_count.get(d, 0) < 2 and not is_chain_site(lid):
        return True  # one business, one location: the whole site is about this listing
    addr = (r.get("address") or "").lower()
    m = re.match(r"\s*(\d+)\s+([a-z]+)", addr.replace(".", ""))
    if not m:
        return False
    page = norm(page_text(lid, url))
    return m.group(1) in page and m.group(2) in page
chain_ok = 0
for f in sorted(os.listdir("staging")):
    if not f.endswith(".json"):
        continue
    lid = f[:-5]
    site = norm(open(f"sites/{lid}.txt").read()) if os.path.exists(f"sites/{lid}.txt") else ""
    dom = urlparse(listing.get(lid, {}).get("website") or "").netloc.lower().replace("www.", "")
    data = json.load(open(f"staging/{f}"))
    for field, v in data.get("fields", {}).items():
        val = v.get("value")
        label, when = "", ""
        if val in (None, "", "unknown"):
            unknown += 1
            status = "UNKNOWN"
        elif v.get("scope") == "chain":
            cpath = f"sites/_chains/{dom}.txt"
            ctext = norm(open(cpath).read()) if os.path.exists(cpath) else ""
            if company_facts == "never":
                unknown += 1
                status = "NOT USED (owner said: this location's own page only)"
            elif field in money:
                unknown += 1
                status = "NOT USED (company-wide amount: amounts vary by location and month, only this location's own page counts)"
            elif v.get("quote") and ctext and norm(v["quote"]) in ctext:
                ok += 1; chain_ok += 1
                status = "VERIFIED"
                label = f"company policy, all {chains.get(dom, {}).get('chain') or dom} locations"
            else:
                bad += 1
                status = "REJECTED (quote not on the chain's company pages)"
        elif v.get("quote") and norm(v["quote"]) in site and (SCOPE.search(v["quote"]) or not on_this_location(lid, v.get("source_url", ""))):
            scope += 1
            status = "CHECK SCOPE (chain website or 'select locations': this location isn't confirmed on the quoted page)"
        elif (v.get("quote") and norm(v["quote"]) in site and types.get(field) in ("price", "number")
              and not set(re.findall(r"\d+(?:\.\d+)?", str(val))) <= set(re.findall(r"\d+(?:\.\d+)?", v["quote"]))):
            bad += 1
            status = "REJECTED (the number is not in the quote)"
        elif v.get("quote") and norm(v["quote"]) in site:
            ok += 1
            status = "VERIFIED"
            label = "this location's own page"
            spath = f"sites/_chains/{dom}.siblings.txt"
            if os.path.exists(spath) and norm(v["quote"]) in norm(open(spath).read()):
                label = f"same wording on every {chains.get(dom, {}).get('chain') or dom} location page"
                chain_ok += 1
        else:
            bad += 1
            status = "REJECTED (quote not on site)"
        if status == "VERIFIED" and field in money:
            when = as_of(f"sites/{lid}.txt")
        rows.append({"listing_id": lid, "name": data.get("name", ""), "field": field,
                     "value": val, "status": status, "scope": label, "as_of": when,
                     "source_url": v.get("source_url", ""), "quote": v.get("quote", ""), "approve (y/n)": ""})
os.makedirs("output", exist_ok=True)
with open("output/review.csv", "w", newline="") as out:
    w = csv.DictWriter(out, fieldnames=list(rows[0].keys()) if rows else ["listing_id"])
    w.writeheader(); w.writerows(rows)
print(f"VERIFIED {ok} (of which company policy: {chain_ok}) | REJECTED {bad} | CHECK SCOPE {scope} | UNKNOWN {unknown} -> output/review.csv")
filled = ok + scope
total = ok + bad + scope + unknown
if total:
    print(f"FILL RATE {ok}/{total} values ({100 * ok // total}%)")
if ok + bad and bad / (ok + bad) > 0.15:
    print("WARNING: more than 15% rejected. Stop and re read the extraction rules in Step 10.")

# How far each chain fact reaches: a company-wide fact found once applies to every listing of that chain.
reach = {}
for r in rows:
    # amounts never multiply: another location may show a different number, even when two pages match
    if r["status"] == "VERIFIED" and r["scope"] and r["scope"] != "this location's own page" and r["field"] not in money:
        d = urlparse(listing.get(r["listing_id"], {}).get("website") or "").netloc.lower().replace("www.", "")
        reach.setdefault(d, set()).add(r["field"])
reach_total = [0, 0, 0]
for d, fields in sorted(reach.items(), key=lambda x: -len(x[1])):
    n = chains.get(d, {}).get("listings") or dom_count.get(d, 0)
    name = chains.get(d, {}).get("chain") or d
    print(f"CHAIN MULTIPLIER {name}: {len(fields)} company-wide facts ({', '.join(sorted(fields))}) apply to all {n} {name} listings")
    reach_total[0] += len(fields); reach_total[1] += len(fields) * n; reach_total[2] += n
if reach:
    print(f"CHAIN REACH TOTAL: {reach_total[0]} company-wide facts fill about {reach_total[1]} values across "
          f"{reach_total[2]} listings. Lead the owner report with this line.")

# Rule 7 guard: blocked sites must be tried with the agent's built-in web reader before anything is "unknown".
if os.path.exists("sites/_failed.txt"):
    tried = set(open("sites/_webreader_tried.txt").read().split()) if os.path.exists("sites/_webreader_tried.txt") else set()
    todo = []
    for line in open("sites/_failed.txt").read().splitlines():
        parts = line.split(",")
        if len(parts) >= 3 and "blocked_by_security" in line and not os.path.exists(f"sites/{parts[0]}.txt") and parts[0] not in tried:
            todo.append((parts[0], parts[1]))
    if todo:
        print(f"STOP: {len(todo)} blocked site(s) not yet tried with your built-in web reader (Rule 7). "
              "Read each URL below with it, save the text to sites/<id>.txt as '=== PAGE: <url>' + text, "
              "or if the reader is blocked too, add the id to sites/_webreader_tried.txt. Then rerun this checker. "
              "Never ask the owner to paste pages.")
        for lid, url in todo[:20]:
            print(f"  READ {lid} {url}")
