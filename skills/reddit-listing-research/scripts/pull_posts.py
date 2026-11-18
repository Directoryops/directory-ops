"""Step 3. Download posts from the subreddits in research.json.
Usage: python3 scripts/pull_posts.py
- "focused" subreddits: downloads the newest posts, page by page (max_pages_per_sub x 100 posts).
- "local" subreddits: big city subs. Only searches post TITLES for each single word in
  local_title_words, because full downloads of big subs are too large and keyword search times out.
Saves to data/posts.json. Free. Takes 5 to 20 minutes. Safe to re run (it starts over)."""
import time
from common import load_config, arctic_get, save_json

cfg = load_config()
FIELDS = "id,title,selftext,num_comments,created_utc,subreddit,score"
posts = {}

for sub in cfg["subreddits"]["focused"]:
    before, got = None, 0
    for page in range(cfg["limits"]["max_pages_per_sub"]):
        params = {"subreddit": sub, "limit": 100, "sort": "desc", "fields": FIELDS}
        if before:
            params["before"] = before
        rows = arctic_get("posts/search", params)
        if not rows:
            break
        for r in rows:
            r["_source"] = "focused"
            posts[r["id"]] = r
        got += len(rows)
        before = rows[-1]["created_utc"]
        time.sleep(1.5)
    print(f"focused r/{sub}: {got} posts")

for sub in cfg["subreddits"].get("local", []):
    for word in cfg.get("local_title_words", []):
        if " " in word:
            print(f"SKIPPED '{word}': local title words must be ONE word")
            continue
        rows = arctic_get("posts/search", {"subreddit": sub, "title": word, "limit": 100,
                                           "sort": "desc", "fields": FIELDS})
        if rows is None:
            print(f"local r/{sub} '{word}': archive timed out 5 times, skipped")
            continue
        for r in rows:
            r["_source"] = "local"
            posts[r["id"]] = r
        print(f"local r/{sub} '{word}': {len(rows)} posts")
        time.sleep(4)

save_json(list(posts.values()), "data/posts.json")
print(f"TOTAL unique posts saved: {len(posts)} -> data/posts.json")
