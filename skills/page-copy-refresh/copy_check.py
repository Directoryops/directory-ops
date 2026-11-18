#!/usr/bin/env python3
"""Quality gate for page-copy-refresh. Nothing may be written to the site until this passes.

    python3 copy_check.py pages.json [--brand-field closing] [--tokens "{count},{state}"]

pages.json: a list of pages, each with the RENDERED copy (tokens filled with real values):
    [{"page": "texas/state-page", "place": "Texas", "names": ["Austin", "Dallas"],
      "facts": {"active listings": "12", "earliest opening": "7AM", "open on Sunday": "11",
                "cities": "Austin, Dallas, Houston"},          # from the Step 2 database query
      "fields": {"intro": "...", "middle": "...", "closing": "..."},
      "template_fields": {"intro": "... {count} ..."}}]   # template_fields optional, used for token checks

Checks (any failure = rewrite that page, by hand, then run again).
Optional per page: "brand": "Sunrise Directory" (or pass --brand once for all pages).
Checks:
  1. Cross-page sameness: a sentence that is the same on 3+ pages once places, names and numbers
     are blanked out (the brand statement field is allowed to share its core message, but not word for word).
  2. Repetition inside a page: any 5-word phrase used twice, or the same list of names twice.
  3. Banned phrases (AI tells, hedges, internal/negative talk).
  4. Token misuse in templates: a word token ({locations}, {stores}, {is_are}) where a number belongs,
     or unknown tokens.
  5. Too short or too long sentences, empty fields.
  6. Accuracy: every number, time and city/area name in the copy must appear in that page's "facts"
     (the Step 2 query results, labels included: a fact "open 24/7: 3" covers both 24/7 and 3). A number or name that isn't in the facts = unverified claim = fail.
     Any Capitalized word or phrase that isn't the place, a listed name, the brand or in the facts also
     fails ("possible invented place"), so names the agent forgot to list are caught too.
Prints JSON: {"pass": bool, "pages_checked": n, "failures": [{"page", "check", "detail"}]}
"""
import argparse
import json
import re
import sys
from collections import defaultdict

BANNED = [
    "nestled", "boasts", "treasure trove", "look no further", "whether you're a seasoned", "in today's",
    "one-stop destination", "unique shopping experience", "hidden gem", "plethora", "myriad",
    "one of the most", " may have", " might ", "try to", "aims to",
    "needs review", "missing", "lacks", "not yet", "still needs", "coordinates", "database", "listing data",
    "listed schedule", "report sunday hours", "plan around",
]
WORD_TOKENS = ["{locations}", "{stores}", "{is_are}"]
# Capitalized words that are fine anywhere (not place or business names)
CAP_OK = set("""I AI Monday Tuesday Wednesday Thursday Friday Saturday Sunday Mondays Tuesdays Wednesdays Thursdays
Fridays Saturdays Sundays January February March April May June July August September October November December
AM PM ChatGPT Google Maps FAQ""".split())


def sentences(text: str):
    return [s.strip() for s in re.split(r"(?<=[.!?;])\s+", text or "") if s.strip()]


