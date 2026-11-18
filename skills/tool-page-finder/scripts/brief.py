#!/usr/bin/env python3
"""STEP 8. Write the final report with a filled-in brief for each of the top 5 tools.

Usage: python3 brief.py scored.csv --site example.com --out tool-pages-report.md

Everything is filled from the data and fixed tables. The only lines left for the
agent are marked CHECK: (open one URL and copy one fact). Nothing to invent.
"""
import argparse, csv, datetime, re

INPUTS = {
 "fee calculator":     ("sale price, shipping the buyer paid, your shipping cost, what you paid for the item",
                        "each fee, total fees, your payout, profit, profit margin %", "monthly"),
 "cost estimator":     ("quantity or weight, location/region, options",
                        "estimated total, cost per unit, low-high range", "monthly"),
 "value lookup":       ("item name or brand, condition, (optional) year/model",
                        "estimated value range, recent sold examples, where to sell it", "monthly"),
 "schedule tool":      ("location or store, date",
                        "the day/time answer, the next upcoming date, a weekly calendar", "weekly"),
 "converter or sizing":("amount + unit, or size + brand",
                        "converted amount or matching size, full chart", "yearly"),
 "checker":            ("the answers to the yes/no question",
                        "yes or no, the reason, the next step", "quarterly"),
 "comparison tool":    ("2-3 options to compare, your use case",
                        "side-by-side table, which option wins for your case", "monthly"),
 "generator":          ("a few details about the item or situation",
                        "a ready-to-copy result", "yearly"),
 "quiz":               ("answers to 5-10 questions", "a score and what to do next", "yearly"),
 "calculator":         ("the numbers the main keyword asks about", "the result plus a one-line explanation", "yearly"),
}

def slug(s): return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def why(r):
    parts = []
    if int(r["s_demand"]) >= 20: parts.append("one of the most-searched tool ideas in this niche")
    if int(r["s_small"]) >= 18: parts.append("several small sites already rank in the top 5")
    elif int(r["s_small"]) >= 10: parts.append("at least one small site ranks in the top 5")
    if int(r["s_tool"]) >= 10: parts.append("Google already ranks tool pages for it, so searchers want a tool")
    if int(r["s_forum"]): parts.append("forums rank, so people aren't finding a good answer")
    if int(r["s_fresh"]) >= 5: parts.append("the data changes, so a kept-up-to-date page beats stale ones")
    if r.get("trend") == "down": parts.append("WARNING: Google Trends shows it falling")
    return "; ".join(parts) or "best remaining score"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scored"); ap.add_argument("--site", required=True)
    ap.add_argument("--top", type=int, default=5); ap.add_argument("--out", default="tool-pages-report.md")
    a = ap.parse_args()
    if getattr(a, "out", None):  # create the output folder (notes/<site>/...) if it is new
        import os as _os
        _os.makedirs(_os.path.dirname(_os.path.abspath(a.out)), exist_ok=True)
    R = [r for r in csv.DictReader(open(a.scored, encoding="utf-8")) if r["confidence"] != "NOT CHECKED"][:a.top]
    if not R: raise SystemExit("ERROR: no checked ideas in scored.csv. Do steps 5-7 first.")
    data_mode = R[0]["demand_source"] == "volume"
    L = [f"# Tool page opportunities for {a.site}",
         f"Generated {datetime.date.today()} with the tool-page-finder skill. Mode: {'DATA (real search volume)' if data_mode else 'FREE (Google Autocomplete, no volume data)'}.", ""]
    if not data_mode:
        L += ["> Demand here is how often a phrase appeared in Google Autocomplete. It is NOT monthly search volume. "
              "Before building, check the top picks in Google Search Console, Keyword Planner, or an SEO tool if you have one.", ""]
    L += ["## Ranked shortlist", "", "| # | Tool | Main keyword | Score /100 | Confidence | Small sites in top 5 |", "|---|---|---|---|---|---|"]
    for i, r in enumerate(R, 1):
        L.append(f"| {i} | {r['subject'].title()} {r['tool_type']} | {r['main_keyword']} | {r['score']} | {r['confidence']} | {r['small_sites_in_top5']} |")
    for i, r in enumerate(R, 1):
        ins, outs, cadence = INPUTS.get(r["tool_type"], INPUTS["calculator"])
        off = r["official_urls"].split()
        L += ["", f"## #{i} {r['subject'].title()} {r['tool_type']}", "",
              f"- **Why it's here:** {why(r)}.",
              f"- **Suggested URL:** /{slug(r['subject'] + ' ' + r['tool_type'])}",
              f"- **Main keyword:** {r['main_keyword']}" + (f" (demand {r['demand']} {r['demand_source']})"),
              f"- **Other keywords to cover:** {r['top_keywords']}",
              f"- **Proof, small sites in top 5:** {r['small_sites_in_top5']}",
              f"- **Tool pages already ranking (study these):** {' '.join(r['tool_pages_in_top5'].split()[:3]) or 'none, so you could be first with a real tool'}",
              f"- **What the user enters:** {ins}",
              f"- **What the tool shows:** {outs}",
              f"- **Official data source:** {off[0] if off else 'none in the top 5'}",
              f"- **CHECK:** open the official source (or, if none, the first tool page above) and copy the current numbers the tool needs (e.g. fee %, price per pound). Write them here with today's date. If you can't find them, write 'unknown'.",
              f"- **Re-check the data:** {cadence}. Show \"Last checked [date]\" on the page.",
              f"- **Score breakdown:** {r['score']}/100 = demand {r['s_demand']} + small sites {r['s_small']} + tool proof {r['s_tool']} + forums {r['s_forum']} + shopping {r.get('s_shop', 0)} + fit {r['s_fit']} + fresh data {r['s_fresh']} + easy build {r['s_ease']}" + (f" + trend ({r['trend']})" if r.get("trend") else "")]
    L += ["", "## Before you build", "",
          "1. Confirm demand for the top 2-3 picks: Search Console impressions for related queries, Keyword Planner ranges, or any SEO tool.",
          "2. Open the 'tool pages already ranking' for each pick. Build something clearly better: more accurate, more up to date, faster.",
          "3. Link the new tool from your homepage and the 2-3 pages on your site most related to it."]
    open(a.out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"DONE: report with {len(R)} briefs -> {a.out}. Fill the {len(R)} CHECK: lines (step 9), nothing else.")

if __name__ == "__main__":
    main()
