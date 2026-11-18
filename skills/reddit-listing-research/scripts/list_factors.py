"""Step 7a. Print every distinct factor name the AI wrote in extractions/, with counts.
Usage: python3 scripts/list_factors.py
You then group these into a short canonical list (Step 7b). Free. Instant."""
import json, os
import common  # noqa: F401  (prints this script's help on --help)
from collections import Counter

c = Counter()
for f in sorted(os.listdir("extractions")):
    if not f.endswith(".json"):
        continue
    for t in json.load(open(os.path.join("extractions", f))):
        for fac in {x["factor"].strip().lower() for x in t.get("factors", [])}:
            c[fac] += 1
for fac, n in c.most_common():
    print(f"{n:>4}  {fac}")
print(f"\n{len(c)} distinct factor names")
