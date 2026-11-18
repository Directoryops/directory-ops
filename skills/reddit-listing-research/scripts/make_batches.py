"""Step 6a. Split the threads into small reading batches for the AI.
Usage: python3 scripts/make_batches.py
Each batch = up to 8 threads, each with its post text and top 25 comments (by score).
Usernames are NOT included. Writes batches/batch_001.txt, batch_002.txt, ... Free. Instant."""
import json, os
import common  # noqa: F401  (prints this script's help on --help)

PER_BATCH, TOP_COMMENTS, MAX_CHARS = 8, 25, 450


def cut(text, n):
    """Shorten long text at a word boundary and mark it, so quotes are never taken from a cut-off word."""
    if len(text) <= n:
        return text
    return text[:n].rsplit(" ", 1)[0] + " [...]"
selected = {p["id"]: p for p in json.load(open("data/selected.json"))}
comments = json.load(open("data/comments.json"))
for d in ("batches", "extractions"):
    os.makedirs(d, exist_ok=True)
for f in os.listdir("batches"):
    os.remove(os.path.join("batches", f))

blocks = []
for pid, rows in comments.items():
    p = selected.get(pid)
    if not p:
        continue
    rows = [r for r in rows if r.get("body") and r["body"] not in ("[deleted]", "[removed]")]
    rows.sort(key=lambda r: -(r.get("score") or 0))
    lines = [f"THREAD_ID: {pid}",
             f"TITLE: {p['title']}  (r/{p['subreddit']}, {p.get('num_comments')} comments)",
             "POST: " + cut(" ".join((p.get("selftext") or "").split()), 800)]
    for r in rows[:TOP_COMMENTS]:
        lines.append(f"- ({r.get('score')}) " + cut(" ".join(r["body"].split()), MAX_CHARS))
    blocks.append("\n".join(lines))

n = 0
for i in range(0, len(blocks), PER_BATCH):
    n += 1
    with open(f"batches/batch_{n:03d}.txt", "w") as f:
        f.write("\n\n=====\n\n".join(blocks[i:i + PER_BATCH]))
print(f"WROTE {n} batches ({len(blocks)} threads) -> batches/")
