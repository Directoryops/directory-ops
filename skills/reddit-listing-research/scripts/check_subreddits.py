"""Step 2. Check that each subreddit exists in the archive and how active it is.
Usage: python3 scripts/check_subreddits.py sub1 sub2 sub3
Prints one line per subreddit. Free. About 3 seconds per subreddit."""
import sys, time
from common import arctic_get

for sub in sys.argv[1:]:
    sub = sub.replace("r/", "").strip("/")
    rows = arctic_get("posts/search", {"subreddit": sub, "limit": 100, "sort": "desc",
                                       "fields": "id,created_utc,num_comments"})
    if rows is None:
        print(f"{sub}: ARCHIVE TIMEOUT, try again in a minute")
    elif not rows:
        print(f"{sub}: NOT FOUND or empty. Do not use.")
    else:
        newest = time.strftime("%Y-%m-%d", time.gmtime(rows[0]["created_utc"]))
        oldest = time.strftime("%Y-%m-%d", time.gmtime(rows[-1]["created_utc"]))
        days = max(1, (rows[0]["created_utc"] - rows[-1]["created_utc"]) / 86400)
        avg_c = sum(r.get("num_comments") or 0 for r in rows) / len(rows)
        print(f"{sub}: OK. last 100 posts span {oldest} to {newest} "
              f"(~{len(rows)/days:.1f} posts/day), avg {avg_c:.0f} comments/post")
    time.sleep(2)
