"""Step 7c. Count how many THREADS raised each canonical factor and write the research report.
Needs: extractions/*.json and factor_map.json (written in Step 7b).
Usage: python3 scripts/build_report.py
Writes output/research_report.md. Counting is done here by code, not by the AI. Free."""
import json, os
import common  # noqa: F401  (prints this script's help on --help)
from collections import defaultdict

fmap = json.load(open("factor_map.json"))  # {"raw factor name": "Canonical Factor"}
fmap = {k.strip().lower(): v for k, v in fmap.items()}
threads, quotes, prices, flags = defaultdict(set), defaultdict(list), [], []
total = 0
for f in sorted(os.listdir("extractions")):
    if not f.endswith(".json"):
        continue
    for t in json.load(open(os.path.join("extractions", f))):
        total += 1
        for x in t.get("factors", []):
            canon = fmap.get(x["factor"].strip().lower())
            if not canon or canon == "DROP":
                continue
            threads[canon].add(t["thread_id"])
            if x.get("quote") and len(quotes[canon]) < 3:
                quotes[canon].append(x["quote"])
        prices += t.get("prices", [])
        flags += t.get("red_flags", [])

os.makedirs("output", exist_ok=True)
rows = sorted(threads.items(), key=lambda kv: -len(kv[1]))
with open("output/research_report.md", "w") as out:
    out.write(f"# Reddit research report\n\nThreads read: {total}\n\n")
    out.write("## What people care about before deciding (ranked by number of threads)\n\n")
    for canon, ids in rows:
        out.write(f"### {canon} ({len(ids)} thread{'s' if len(ids) != 1 else ''})\n")
        for q in quotes[canon]:
            out.write(f'> "{q}"\n\n')
    out.write("## Prices people mentioned\n\n")
    for p in prices:
        out.write(f"- {p}\n")
    out.write("\n## Red flags people reported\n\n")
    for r in flags[:80]:
        out.write(f"- {r}\n")
print(f"WROTE output/research_report.md ({len(rows)} factors from {total} threads)")
for canon, ids in rows:
    print(f"{len(ids):>4}  {canon}")
