"""Step 6c. Check your reading: every factor quote in extractions/batch_NNN.json must appear in batches/batch_NNN.txt
(ignoring spaces, capitals and curly quotes), and every thread_id must exist in that batch. Free. Instant.
Usage: python3 scripts/check_batches.py
Prints each problem. Fix those quotes (copy the exact words) and run again until it says OK."""
import json, os, re
import common  # noqa: F401  (prints this script's help on --help)


def norm(s):
    s = (s or "").lower().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", "", s)


problems, checked = [], 0
for f in sorted(os.listdir("extractions")):
    if not (f.startswith("batch_") and f.endswith(".json")):
        continue
    src = f"batches/{f[:-5]}.txt"
    if not os.path.exists(src):
        problems.append(f"{f}: no matching {src}")
        continue
    text = open(src).read()
    ntext = norm(text)
    try:
        data = json.load(open(os.path.join("extractions", f)))
    except ValueError as e:
        problems.append(f"{f}: not valid JSON ({e})")
        continue
    for t in data:
        if f"THREAD_ID: {t.get('thread_id')}" not in text:
            problems.append(f"{f}: thread_id {t.get('thread_id')} is not in this batch")
        for x in t.get("factors", []):
            checked += 1
            if not x.get("quote") or norm(x["quote"]) not in ntext:
                problems.append(f"{f}: quote not found word for word: {str(x.get('quote'))[:90]}")
for p in problems:
    print("FIX", p)
print(f"OK: {checked} quotes checked, all found" if not problems else f"{len(problems)} problem(s) in {checked} quotes. Fix them, then run again.")
