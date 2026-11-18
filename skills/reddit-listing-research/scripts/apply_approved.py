"""Step 12. Write the owner-approved, VERIFIED values to the live directory through the safe database helper.
Dry run by default; add --apply to write. Free. No AI.

    python3 <this folder>/apply_approved.py --db-py /data/skills/directory-ops/directory-db/db.py \
        --site-url <url> --key-env <KEY_ENV> --table <listings table> --id-column id --slug <slug> [--overwrite] [--apply]

Reads output/review.csv (rows with status VERIFIED and approve = y) and output/fields.json (each field may
have "column": the real column name in the listings table; default = the field name).
Rules: only VERIFIED + approved values; never REJECTED or UNKNOWN. By default it only fills EMPTY cells
(it never replaces something the owner already wrote) unless --overwrite. One update per listing, logged
by db.py with the source URL. Prints what it did or would do.
Money values carry an "as of" date (review.csv as_of): written to a "<column>_as_of" column when the table has one,
otherwise added to the value as " (as of Nov 2026)" so visitors know how fresh a price is."""
import argparse, csv, json, os, subprocess, sys, time

ap = argparse.ArgumentParser()
for k in ("--db-py", "--site-url", "--key-env", "--table"):
    ap.add_argument(k, required=True)
ap.add_argument("--id-column", default="id")
ap.add_argument("--slug", default="")
ap.add_argument("--overwrite", action="store_true")
ap.add_argument("--apply", action="store_true")
a = ap.parse_args()

fields = {f["field"]: f.get("column", f["field"]) for f in json.load(open("output/fields.json"))}
approved = {}
for r in csv.DictReader(open("output/review.csv", newline="")):
    ok = (r.get("approve (y/n)") or r.get("approve") or "").strip().lower() in ("y", "yes")
    if ok and r["status"] == "VERIFIED" and r["field"] in fields:
        approved.setdefault(r["listing_id"], []).append(r)
if not approved:
    sys.exit("Nothing approved yet. The owner marks y in the approve column of output/review.csv (or says 'approve all VERIFIED').")

base = ["python3", a.db_py]
conn = ["--site-url", a.site_url, "--key-env", a.key_env, "--table", a.table]

# Always save the approved values as a sheet too (for owners who import by hand or can't add columns yet)
os.makedirs("output", exist_ok=True)
with open("output/approved.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["listing_id", "column", "value", "as_of", "scope", "source_url", "quote"])
    for lid, rs in approved.items():
        for r in rs:
            w.writerow([lid, fields[r["field"]], r["value"], r.get("as_of", ""), r.get("scope", ""), r["source_url"], r["quote"]])

cols = sorted(set(fields[r["field"]] for rs in approved.values() for r in rs))
probe = subprocess.run(base + ["select"] + conn + ["--columns", "*", "--limit", "1"], capture_output=True, text=True)
try:
    have = set(((json.loads(probe.stdout).get("rows") or [{}])[0]).keys())
except ValueError:
    sys.exit(f"Could not read the table: {probe.stdout or probe.stderr}")
missing = [c for c in cols if have and c not in have]
if missing:
    print("Not in the table yet (kept in output/approved.csv, write them after Step 8b by running this again): " + ", ".join(missing))
    cols = [c for c in cols if c not in missing]
    approved = {lid: [r for r in rs if fields[r["field"]] not in missing] for lid, rs in approved.items()}
    approved = {lid: rs for lid, rs in approved.items() if rs}
    if not approved:
        sys.exit("Nothing to write yet: every approved value needs a column that doesn't exist. They are saved in output/approved.csv.")

written = skipped = 0
for lid, rs in approved.items():
    cur = subprocess.run(base + ["select"] + conn + ["--where", f"{a.id_column}=eq.{lid}", "--columns", ",".join(cols), "--limit", "1"],
                         capture_output=True, text=True)
    try:
        row = (json.loads(cur.stdout).get("rows") or [{}])[0]
    except ValueError:
        sys.exit(f"Could not read listing {lid}: {cur.stdout or cur.stderr}")
    for r in rs:  # one update per value, so each log line carries its own source URL
        col = fields[r["field"]]
        if row.get(col) not in (None, "") and not a.overwrite:
            print(f"skip {lid} {col}: already has a value")
            skipped += 1
            continue
        sets = {col: r["value"]}
        if r.get("as_of"):
            if f"{col}_as_of" in have:
                sets[f"{col}_as_of"] = r["as_of"]
            else:
                sets[col] = f'{r["value"]} (as of {time.strftime("%b %Y", time.strptime(r["as_of"], "%Y-%m-%d"))})'
        cmd = base + ["update"] + conn + ["--allowed-tables", a.table, "--match", f"{a.id_column}=eq.{lid}",
                                         "--set", json.dumps(sets), "--why", "reddit-listing-research (owner approved)",
                                         "--source", r["source_url"]] + (["--slug", a.slug] if a.slug else [])
        if not a.apply:
            cmd.append("--dry-run")
        out = subprocess.run(cmd, capture_output=True, text=True)
        print(f"{'wrote' if a.apply else 'would write'} {lid} {col} = {sets[col]}" if out.returncode == 0 else f"FAILED {lid} {col}: {out.stdout or out.stderr}")
        written += out.returncode == 0
print(f"{'Written' if a.apply else 'Dry run'}: {written} values, {skipped} skipped (already filled). Sheet: output/approved.csv."
      + ("" if a.apply else " Add --apply to write."))
