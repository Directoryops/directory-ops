#!/usr/bin/env python3
"""Honest stats from a listings export, before any number goes into an article. Free, no AI, read only.

  python3 listing_stats.py rows.json --name <name column> --website <website column> --hours <hours column> [--day Su]
  python3 listing_stats.py rows.json --name <name> --website <website> --text <description column> --yes '<regex>' --no '<regex>'
     -> per company: how many listings say YES, say NO, or don't say (UNKNOWN). A listing that doesn't
        mention something is UNKNOWN, never "no". Use this for every "X% of centers do Y" claim.

rows.json = the output of directory-db/db.py select --all (or a plain JSON list of rows).

What it does:
  1. Flags rows whose data looks fake or stale, and leaves them OUT of every stat:
     - "Coming soon" listings (name or phone says coming soon / opens <date>)
     - identical hours all 7 days (often a placeholder), a close at 12:00 AM / 00:00, no hours at all
  2. Brand map: groups listings by their website's domain, so sub-brands roll up under the parent
     (two brand names sharing one website domain = one company). Shows the brand names in each group.
  3. Per company: how many listings, and (with --day) how many are open that day, share in %.
Prints JSON. Every stat line says how many rows were excluded and why, so the article can say so.

Hours formats read: a list like ["Mo 06:00-19:00", ...] (also inside {"hours": [...]}), or text like
"Mo-Sa 07:00-19:00; Su 08:00-15:00", or "Mon-Sat 7AM-7PM, Sun 8AM-6PM"."""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict

DAYS = ["mo", "tu", "we", "th", "fr", "sa", "su"]
ALIASES = {"mon": "mo", "tue": "tu", "wed": "we", "thu": "th", "fri": "fr", "sat": "sa", "sun": "su",
           "monday": "mo", "tuesday": "tu", "wednesday": "we", "thursday": "th", "friday": "fr",
           "saturday": "sa", "sunday": "su"}


def day_key(w):
    w = w.lower().strip(".")
    return w if w in DAYS else ALIASES.get(w)


def parse_hours(v):
    """-> dict day -> 'HH:MM-HH:MM' (or 'closed'); {} if unreadable."""
    if isinstance(v, dict):
        v = v.get("hours", v)
    if isinstance(v, str):
        v = [p for p in re.split(r"[;,]\s*", v) if p.strip()]
    if not isinstance(v, list):
        return {}
    out = {}
    for item in v:
        m = re.match(r"\s*([A-Za-z]+)(?:\s*-\s*([A-Za-z]+))?\s+(.+)$", str(item))
        if not m:
            continue
        a, b, t = day_key(m.group(1)), day_key(m.group(2) or m.group(1)), m.group(3).strip()
        if m.group(1).lower() == "daily":
            a, b = "mo", "su"
        if not a or not b:
            continue
        i, j = DAYS.index(a), DAYS.index(b)
        for d in DAYS[i:j + 1] if i <= j else DAYS[i:] + DAYS[:j + 1]:
            out[d] = "closed" if re.match(r"(?i)closed|off", t) else t
    return out


def to24(t):
    m = re.match(r"(\d{1,2})(?::(\d\d))?\s*(am|pm)?", t.strip(), re.I)
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2) or 0)
    if m.group(3):
        h = h % 12 + (12 if m.group(3).lower() == "pm" else 0)
    return h * 60 + mi


