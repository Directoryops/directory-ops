#!/usr/bin/env python3
"""Find the hours style a listings column already uses, and write new hours in that exact style.
So every run writes hours the same way (no judgment needed). Free, no AI.

  1) Which style does the column use?   (feed it the column's current values, JSON list)
     python3 hours_style.py detect values.json
     -> {"style": "osm", "counts": {"osm": 15, "compact": 4, ...}, "example": "Mo-Sa 07:00-19:00; Su 08:00-18:00"}

  2) Render Google's per-day hours (gmaps_lookup.py "hours" dict) in that style:
     python3 hours_style.py render --style osm --hours '{"monday": "7AM-7PM", ..., "sunday": "8AM-6PM"}'
     -> {"value": "Mo-Sa 07:00-19:00; Su 08:00-18:00"}

Styles: osm ("Mo-Sa 07:00-19:00; Su 08:00-18:00"), compact ("Mon-Sat 7AM-7PM, Sun 8AM-6PM" / "Daily 7AM-7PM"),
        long ("Monday-Saturday: 7:00 AM - 7:00 PM, Sunday: 8:00 AM - 6:00 PM"). The most common style among
        filled values wins; ties or an empty column -> compact. 24-hour places use the column's own 24h wording
        if one exists ("24/7", "Open 24 hours"), else "Open 24 hours"."""
import argparse
import json
import re
import sys

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
ABBR = {"osm": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
        "compact": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "long": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]}


def style_of(v):
    v = (v or "").strip()
    if not v:
        return None
    if re.search(r"\b(24/7|24 hours|open 24)\b", v, re.I):
        return "24h"
    if re.search(r"\b(Mo|Tu|We|Th|Fr|Sa|Su)(-(Mo|Tu|We|Th|Fr|Sa|Su))?\s+\d{2}:\d{2}-\d{2}:\d{2}", v):
        return "osm"
    if re.search(r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b", v):
        return "long"
    if re.search(r"\b(Daily|Mon|Tue|Wed|Thu|Fri|Sat|Sun)\b.*\d{1,2}(:\d\d)?\s?(AM|PM)", v, re.I):
        return "compact"
    return "other"


def to24(t):
    m = re.match(r"(\d{1,2})(?::(\d\d))?\s*(AM|PM)", t.strip(), re.I)
    if not m:
        return None
    h, mi, ap = int(m.group(1)), int(m.group(2) or 0), m.group(3).upper()
    h = (h % 12) + (12 if ap == "PM" else 0)
    return h, mi


def fmt(t, style):
    hm = to24(t)
    if hm is None:
        return t
    h, mi = hm
    if style == "osm":
        return f"{h:02d}:{mi:02d}"
    ap = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    if style == "long":
        return f"{h12}:{mi:02d} {ap}"
    return f"{h12}{':%02d' % mi if mi else ''}{ap}"


def render(hours, style, h24_word="Open 24 hours"):
    vals = [str(hours.get(d, "")).strip() for d in DAYS]
    if all(re.search(r"24 hours|open 24|24/7", v, re.I) for v in vals if v) and any(vals):
        return h24_word
    def piece(v):
        if not v or v.lower() == "closed":
            return "Closed" if style != "osm" else "off"
        parts = re.split(r"\s*[-–]\s*", v)
        if len(parts) != 2:
            return v
        sep = " - " if style == "long" else "-"
        return fmt(parts[0], style) + sep + fmt(parts[1], style)
    groups = []
    for i, v in enumerate(vals):
        p = piece(v)
        if groups and groups[-1][2] == p:
            groups[-1][1] = i
        else:
            groups.append([i, i, p])
    ab = ABBR["compact" if style not in ABBR else style]
    if len(groups) == 1 and style == "compact":
        return f"Daily {groups[0][2]}"
    out = []
    for a, b, p in groups:
        days = ab[a] if a == b else f"{ab[a]}-{ab[b]}"
        out.append(f"{days}: {p}" if style == "long" else f"{days} {p}")
    return ("; " if style == "osm" else ", ").join(out)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("detect")
    d.add_argument("values", help="JSON file with a list of the column's current values")
    r = sub.add_parser("render")
    r.add_argument("--style", required=True, choices=["osm", "compact", "long"])
    r.add_argument("--hours", required=True, help="JSON dict of day -> hours from gmaps_lookup.py")
    r.add_argument("--h24", default="Open 24 hours", help="the column's own 24-hour wording")
    a = ap.parse_args()
    if a.cmd == "detect":
        vals = json.load(open(a.values))
        if isinstance(vals, dict):
            vals = [row.get("hours") for row in vals.get("rows", [])]
        counts = {}
        h24 = None
        for v in vals:
            s = style_of(v)
            if s:
                counts[s] = counts.get(s, 0) + 1
                if s == "24h" and not h24:
                    h24 = v.strip()
        ranked = sorted(((n, s) for s, n in counts.items() if s in ("osm", "compact", "long")), reverse=True)
        style = ranked[0][1] if ranked and (len(ranked) == 1 or ranked[0][0] > ranked[1][0]) else "compact"
        ex = next((v for v in vals if style_of(v) == style), None)
        print(json.dumps({"style": style, "counts": counts, "example": ex, "h24_word": h24 or "Open 24 hours"}))
    else:
        print(json.dumps({"value": render(json.loads(a.hours), a.style, a.h24)}))


if __name__ == "__main__":
    sys.exit(main())
