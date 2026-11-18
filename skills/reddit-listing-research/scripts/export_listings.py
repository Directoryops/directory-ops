"""Step 9 helper. Turn the directory's listings into data/listings.csv (id,name,website) for fetch_sites.py.
Free. No AI.

Supabase sites (directory-db helper; run from this research folder):
    python3 /data/skills/directory-ops/directory-db/db.py select --site-url <url> --key-env <KEY_ENV> \
        --table <listings table> --columns <id col>,<name col>,<website col> --all > data/listings.json
    python3 <this folder>/export_listings.py data/listings.json --id <id col> --name <name col> --website <website col>

Any other source: give it a CSV that has those three columns (any names) instead of the JSON:
    python3 <this folder>/export_listings.py my_export.csv --id ID --name Title --website URL
Rows without a website starting with http are kept in the file but fetch_sites.py skips them."""
import argparse, csv, json, os

ap = argparse.ArgumentParser()
ap.add_argument("source", help="db.py select output (.json) or a CSV export")
ap.add_argument("--id", default="id")
ap.add_argument("--name", default="name")
ap.add_argument("--website", default="website")
ap.add_argument("--address", default="", help="address column (recommended: lets the checker confirm chain pages are about THIS location)")
a = ap.parse_args()

if a.source.endswith(".json"):
    data = json.load(open(a.source))
    rows = data.get("rows", data) if isinstance(data, dict) else data
else:
    rows = list(csv.DictReader(open(a.source, newline="", encoding="utf-8-sig")))
missing = [c for c in (a.id, a.name, a.website, a.address) if c and rows and c not in rows[0]]
if missing:
    raise SystemExit(f"Column(s) not found: {', '.join(missing)}. Columns in the file: {', '.join(rows[0].keys())}")
os.makedirs("data", exist_ok=True)
with open("data/listings.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "name", "website", "address"])
    for r in rows:
        site = (r.get(a.website) or "").strip()
        if site and not site.startswith("http"):
            site = "https://" + site
        w.writerow([r.get(a.id), r.get(a.name), site, r.get(a.address) if a.address else ""])
with_site = sum(1 for r in rows if (r.get(a.website) or "").strip())
print(f"data/listings.csv: {len(rows)} listings, {with_site} with a website")
