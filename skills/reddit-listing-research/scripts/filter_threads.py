"""Step 4. Keep only threads where a real person is choosing, comparing, paying for,
or complaining about the business type. Uses word lists from research.json. Free. Instant.
Usage: python3 scripts/filter_threads.py            (strict: a decision word in the title, or a question
                                                    title whose post starts with a decision word)
       python3 scripts/filter_threads.py --loose    (thin niches only: any question title, or a decision word anywhere)
Saves data/selected.json and prints the 40 biggest kept threads. YOU then count how many of the 40 are about
choosing, paying for, comparing or complaining about this kind of business: target 30+ (3 of 4)."""
import json, re, sys
from common import load_config, save_json

cfg = load_config()
lim = cfg["limits"]
LOOSE = "--loose" in sys.argv


def rx(words, whole_words=False):
    words = [re.escape(w.strip()) for w in words if w.strip()]
    if not words:
        return None
    if whole_words:
        return re.compile(rf"\b(?:{'|'.join(words)})\b", re.I)
    # stems match the START of a word ("cremat" matches "cremation", but "fee" no longer matches "feeling")
    return re.compile("|".join((r"\b" + w + (r"(?:s|es|ed|d|ing)?\b" if len(w) <= 3 else "")) if w[:1].isalnum() else w for w in words), re.I)


# decision and business words match the start of a word; short ones (3 letters or less) only whole words
decision = rx(cfg["decision_words"])
business = rx(cfg["business_words"])
# exclude words match WHOLE words only ("cat" must not remove "location")
exclude = rx(cfg.get("exclude_words", []), whole_words=True)

posts = json.load(open("data/posts.json"))
focused_kept, local_kept = [], []
for p in posts:
    title = p.get("title") or ""
    text = title + " " + (p.get("selftext") or "")[:500]
    if (p.get("num_comments") or 0) < lim["min_comments"]:
        continue
    if exclude and exclude.search(text):
        continue
    if p.get("_source") == "local":
        # big general subs: the title must name the business type
        if business and business.search(title):
            local_kept.append(p)
    else:
        # the niche's own community is on topic already: keep questions, decisions, prices or problems
        # (title OR the start of the post), so "First time, what should I expect?" posts are not lost
        start = (p.get("selftext") or "")[:300]
        if LOOSE:
            keep = "?" in title or (decision and decision.search(text))
        else:
            keep = bool(decision and (decision.search(title) or ("?" in title and decision.search(start))))
        if keep:
            focused_kept.append(p)

# The niche's own community comes first: it gets up to 70% of the threads, general subs fill the rest
by_c = lambda p: -(p.get("num_comments") or 0)
focused_kept.sort(key=by_c); local_kept.sort(key=by_c)
cap = lim["max_threads"]
take_f = focused_kept[: max(int(cap * 0.7), cap - len(local_kept))]
kept = take_f + local_kept[: cap - len(take_f)]
kept += focused_kept[len(take_f): len(take_f) + cap - len(kept)]
kept.sort(key=by_c)
print(f"focused (niche community): {len([p for p in kept if p.get('_source') != 'local'])} kept of {len(focused_kept)} matching | "
      f"general subs: {len([p for p in kept if p.get('_source') == 'local'])} kept of {len(local_kept)} matching")
if cfg["subreddits"].get("focused") and not focused_kept:
    print("WARNING: 0 threads from the niche's own community. Check its activity (discover_subs.py) and "
          "lower min_comments, or add more decision_words. Its threads should be the main source.")
save_json(kept, "data/selected.json")
total_c = sum(p.get("num_comments") or 0 for p in kept)
print(f"KEPT {len(kept)} threads (~{total_c} comments) out of {len(posts)} posts -> data/selected.json")
for p in kept[:40]:
    print(f"  {p.get('num_comments'):>4} r/{p['subreddit']} | {p['title'][:90]}")
print("NEXT: count how many of these 40 titles are about choosing / paying / comparing / complaining about this kind "
      "of business. Under 30 of 40: add the off-topic words to exclude_words and run again. Report the share to the owner.")
