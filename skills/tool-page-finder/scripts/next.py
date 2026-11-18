#!/usr/bin/env python3
"""Tells the agent exactly which step to do next, by looking at the files in the work folder.

Usage (run from the work folder, any time you are unsure):
  python3 next.py --site example.com
"""
import argparse, csv, os, re, sys

D = os.path.dirname(os.path.abspath(__file__))

def say(step, msg, cmd=None):
    print(f"NEXT STEP: {step}")
    print(msg)
    if cmd: print("RUN:\n  " + cmd)
    sys.exit(0)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--site", default="<site>"); a = ap.parse_args()
    py = f"python3 {D}"
    if not os.path.exists("seeds.txt"):
        say("1", "Write seeds.txt (8-12 lines, format 'bucket: seed', buckets core/entity/next). See SKILL.md step 1.")
    seeds = [l for l in open("seeds.txt") if l.strip() and not l.startswith("#")]
    b = [l.split(":")[0].strip() for l in seeds]
    if not (8 <= len(seeds) <= 12 and b.count("core") >= 2 and b.count("entity") >= 3 and b.count("next") >= 2):
        say("1", f"seeds.txt is not valid: {len(seeds)} seeds ({b.count('core')} core, {b.count('entity')} entity, {b.count('next')} next). "
                 "Need 8-12 seeds with at least 2 core, 3 entity, 2 next.")
    if not os.path.exists("suggestions.csv"):
        say("2", "Pull Google Autocomplete suggestions (about 1 minute per seed).",
            f"{py}/suggest.py --seeds-file seeds.txt --out suggestions.csv")
    extra = [f for f in os.listdir(".") if f.endswith(".csv") and f not in
             ("suggestions.csv", "candidates.csv", "serp.csv", "scored.csv", "trends.csv")]
    if not os.path.exists("candidates.csv"):
        say("3", "Group keywords into tool ideas." + (f" Including your data files: {' '.join(extra)}" if extra else ""),
            f"{py}/classify.py suggestions.csv {' '.join(extra)} --seeds-file seeds.txt --out candidates.csv".replace("  ", " "))
    if os.path.exists("review.txt") and re.search(r"^C\d+ \?\?", open("review.txt").read(), re.M):
        say("4", "Open review.txt. On every line replace ?? with yes or no (would a visitor of this site use this tool?). Save it. Then run next.py again.")
    if not os.path.exists("serp.csv"):
        say("5", "Make the search-results template.",
            f"{py}/score.py candidates.csv --decisions review.txt --make-serp-template 10")
    rows = list(csv.DictReader(open("serp.csv")))
    empty = sorted({r["keyword"] for r in rows if not r["url"].strip()})
    filled = {r["keyword"] for r in rows if r["url"].strip()}
    todo = [k for k in empty if k not in filled]
    if todo:
        say("6", "Web-search these keywords and paste the top 5 result URLs into serp.csv (rank 1-5):\n  " + "\n  ".join(todo[:10]))
    if not os.path.exists("scored.csv"):
        t = " --trends trends.csv" if os.path.exists("trends.csv") else ""
        say("7", "Score all ideas.", f"{py}/score.py candidates.csv --decisions review.txt --serp serp.csv{t} --out scored.csv")
    if not os.path.exists("tool-pages-report.md"):
        say("8", "Write the report.", f"{py}/brief.py scored.csv --site {a.site} --out tool-pages-report.md")
    txt = open("tool-pages-report.md").read()
    if re.search(r"\*\*CHECK:\*\* open", txt):
        say("9", "In tool-pages-report.md, replace each '**CHECK:** open the official source...' line with "
                 "'**Current numbers (checked YYYY-MM-DD):** ...' using numbers copied from that URL, or 'unknown'.")
    say("10", "Done. Send the user the shortlist table, the 'Why it's here' line for each tool, and the report path.")

if __name__ == "__main__":
    main()
