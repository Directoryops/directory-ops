"""Step 5. Download the comments for every thread in data/selected.json.
Usage: python3 scripts/pull_comments.py
One thread at a time, slowly, on purpose (the archive is a free volunteer service).
RESUMABLE: if it stops, run the same command again and it continues where it left off.
Saves data/comments.json. Free. About 8 seconds per thread (250 threads = ~35 minutes)."""
import json, os, time
from common import arctic_get, save_json

selected = json.load(open("data/selected.json"))
path = "data/comments.json"
done = json.load(open(path)) if os.path.exists(path) else {}
failed = []

for i, p in enumerate(selected):
    if p["id"] in done:
        continue
    rows = arctic_get("comments/search", {"link_id": p["id"], "limit": 100,
                                          "fields": "body,score,parent_id,created_utc"})
    if rows is None:
        failed.append(p["id"])
        continue
    done[p["id"]] = rows
    if len(done) % 20 == 0:
        save_json(done, path)
        print(f"progress: {len(done)}/{len(selected)} threads", flush=True)
    time.sleep(1.2)

save_json(done, path)
print(f"DONE: {len(done)} threads, {sum(len(v) for v in done.values())} comments -> {path}")
if failed:
    print(f"{len(failed)} threads failed. Run this command again to retry them.")