def domain(url):
    host = re.sub(r"^https?://", "", (url or "").strip().lower()).split("/")[0].split("?")[0]
    host = re.sub(r"^www\d?\.", "", host)
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def brand_of(name):
    """First word of the listing name, case-folded ('SunWash' and 'Sunwash' are one brand)."""
    words = re.sub(r"[^A-Za-z0-9 &'-]", " ", name or "").split()
    return words[0].lower() if words else ""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rows")
    ap.add_argument("--name", required=True)
    ap.add_argument("--website", required=True)
    ap.add_argument("--hours", default="", help="hours column (needed for --day and the placeholder-hours checks)")
    ap.add_argument("--text", default="", help="text column(s) to read for a yes/no fact, comma separated (e.g. description)")
    ap.add_argument("--yes", default="", help="regex that means YES in --text (e.g. 'walk-?ins? (are )?(welcome|accepted)')")
    ap.add_argument("--no", default="", help="regex that means NO in --text (e.g. 'appointment(s)? (only|required)')")
    ap.add_argument("--phone", default="", help="phone column (to spot 'coming soon' rows)")
    ap.add_argument("--day", default="", help="mo..su: count listings open that day per company")
    a = ap.parse_args()
    data = json.load(open(a.rows))
    rows = data.get("rows", data) if isinstance(data, dict) else data

    flags, kept = Counter(), []
    examples = defaultdict(list)
    for r in rows:
        name, phone = str(r.get(a.name) or ""), str(r.get(a.phone) or "") if a.phone else ""
        hrs = parse_hours(r.get(a.hours)) if a.hours else {"_": "n/a"}
        why = None
        if re.search(r"(?i)coming soon|opens? (on )?[a-z]+ \d", name + " " + phone):
            why = "coming_soon"
        elif a.hours and not hrs:
            why = "no_hours"
        elif a.hours and len(hrs) == 7 and len(set(hrs.values())) == 1 and "closed" not in hrs.values():
            why = "same_hours_all_7_days"
        elif any(re.search(r"(-|–)\s*(00:00|12:00\s*am|12\s*am)\b", t, re.I) for t in hrs.values()):
            why = "closes_at_midnight"
        if why:
            flags[why] += 1
            if len(examples[why]) < 3:
                examples[why].append(name)
            continue
        kept.append((r, hrs))

    groups = defaultdict(lambda: {"listings": 0, "brands": Counter(), "open_day": 0, "yes": 0, "no": 0, "unknown": 0,
                                  "conditional": 0, "example": ""})
    COND = re.compile(r"\b(only if|if your|unless|some (centers|locations)|at some|may (not )?|depending)\b", re.I)

    def sentence_with(t, rx):
        m = re.search(rx, t, re.I)
        if not m:
            return ""
        a0 = max(t.rfind(".", 0, m.start()), t.rfind("!", 0, m.start())) + 1
        e = t.find(".", m.end())
        return t[a0:e + 1 if e != -1 else len(t)].strip()[:240]
    text_cols = [c.strip() for c in a.text.split(",") if c.strip()]
    for r, hrs in kept:
        g = groups[domain(r.get(a.website)) or "(no website)"]
        g["listings"] += 1
        g["brands"][brand_of(r.get(a.name))] += 1
        if a.day and hrs.get(a.day.lower()[:2], "closed") != "closed":
            g["open_day"] += 1
        if text_cols:
            t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", " ".join(str(r.get(c) or "") for c in text_cols)))
            ys = sentence_with(t, a.yes) if a.yes else ""
            ns = sentence_with(t, a.no) if a.no else ""
            # silence is UNKNOWN, never "no"; conflicting text is unknown; "yes, but only if ..." is CONDITIONAL
            if ys and not ns:
                k = "conditional" if COND.search(ys) else "yes"
            elif ns and not ys:
                k = "no"
            else:
                k = "unknown"
            g[k] += 1
            if not g["example"] and (ys or ns):
                g["example"] = ys or ns

    companies = []
    for dom, g in sorted(groups.items(), key=lambda x: -x[1]["listings"]):
        row = {"website_domain": dom, "listings": g["listings"],
               "brand_names": [f"{b} ({n})" for b, n in g["brands"].most_common(5)]}
        if len(g["brands"]) > 1:
            row["note"] = "several brand names share one website: count them as one company"
        if a.day:
            row[f"open_{a.day.lower()[:2]}"] = g["open_day"]
            row["share_pct"] = round(100 * g["open_day"] / g["listings"]) if g["listings"] else 0
        if text_cols:
            row["text_fact"] = {"yes": g["yes"], "conditional": g["conditional"], "no": g["no"], "unknown": g["unknown"],
                                "example_sentence": g["example"],
                                "say": ("all say yes" if g["yes"] == g["listings"] else
                                        "all say no" if g["no"] == g["listings"] else
                                        "not stated for most" if g["unknown"] > g["listings"] / 2 else "mixed")}
        companies.append(row)

    total_open = sum(g["open_day"] for g in groups.values())
    print(json.dumps({
        "rows_total": len(rows),
        "rows_used": len(kept),
        "excluded": dict(flags),
        "excluded_examples": dict(examples),
        "day": a.day.lower()[:2] or None,
        "open_that_day": total_open if a.day else None,
        "companies": companies,
        "say_in_article": (f"Based on {len(kept)} of {len(rows)} listings; {sum(flags.values())} left out "
                           f"(coming soon, missing or placeholder hours)."),
    }, indent=1))


if __name__ == "__main__":
    sys.exit(main())
