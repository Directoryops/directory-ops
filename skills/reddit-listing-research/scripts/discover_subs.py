"""Step 2. Find the niche's OWN community (the place customers actually talk), not just the obvious name.
Usage: python3 scripts/discover_subs.py --words plasma donor --general beermoney povertyfinance personalfinance
  --words    2 to 4 word stems for the niche (the business word plus the customer word, e.g. "plasma donor",
             "dog groom", "wedding venue"). Used for name search and to judge relevance.
  --general  2 to 4 big subreddits where customers of this niche also post (money, parenting, pets, weddings...).
  --threads  how many of the busiest matching threads in --general to read for mentions (default 15).
  --also     community names you found with a normal web search ("best subreddit for <niche>"), checked too.
How it finds communities (free, about 2 to 4 minutes):
  1. Subreddits whose NAME starts with each word (r/plasmadonation for "plasma").
  2. Subreddits people RECOMMEND inside real threads ("go ask on r/plassing"): the busiest threads in --general
     whose title has the first word are downloaded with their comments and every r/<name> mention is counted.
     This catches slang names a name search never finds.
  3. Each candidate's activity: posts per day and comments per post (recent 100 posts).
Prints a ranked table. The top row marked PRIMARY is the niche's own community: put it FIRST in "focused".
Use only communities whose description or name is about the niche (the table shows the description)."""
import argparse, re, time
from collections import Counter
from common import arctic_get

ap = argparse.ArgumentParser()
ap.add_argument("--words", nargs="+", required=True)
ap.add_argument("--general", nargs="*", default=[])
ap.add_argument("--threads", type=int, default=15)
ap.add_argument("--also", nargs="*", default=[])
a = ap.parse_args()
words = [w.lower() for w in a.words]
general = {g.lower().replace("r/", "") for g in a.general}

info = {}  # name(lower) -> dict(name, subs, desc)
mentions = Counter()


def remember(row):
    n = row.get("display_name") or ""
    if n:
        info[n.lower()] = {"name": n, "subs": row.get("subscribers") or 0,
                           "desc": (row.get("public_description") or "").replace("\n", " ")[:90]}


# 1. name search
for w in words:
    rows = arctic_get("subreddits/search", {"subreddit_prefix": w, "limit": 25}) or []
    for r in rows:
        remember(r)
    time.sleep(2)

# 2. mentions inside real threads
MENTION = re.compile(r"(?<![\w/])/?r/([A-Za-z0-9_]{3,21})\b")
for g in general:
    posts = arctic_get("posts/search", {"subreddit": g, "title": words[0], "limit": 100, "sort": "desc",
                                        "fields": "id,title,selftext,num_comments"})
    if posts is None:
        print(f"r/{g}: archive timed out, skipped (run again later for more mentions)")
        continue
    posts.sort(key=lambda p: -(p.get("num_comments") or 0))
    for p in posts[: a.threads]:
        text = (p.get("title") or "") + " " + (p.get("selftext") or "")
        rows = arctic_get("comments/search", {"link_id": p["id"], "limit": 100, "fields": "body"}) or []
        text += " " + " ".join(c.get("body") or "" for c in rows)
        for m in MENTION.findall(text):
            if m.lower() not in general:
                mentions[m.lower()] += 1
        time.sleep(2)
    print(f"read {min(len(posts), a.threads)} threads in r/{g}")

for n in a.also:
    mentions[n.lower().replace("r/", "")] += 1
for name, _ in mentions.most_common(15):
    if name not in info:
        rows = arctic_get("subreddits/search", {"subreddit_prefix": name, "limit": 5}) or []
        for r in rows:
            if (r.get("display_name") or "").lower() == name:
                remember(r)
        time.sleep(1.5)


def relevant(n, d):
    """Every niche word in the name or description ("plasma" AND "donor": not plasma TVs), or people recommend it
    in real threads AND it is about the niche at all."""
    blob = (n + " " + d["desc"]).lower()
    return all(w in blob for w in words) or (mentions[n] >= 1 and any(w in blob for w in words)) or mentions[n] >= 3


cands = [n for n, d in info.items() if relevant(n, d) and n not in general]
cands.sort(key=lambda n: -(mentions[n] * 1000 + info[n]["subs"]))

# 3. activity
out = []
for n in cands[:10]:
    rows = arctic_get("posts/search", {"subreddit": info[n]["name"], "limit": 100, "sort": "desc",
                                       "fields": "created_utc,num_comments"})
    if not rows:
        continue
    days = max(1, (rows[0]["created_utc"] - rows[-1]["created_utc"]) / 86400)
    per_day = len(rows) / days
    avg_c = sum(r.get("num_comments") or 0 for r in rows) / len(rows)
    last = time.strftime("%Y-%m-%d", time.gmtime(rows[0]["created_utc"]))
    out.append((per_day * avg_c, n, per_day, avg_c, last))
    time.sleep(2)

out.sort(reverse=True)
print(f"\n{'':8} {'subreddit':24} {'posts/day':>9} {'comments/post':>13} {'members':>8} {'recommended in threads':>22}  last post   about")
for i, (score, n, pd, ac, last) in enumerate(out):
    tag = "PRIMARY" if i == 0 else ""
    print(f"{tag:8} r/{info[n]['name']:22} {pd:9.1f} {ac:13.1f} {info[n]['subs']:8} {mentions[n]:22}  {last}  {info[n]['desc'][:60]}")
if not out:
    print("No niche community found. Use big general subreddits with a one-word title search (Step 2, 'local' style).")
else:
    print("\nPut PRIMARY first in research.json 'focused' (unless its description shows it's off topic), "
          "then 1 to 2 more from this table. Under 0.5 posts/day = too small to be the main source.")
