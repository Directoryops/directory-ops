#!/usr/bin/env python3
"""Quick, plain look at a list of businesses right after onboarding finds it. Free, no AI, read only.

    python3 listing_quality.py rows.json            # output of: db.py select --all ... > rows.json
    python3 listing_quality.py listings.csv         # a spreadsheet export
    python3 listing_quality.py data/listings.json   # a JSON list from a site's code

Prints JSON:
  count                     how many listings
  missing                   % empty per key field it can find (phone, website, hours, address, description, map point)
  duplicates                listings sharing the same street address or the same phone
  placeholder               {"likely": bool, "signals": [...], "examples": [...]}: TEST / FAKE data. Only strong signals
                            count: 555 phone numbers, example.com / .example / .test / .invalid websites,
                            "lorem ipsum", or the words test/sample/dummy/placeholder in names or addresses.
                            A made-up-sounding business name alone is never enough.
  plain_summary             2 to 4 owner-friendly bullets (no technical words)

How onboarding uses it: confirm the count with ONE question ("I found 6 groomers in your file. Is that all of them?"),
share one useful finding, and if placeholder.likely is true, say so plainly and hold every helper that needs real
listings ("I'll start these once your real listings are in"). Never schedule helpers on test data.
"""
import csv
import json
import re
import sys
from collections import defaultdict

FIELDS = {
    "phone": ["phone", "phone_number", "telephone", "tel", "contact_phone"],
    "website": ["website", "url", "site", "web", "website_url", "homepage"],
    "hours": ["hours", "opening_hours", "hours_of_operation", "working_hours", "business_hours"],
    "address": ["address", "street", "street_address", "full_address", "location", "addr"],
    "description": ["description", "about", "summary", "details", "bio"],
    "map point": ["lat", "latitude", "lng", "lon", "longitude", "coordinates", "geo"],
}
PLAIN = {"phone": "a phone number", "website": "a website", "hours": "hours", "address": "an address",
         "description": "a description", "map point": "a map location"}
FAKE_PHONE = re.compile(r"(?<!\d)(?:\(?\d{3}\)?[\s.-]*)?555[\s.-]*\d{4}(?!\d)")
FAKE_SITE = re.compile(r"(?:^|[/.@])(example\.(com|org|net)|[a-z0-9-]+\.(example|test|invalid|localhost))(?:[/:]|$)", re.I)
FAKE_WORDS = re.compile(r"\b(lorem ipsum|test listing|test business|sample listing|dummy|placeholder|fake)\b", re.I)
FAKE_NAME_WORD = re.compile(r"^\s*(test|sample|demo)\b", re.I)


def load(path):
    if path.lower().endswith(".csv"):
        with open(path, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    data = json.load(open(path, encoding="utf-8"))
    if isinstance(data, dict):
        for k in ("rows", "listings", "data", "items", "businesses", "results"):
            if isinstance(data.get(k), list):
                return data[k]
        lists = [v for v in data.values() if isinstance(v, list)]
        return lists[0] if lists else []
    return data if isinstance(data, list) else []


def empty(v):
    return v is None or (isinstance(v, str) and not v.strip()) or v == [] or v == {}


def pick(row_keys, names):
    low = {k.lower(): k for k in row_keys}
    for n in names:
        if n in low:
            return low[n]
    for k in row_keys:  # loose match, e.g. "business_phone"
        if any(n in k.lower() for n in names if len(n) > 3):
            return k
    return None


def norm_addr(a):
    a = re.sub(r"[^a-z0-9 ]", " ", str(a).lower())
    return re.sub(r"\s+", " ", a).strip()[:40]


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        return 0
    rows = [r for r in load(sys.argv[1]) if isinstance(r, dict)]
    n = len(rows)
    keys = set().union(*(r.keys() for r in rows)) if rows else set()
    cols = {f: pick(keys, names) for f, names in FIELDS.items()}
    name_col = pick(keys, ["name", "title", "business_name", "company"])

    missing = {}
    for f, c in cols.items():
        if c:
            missing[f] = round(100 * sum(1 for r in rows if empty(r.get(c))) / n) if n else 0

    dups, by_addr, by_phone = [], defaultdict(list), defaultdict(list)
    for r in rows:
        label = str(r.get(name_col) or r.get("id") or "?")
        if cols["address"] and not empty(r.get(cols["address"])):
            by_addr[norm_addr(r[cols["address"]])].append(label)
        if cols["phone"] and not empty(r.get(cols["phone"])):
            digits = re.sub(r"\D", "", str(r[cols["phone"]]))[-10:]
            if len(digits) == 10:
                by_phone[digits].append(label)
    for k, v in list(by_addr.items()) + list(by_phone.items()):
        if len(v) > 1:
            dups.append(v)

    signals, examples, fake_rows = [], [], 0
    for r in rows:
        hit = []
        blob = " ".join(str(v) for v in r.values() if isinstance(v, (str, int, float)))
        if cols["phone"] and FAKE_PHONE.search(str(r.get(cols["phone"]) or "")):
            hit.append("555 phone number")
        if cols["website"] and FAKE_SITE.search(str(r.get(cols["website"]) or "")):
            hit.append("example/test website")
        if FAKE_WORDS.search(blob):
            hit.append("test/placeholder words")
        if name_col and FAKE_NAME_WORD.search(str(r.get(name_col) or "")):
            hit.append("name starts with test/sample/demo")
        if hit:
            fake_rows += 1
            signals += hit
            if len(examples) < 3:
                examples.append({"listing": str(r.get(name_col) or r.get("id")), "why": sorted(set(hit))})
    likely = n > 0 and (fake_rows / n >= 0.5 or fake_rows >= 3)

    summary = [f"{n} listings in total."]
    gaps = sorted(((p, f) for f, p in missing.items() if p > 0), reverse=True)[:2]
    for p, f in gaps:
        cnt = round(p * n / 100)
        summary.append(f"{cnt} of {n} {'is' if cnt == 1 else 'are'} missing {PLAIN[f]}.")
    if dups:
        summary.append(f"{len(dups)} look like duplicates (same address or phone).")
    if likely:
        summary.append(f"{fake_rows} of {n} look like test data (fake phone numbers or example websites), not real businesses.")
    elif fake_rows:
        summary.append(f"{fake_rows} listing{'s' if fake_rows > 1 else ''} look{'' if fake_rows > 1 else 's'} like test data and should be checked.")

    print(json.dumps({"count": n, "missing": missing, "duplicates": dups[:10],
                      "placeholder": {"likely": likely, "rows": fake_rows, "signals": sorted(set(signals)), "examples": examples},
                      "plain_summary": summary[:4]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
