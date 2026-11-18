#!/usr/bin/env python3
"""STEP 2. Free keyword discovery via Google Autocomplete.

Usage:
  python3 suggest.py --seeds-file seeds.txt --out suggestions.csv

seeds.txt format, one per line:  bucket: seed
  bucket is one of  core | entity | next
  example:
    core: fish tank
    entity: petco
    next: aquarium setup
Lines starting with # are ignored.

For each seed it asks Google Autocomplete for "seed + tool word" and
"question word + seed". Output columns: keyword, hits, seed, bucket.
'hits' = how many different prefixes returned that keyword (rough demand
signal, NOT search volume). Stdlib only. ~37 requests per seed, ~1 min per seed.
"""
import argparse, csv, json, sys, time, urllib.error, urllib.parse, urllib.request

AFTER = ["calculator", "fees", "fee", "cost", "price", "prices", "price per",
    "worth", "value", "chart", "size", "converter", "estimate", "checker",
    "lookup", "schedule", "calendar", "template", "generator", "vs",
    "per pound", "how much", "tracker", "quiz", "test", "rates", "formula"]
BEFORE = ["how much does", "how much is", "how much do", "how many",
    "what percentage does", "is it worth", "best time to", "when does",
    "how long does", "how to calculate"]
URL = "https://suggestqueries.google.com/complete/search?client=firefox&hl={hl}&gl={gl}&q={q}"
BUCKETS = {"core", "entity", "next"}

def fetch(q, hl, gl):
    req = urllib.request.Request(URL.format(hl=hl, gl=gl, q=urllib.parse.quote(q)),
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    return data[1] if len(data) > 1 else []

def read_seeds(path):
    seeds = []
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.strip()
        if not line or line.startswith("#"): continue
        if ":" not in line: sys.exit(f"seeds.txt line {n}: missing 'bucket:' prefix -> {line!r}")
        b, s = [x.strip().lower() for x in line.split(":", 1)]
        if b not in BUCKETS: sys.exit(f"seeds.txt line {n}: bucket must be core, entity or next -> {b!r}")
        if s: seeds.append((b, s))
    if not seeds: sys.exit("seeds.txt has no seeds")
    return seeds

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds-file", required=True)
    ap.add_argument("--out", default="suggestions.csv")
    ap.add_argument("--hl", default="en"); ap.add_argument("--gl", default="us")
    ap.add_argument("--sleep", type=float, default=0.6)
    ap.add_argument("--max-minutes", type=float, default=20, help="stop asking for new suggestions after this many minutes")
    a = ap.parse_args()
    if getattr(a, "out", None):  # create the output folder (notes/<site>/...) if it is new
        import os as _os
        _os.makedirs(_os.path.dirname(_os.path.abspath(a.out)), exist_ok=True)
    t0, net_fails, rate_limits, stopped = time.time(), 0, 0, 0
    seeds = read_seeds(a.seeds_file)
    hits, meta, errors, calls = {}, {}, 0, 0
    for i, (bucket, seed) in enumerate(seeds, 1):
        if time.time() - t0 > a.max_minutes * 60 or net_fails >= 5 or rate_limits >= 3:
            stopped = len(seeds) - i + 1
            why = ("Google stopped answering" if net_fails >= 5 else "rate limited 3 times" if rate_limits >= 3
                   else "time limit")
            print(f"STOP time budget reached ({why}): {stopped} items not checked (rerun with only those seeds to continue)",
                  file=sys.stderr)
            break
        print(f"[{i}/{len(seeds)}] {seed}", flush=True)
        for q in [f"{seed} {m}" for m in AFTER] + [f"{m} {seed}" for m in BEFORE]:
            calls += 1
            try:
                for s in fetch(q, a.hl, a.gl):
                    s = " ".join(s.lower().split())
                    hits[s] = hits.get(s, 0) + 1
                    meta.setdefault(s, (seed, bucket))
                net_fails = 0
            except Exception as e:
                errors += 1
                print(f"  warn: {q!r}: {e}", file=sys.stderr)
                if "429" in str(e):
                    rate_limits += 1
                    print("  rate limited: sleeping 60s", file=sys.stderr); time.sleep(60)
                elif not isinstance(e, urllib.error.HTTPError):
                    net_fails += 1
                    if net_fails >= 5:
                        break
            time.sleep(a.sleep)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["keyword", "hits", "seed", "bucket"])
        for k, n in sorted(hits.items(), key=lambda x: -x[1]):
            w.writerow([k, n, *meta[k]])
    print(f"DONE: {len(hits)} suggestions from {len(seeds)} seeds ({errors}/{calls} failed requests) -> {a.out}")
    if errors > calls / 2: sys.exit("ERROR: more than half the requests failed. Check internet access to suggestqueries.google.com")

if __name__ == "__main__":
    main()