def skeleton(sentence: str, blanks) -> str:
    s = sentence.lower()
    for b in sorted(blanks, key=len, reverse=True):
        if b:
            s = s.replace(b.lower(), "_")
    s = re.sub(r"\d+(:\d\d)?\s*(am|pm)?", "#", s)
    s = re.sub(r"[^a-z_# ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pages")
    ap.add_argument("--brand-field", default="", help="field holding the brand statement (may share its message)")
    ap.add_argument("--tokens", default="", help="comma separated allowed tokens")
    ap.add_argument("--brand", default="", help="the site's brand name (allowed in the copy)")
    a = ap.parse_args()
    pages = json.load(open(a.pages))
    allowed = [t.strip() for t in a.tokens.split(",") if t.strip()]
    fails = []

    # 1. cross-page sameness
    seen = defaultdict(set)
    for p in pages:
        blanks = [p.get("place", "")] + list(p.get("names", []))
        for field, text in p["fields"].items():
            for s in sentences(text):
                key = skeleton(s, blanks)
                if len(key.split()) >= 4:
                    seen[(field == a.brand_field, key)].add(p["page"])
    for (is_brand, key), where in seen.items():
        limit = len(pages) if is_brand else 2
        if len(where) > limit or (is_brand and len(where) > 3 and len(pages) > 3):
            for page in sorted(where):
                fails.append({"page": page, "check": "same sentence on %d pages" % len(where), "detail": key[:120]})

    for p in pages:
        text = " ".join(p["fields"].values())
        low = text.lower()
        # 2. repetition inside the page
        words = re.findall(r"[a-z0-9']+", low)
        grams = defaultdict(int)
        for i in range(len(words) - 4):
            grams[" ".join(words[i:i + 5])] += 1
        rep = [g for g, n in grams.items() if n > 1]
        if rep:
            fails.append({"page": p["page"], "check": "phrase repeated inside the page", "detail": rep[0]})
        for name in p.get("names", []):
            if name and low.count(name.lower()) > 2:
                fails.append({"page": p["page"], "check": "name repeated more than twice", "detail": name})
        # 3. banned phrases
        for b in BANNED:
            if b in low:
                fails.append({"page": p["page"], "check": "banned phrase", "detail": b.strip()})
        # 4. tokens
        for field, t in (p.get("template_fields") or {}).items():
            for tok in re.findall(r"\{[a-z_]+\}", t):
                if allowed and tok not in allowed:
                    fails.append({"page": p["page"], "check": "unknown token", "detail": f"{field}: {tok}"})
            for wt in WORD_TOKENS:
                if re.search(re.escape(wt) + r"\s+of\b", t) or re.search(r"(^|[.!?]\s+)" + re.escape(wt), t):
                    fails.append({"page": p["page"], "check": "word token used like a number", "detail": f"{field}: {wt}"})
        # 6. accuracy: numbers, times and names must come from the facts
        facts = p.get("facts")
        if facts is None:
            fails.append({"page": p["page"], "check": "no facts given", "detail": "include the Step 2 facts for this page"})
        else:
            fact_text = " ".join(f"{k} {v}" for k, v in facts.items()).lower().replace(" ", "")
            for m in re.findall(r"\b\d{1,2}(?::\d\d)?\s?(?:am|pm)\b|\b\d+\b", low):
                if m.replace(" ", "") not in fact_text:
                    fails.append({"page": p["page"], "check": "number or time not in facts", "detail": m})
            known = {n.lower() for n in p.get("names", [])} | {str(p.get("place", "")).lower()}
            fact_names = " ".join(f"{k} {v}" for k, v in facts.items()).lower()
            for n in p.get("names", []):
                if n.lower() not in fact_names:
                    fails.append({"page": p["page"], "check": "name not in facts", "detail": n})
            # names the agent didn't list: any Capitalized word or phrase (not starting a sentence)
            # that isn't in the facts, the place, the names or the brand
            allowed_text = " ".join([fact_names, str(p.get("place", "")).lower(), " ".join(p.get("names", [])).lower(),
                                     (p.get("brand") or a.brand).lower()])
            seen_caps = set()
            for field, t in p["fields"].items():
                for sent in sentences(t):
                    words_ = re.findall(r"[A-Za-z][A-Za-z'.-]*", sent)[1:]  # skip the sentence's first word
                    phrase = []
                    for w in words_ + [""]:
                        clean = w.strip(".'")
                        if clean[:1].isupper() and clean not in CAP_OK:
                            phrase.append(clean)
                            continue
                        if phrase:
                            ph = " ".join(phrase)
                            if ph.lower() not in allowed_text and ph not in seen_caps:
                                seen_caps.add(ph)
                                fails.append({"page": p["page"], "check": "name not in facts (possible invented place)", "detail": ph})
                            phrase = []
        # 7. the brand makes the claim, not the place
        place = str(p.get("place", ""))
        if place and re.search(re.escape(place.lower()) + r"( shoppers)? (has|have|gets?) the most", low):
            fails.append({"page": p["page"], "check": "claim made by the place, not the brand", "detail": place})
        # 5. shape
        for field, t in p["fields"].items():
            if not t or len(t.split()) < 12:
                fails.append({"page": p["page"], "check": "field empty or too short", "detail": field})
            for s in sentences(t):
                if len(s.split()) > 40:
                    fails.append({"page": p["page"], "check": "sentence too long (over 40 words)", "detail": s[:80]})

    print(json.dumps({"pass": not fails, "pages_checked": len(pages), "failures": fails[:200]}, ensure_ascii=False, indent=1))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
