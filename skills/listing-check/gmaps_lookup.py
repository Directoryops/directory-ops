#!/usr/bin/env python3
"""Free Google Maps lookup for listing-check (no API key, no browser).

Usage:
    python3 gmaps_lookup.py "Sunrise Car Wash 120 Main St, Springfield, IL 62701"
    python3 gmaps_lookup.py --batch queries.txt        # one query per line
    python3 gmaps_lookup.py --listing "<name>" "<full address line>" [type word]   # recommended
    e.g. --listing "Sunrise Car Wash - Downtown" "120 N. Main St., Springfield 62701" "Touchless"

Pass the listing's ADDRESS LINE exactly as stored (street, city, zip). That is the truth.
Don't build it from the title or a separate city column: titles often name a nearby city or
neighborhood, and city columns can be wrong.

--listing tries several wordings before giving up (name + address, brand + type word +
address, brand + street + zip, address only), because one wording often misses a place.
address_match = same street number + street name (N./North, Rd/Road are normalized) and the
same ZIP when both have one. City names are ignored on purpose.
brand_in_name = the Google profile name contains the brand (a result named only by its
street address is a building, not the business). "attempts" shows what was tried.

Prints JSON per query:
    {query, status, names, addresses, phones, hours (per day), hours_compact, place_id, lat, lng, description,
     review_snippets, closed_permanently, closed_temporarily}

description = the business's own Google description (a strong type signal, e.g. "touchless automatic wash, open 24 hours").
review_snippets = short review quotes Google shows on the profile, with star rating.
hours = one entry per day, e.g. {"monday": "7AM-7PM", ..., "sunday": "Closed"}.
hours_compact = the same in one line: "Mon-Sat 7AM-7PM, Sun 8AM-6PM", "Daily 7:30AM-8PM" or "Open 24 hours".
single_place = true when Google showed one place (its hours/phone are that place's); false = a list of
several places, so hours/phone may belong to a neighbor.
business_details = false when Google only knows the address as a map point (no name, phone, hours
or website): there may be no business there.
usable (--listing only) = THE flag to trust: true only when address_match AND brand_in_name AND single_place.
Use Google's hours/phone/website only when usable is true. why_not_usable says why in plain words.
Never read "status" as trust: "found" can be a different business or a bare address.

place_id is Google's permanent ID for the place. Save it in the place ids file
(notes/<slug>/listing-check/place-ids.json, or the listing_place_ids table) the first time the street address matches (never on the listing itself, so the listing's
"last updated" date doesn't move); on later checks, a different place_id means a different place.

status:
    found       a place matched (check name + street address before trusting it)
    not_found   Google Maps returned no place for this query (closed businesses often vanish)
    blocked     Google refused the request (captcha / rate limit); stop and try later
    error       network or parsing problem

This reads the same data Google Maps shows a visitor. It is unofficial and can change;
if every lookup returns not_found or blocked, report it to the owner instead of guessing.
Be polite: the script waits between requests. Don't run it in parallel.
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DELAY_SECONDS = 3


def site_hours(text: str) -> str:
    """'9\u202fAM–7\u202fPM' -> '9AM-7PM', 'Closed' -> 'Closed', 'Open 24 hours' kept."""
    t = text.replace("\u202f", " ").replace("\u2009", " ").replace("–", "-").replace("—", "-")
    t = re.sub(r"\s*-\s*", "-", t)
    t = re.sub(r"(\d)(?::00)?\s*(AM|PM)", r"\1\2", t)
    t = re.sub(r"(\d:\d\d)\s*(AM|PM)", r"\1\2", t)
    # "9-5PM" style ranges where Google drops the first AM/PM are left as Google wrote them
    return t.strip()


SHORT = {"monday": "Mon", "tuesday": "Tue", "wednesday": "Wed", "thursday": "Thu", "friday": "Fri",
         "saturday": "Sat", "sunday": "Sun"}


def hours_compact(hours: dict) -> str:
    """{'monday': '7AM-7PM', ..., 'sunday': '8AM-6PM'} -> 'Mon-Sat 7AM-7PM, Sun 8AM-6PM'.
    Same every day -> 'Daily 7:30AM-8PM'. 24 hours every day -> 'Open 24 hours'. Missing days are left out."""
    order = [d.lower() for d in DAYS]
    days = [(d, hours[d]) for d in order if d in hours]
    if not days:
        return ""
    if len(days) == 7 and len({v for _, v in days}) == 1:
        v = days[0][1]
        return "Open 24 hours" if "24" in v else ("Closed" if v == "Closed" else f"Daily {v}")
    groups = []  # runs of consecutive days with the same hours
    for d, v in days:
        if groups and groups[-1][2] == v and order.index(d) == order.index(groups[-1][1]) + 1:
            groups[-1][1] = d
        else:
            groups.append([d, d, v])
    parts = []
    for a, b, v in groups:
        label = SHORT[a] if a == b else f"{SHORT[a]}-{SHORT[b]}"
        parts.append(f"{label} {'open 24 hours' if '24' in v else v}")
    return ", ".join(parts)


UI_TEXT = {"want to go", "been there", "directions", "save", "nearby", "share", "website", "call", "send to phone",
           "suggest an edit", "own this business?", "add a label", "write a review", "change name or other details",
           "claim this business", "photos", "reviews", "overview", "about", "menu", "order online", "updates"}


def looks_like_name(s: str) -> bool:
    """A business name, not a token, link, time zone, button label or review sentence."""
    t = s.strip()
    if not t or len(t) > 60 or "http" in t.lower() or t.lower() in UI_TEXT:
        return False
    if " " not in t and (len(t) > 20 or "/" in t or "," in t):
        return False  # tokens like ",AOvVaw2...", time zones like "America/Chicago"
    if t[0] in ",\"'(" or t[-1] in '.!?"' or t.count(",") >= 2:
        return False  # review text and quoted snippets
    return True


def lookup(query: str) -> dict:
    url = "https://www.google.com/search?tbm=map&hl=en&gl=us&q=" + urllib.parse.quote_plus(query)
    out = {"query": query, "status": "error", "names": [], "addresses": [], "phones": [],
           "hours": {}, "closed_permanently": False, "closed_temporarily": False}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US"})
        body = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        out["status"] = "blocked" if ("429" in msg or "sorry" in msg) else "error"
        out["error"] = msg[:200]
        return out

    if "/sorry/" in body or "unusual traffic" in body:
        out["status"] = "blocked"
        return out

    # All JSON string literals in the response, properly unescaped (handles & etc.)
    strings = []
    for raw in re.findall(r'"((?:[^"\\]|\\.){2,90})"', body):
        try:
            strings.append(json.loads('"' + raw + '"'))
        except ValueError:
            continue

    q_lower = query.lower()
    brand = query.split()[0].lower() if query.split() else ""
    names, categories, websites = [], [], []
    for s in strings:
        sl = s.lower()
        if sl == q_lower or sl.startswith(q_lower[:25]) or re.search(r"\d{5}", s):
            continue  # query echo or an address
        if re.fullmatch(r"[a-z0-9-]+(\.[a-z0-9-]+)*\.(org|com|net|us|biz|info|co)", sl):
            websites.append(s)
        elif re.fullmatch(r"[A-Z][A-Za-z'&, ]{2,40} (store|shop|center|warehouse|outlet|market)", s) and brand not in sl:
            categories.append(s)
        elif brand and brand in sl and looks_like_name(s):
            names.append(s)
    out["names"] = list(dict.fromkeys(names))[:5]
    out["categories"] = list(dict.fromkeys(categories))[:5]
    out["websites"] = list(dict.fromkeys(websites))[:3]

    addrs = re.findall(r'"(\d{1,6} [^"]{3,60}, [A-Za-z .\'-]+, [A-Z]{2} \d{5})(?:, United States)?"', body)
    out["addresses"] = list(dict.fromkeys(addrs))[:3]

    out["phones"] = list(dict.fromkeys(re.findall(r'"(\(\d{3}\) \d{3}-\d{4})"', body)))[:3]

    for m in re.finditer(r'\["(' + "|".join(DAYS) + r')",\d,\[[^\]]*\],\[\["([^"]+)"', body):
        day = m.group(1).lower()
        if day not in out["hours"]:
            out["hours"][day] = site_hours(m.group(2))
    for m in re.finditer(r'\["(' + "|".join(DAYS) + r')",\d,\[[^\]]*\],\["Closed"', body):
        out["hours"].setdefault(m.group(1).lower(), "Closed")

    out["hours_compact"] = hours_compact(out["hours"])

    # Coordinates of the place (first [null,null,lat,lng] pair)
    m = re.search(r'\[null,null,(-?\d{1,3}\.\d+),(-?\d{1,3}\.\d+)\]', body)
    out["lat"], out["lng"] = (float(m.group(1)), float(m.group(2))) if m else (None, None)

    # The business's own Google description (often says what kind of place it is)
    out["description"] = None
    for raw in re.findall(r'"([A-Z][^"\\]{80,1500})"', body):
        if (raw.count(" ") >= 10 and "." in raw and "Google" not in raw and "Maps" not in raw
                and not raw.lower().startswith(q_lower[:25])):
            try:
                out["description"] = json.loads('"' + raw + '"')
            except ValueError:
                out["description"] = raw
            break

    # Short review snippets Google shows on the profile, with star rating
    out["review_snippets"] = []
    for m in re.finditer(r'\],"\\"((?:[^"\\]|\\.){5,400})\\"",null,null,\[[^\]]*\](?:,\[[^\]]*\])*\],\d,\[.*?\]\],null,"\d+",(\d)', body):
        try:
            text = json.loads('"' + m.group(1) + '"')
        except ValueError:
            continue
        out["review_snippets"].append({"text": text, "rating": int(m.group(2))})
    out["review_snippets"] = out["review_snippets"][:5]

    out["place_ids"] = list(dict.fromkeys(re.findall(r'"(ChIJ[A-Za-z0-9_\-]{20,})"', body)))[:3]
    out["place_id"] = out["place_ids"][0] if out["place_ids"] else None
    out["closed_permanently"] = bool(re.search(r'"Permanently closed"', body))
    out["closed_temporarily"] = bool(re.search(r'"Temporarily closed"', body))
    # One place on the page = its hours/phone are that place's. Several = a list; fields may mix businesses.
    out["single_place"] = len(out["place_ids"]) <= 1
    # Google echoes the searched address back even when nothing is there. An address with no name,
    # phone or hours is just a map point, not proof a business exists.
    out["business_details"] = bool(out["names"] or out["phones"] or out["hours"] or out["websites"])
    out["status"] = "found" if (out["addresses"] or out["hours"] or out["phones"] or out["names"]) else "not_found"
    return out


DIRECTIONS = {"n": "north", "s": "south", "e": "east", "w": "west", "ne": "northeast", "nw": "northwest",
              "se": "southeast", "sw": "southwest"}
SUFFIXES = {"st": "street", "rd": "road", "ave": "avenue", "av": "avenue", "blvd": "boulevard", "dr": "drive",
            "ln": "lane", "hwy": "highway", "pkwy": "parkway", "ct": "court", "pl": "place", "cir": "circle",
            "ter": "terrace", "trl": "trail", "fwy": "freeway", "tpke": "turnpike", "sq": "square"}


ROUTE_WORDS = {"state", "us", "route", "rte", "sr", "fm", "rr", "county", "road", "highway", "interstate", "i"}


def norm_words(text: str) -> list:
    """'3150 N. San Fernando Rd.' -> ['3150', 'north', 'san', 'fernando', 'road']"""
    words = re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()
    out = []
    for i, w in enumerate(words):
        m = re.fullmatch(r"(\d+)(n|s|e|w)", w)
        if i and m and words[i - 1] in ROUTE_WORDS:   # "US 19N" -> "us 19 north" (route number + direction)
            out += [m.group(1), DIRECTIONS[m.group(2)]]
        else:
            out.append(SUFFIXES.get(w, DIRECTIONS.get(w, w)))
    return out


def street_key(address: str):
    """Street number + core street name words (no directions, no suffix), from the street part only."""
    street = address.split(",")[0]
    words = norm_words(street)
    if not words or not words[0][0].isdigit():
        return None, []
    core = [w for w in words[1:] if w not in DIRECTIONS.values() and w not in SUFFIXES.values()
            and w not in ROUTE_WORDS and not re.fullmatch(r"(suite|ste|unit|#)?\d*[a-z]?", w)]
    if not core:
        # Numbered roads ("Highway 71 West", "State Hwy 71", "FM 1825", "Route 9"): the road number is the name.
        core = [w for w in words[1:] if w.isdigit()]
    return words[0], core[:2]


def zip_of(address: str):
    """ZIP at the END of the address ('..., OH 44110' or '... Los Angeles 90065'), never the street number."""
    a = re.sub(r",?\s*(USA|United States)\s*$", "", address.strip())
    m = re.search(r"\s(\d{5})(?:-\d{4})?$", a)
    return m.group(1) if m and not a.startswith(m.group(1)) else None


def same_address(listing_address: str, google_address: str) -> bool:
    """Number + street name must match. ZIP must match when both have one. City names are ignored
    (listings often use a nearby city or neighborhood; the street address is what's true)."""
    num, core = street_key(listing_address)
    g_num, g_core = street_key(google_address)
    if not num or num != g_num or not core:
        return False
    if not all(w in g_core or w in norm_words(google_address) for w in core):
        return False
    z1, z2 = zip_of(listing_address), zip_of(google_address)
    return not (z1 and z2 and z1 != z2)


def lookup_listing(name: str, address: str, type_word: str = "") -> dict:
    """Use the listing's full ADDRESS line as the truth (not the title, not a separate city column).
    Try several wordings; prefer a result that matches the address AND carries the brand name."""
    brand = name.split()[0] if name.split() else ""
    street = address.split(",")[0].strip()
    zip_code = zip_of(address) or ""
    variants = [
        f"{name} {address}",
        f"{brand} {type_word} {address}".replace("  ", " "),
        f"{brand} {street} {zip_code}".strip(),
        address,
    ]
    attempts, best, fallback = [], None, None
    for i, q in enumerate(dict.fromkeys(variants)):
        if i:
            time.sleep(DELAY_SECONDS)
        r = lookup(q)
        r["address_match"] = any(same_address(address, a) for a in r["addresses"]) and r.get("business_details", True)
        r["brand_in_name"] = any(brand.lower() in n.lower() for n in r["names"]) if brand else False
        attempts.append({"query": q, "status": r["status"], "address_match": r["address_match"],
                         "names": r["names"][:2]})
        if r["status"] == "blocked":
            best = r
            break
        if r["address_match"] and r["brand_in_name"]:
            best = r
            break
        if r["address_match"] and fallback is None:
            fallback = r
        if fallback is None and best is None and r["status"] == "found":
            best = r
    best = best if (best and best.get("address_match")) or not fallback else fallback
    best = best or {"query": variants[0], "status": "not_found", "names": [], "addresses": [], "phones": [],
                    "hours": {}, "closed_permanently": False, "closed_temporarily": False,
                    "address_match": False, "brand_in_name": False}
    best["listing_address"] = address
    best["attempts"] = attempts
    # ONE flag to trust: hours/phone/website from Google may be used only when usable is true.
    # Never read "status" as trust ("found" can be a different business or a bare address).
    reasons = []
    if not best.get("address_match"):
        reasons.append("Google's address doesn't match the listing's address")
    if not best.get("brand_in_name"):
        reasons.append("the Google profile name doesn't contain the listing's name")
    if not best.get("single_place", True):
        reasons.append("the page shows several places, so hours/phone may belong to another one")
    if best.get("status") in ("blocked", "error"):
        reasons.insert(0, "Google lookup failed (" + best.get("status") + "), try again later")
    best["usable"] = not reasons
    best["why_not_usable"] = "; ".join(reasons)
    return best


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__)
        sys.exit(0 if args else 1)
    if args[0] == "--listing" and len(args) >= 3:
        # --listing "<name>" "<full address line exactly as on the listing>" [type word, e.g. Touchless]
        print(json.dumps(lookup_listing(args[1], args[2], args[3] if len(args) > 3 else ""), ensure_ascii=False))
        return
    if args[0] == "--batch":
        queries = [line.strip() for line in open(args[1]) if line.strip()]
    else:
        queries = [" ".join(args)]
    for i, q in enumerate(queries):
        if i:
            time.sleep(DELAY_SECONDS)
        print(json.dumps(lookup(q), ensure_ascii=False))


if __name__ == "__main__":
    main()
