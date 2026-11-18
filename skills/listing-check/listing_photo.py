#!/usr/bin/env python3
"""Free exterior photo for a listing (no API key): Google Street View at the place's coordinates.

1) Get candidate photos (8 angles; widens to the nearest street photo within 200 m if the pin has none), then LOOK at each and pick the one that shows the storefront:
    python3 listing_photo.py streetview <lat> <lng> --out $DIROPS_REPO/notes/<slug>/tmp/listing-photos
   (lat/lng come from gmaps_lookup.py, fields "lat" and "lng")

2) Upload the chosen one to the site's public Supabase Storage bucket and get its URL:
    python3 listing_photo.py upload <file> --path <folder>/<slug>.jpg \
        --site-url https://<project>.supabase.co --key-env <SLUG>_SUPABASE_KEY [--bucket listing-photos]

Prints JSON. Upload prints {"status": "ok", "public_url": ...}: save that URL in the listing's photo field.

Rules for the agent:
- Only use a photo that clearly shows this business's building or sign. If none of the 8 angles does, use no photo.
- Never use photos from other directories or competitors.
- The bucket must exist and be public (the skill's setup step creates it).
"""
import argparse
import json
import os
import sys
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
SV = "https://geo0.ggpht.com/cbk?cb_client=maps_sv.tactile&output=thumbnail&thumb=2&w=800&h=450&ll={lat},{lng}{extra}"
ANGLES = [("north", 0), ("northeast", 45), ("east", 90), ("southeast", 135),
          ("south", 180), ("southwest", 225), ("west", 270), ("northwest", 315)]


def _get(url: str):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        data = urllib.request.urlopen(req, timeout=20).read()
    except Exception:  # noqa: BLE001
        return None
    return data if len(data) >= 5000 else None  # no coverage returns a tiny placeholder


def streetview(lat: str, lng: str, out: str) -> dict:
    """Pins often sit in the middle of a building, away from the road. If there's no photo at the
    exact pin, use the nearest street photo within 50, 100, then 200 meters, and take 8 angles so
    one of them faces the building."""
    os.makedirs(out, exist_ok=True)
    for radius in (None, 50, 100, 200):
        r = f"&radius={radius}" if radius else ""
        if not _get(SV.format(lat=lat, lng=lng, extra=r)):
            continue
        files = []
        for label, yaw in ANGLES:
            data = _get(SV.format(lat=lat, lng=lng, extra=f"{r}&yaw={yaw}"))
            if data:
                path = os.path.join(out, f"streetview-{label}.jpg")
                with open(path, "wb") as f:
                    f.write(data)
                files.append({"file": path, "angle": label})
        if files:
            return {"status": "ok", "search_radius_m": radius or 0, "images": files,
                    "note": "Look at every image; pick the one facing the business's building or sign."}
    return {"status": "none", "images": []}


def upload(file: str, path: str, site_url: str, key_env: str, bucket: str) -> dict:
    key = (os.environ.get(key_env) or "").strip().strip("\"'")
    if not key:
        return {"status": "error", "error": f"env var {key_env} is not set"}
    ctype = {"png": "image/png", "webp": "image/webp"}.get(file.rsplit(".", 1)[-1].lower(), "image/jpeg")
    url = f"{site_url.rstrip('/')}/storage/v1/object/{bucket}/{path}"
    req = urllib.request.Request(url, data=open(file, "rb").read(), method="POST", headers={
        "apikey": key, "Content-Type": ctype, "x-upsert": "true", **({} if key.startswith("sb_") else {"Authorization": f"Bearer {key}"})})
    try:
        urllib.request.urlopen(req, timeout=30).read()
    except urllib.error.HTTPError as e:
        return {"status": "error", "error": f"{e.code} {e.read()[:200].decode('utf-8', 'ignore')}"}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": str(e)[:200]}
    return {"status": "ok", "public_url": f"{site_url.rstrip('/')}/storage/v1/object/public/{bucket}/{path}"}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("streetview")
    a.add_argument("lat")
    a.add_argument("lng")
    a.add_argument("--out", default=os.path.join(os.environ.get("DIROPS_REPO", "/data/workspace/directory-ops"), "notes", "tmp", "listing-photos"))
    b = sub.add_parser("upload")
    b.add_argument("file")
    b.add_argument("--path", required=True)
    b.add_argument("--site-url", required=True)
    b.add_argument("--key-env", required=True)
    b.add_argument("--bucket", default="listing-photos")
    args = ap.parse_args()
    if args.cmd == "streetview":
        print(json.dumps(streetview(args.lat, args.lng, args.out)))
    else:
        print(json.dumps(upload(args.file, args.path, args.site_url, args.key_env, args.bucket)))


if __name__ == "__main__":
    sys.exit(main())
