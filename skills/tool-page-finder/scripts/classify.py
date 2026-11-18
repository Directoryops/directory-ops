#!/usr/bin/env python3
"""STEP 3. Turn keywords into tool ideas and flag the ones a human/agent must check.

Usage:
  python3 classify.py suggestions.csv --seeds-file seeds.txt --out candidates.csv
  python3 classify.py suggestions.csv my_export.csv --seeds-file seeds.txt --out candidates.csv

Inputs: one or more CSV files. Each needs a keyword column (keyword / query /
top queries / search term). Optional demand columns are detected by name:
  hits                      -> from suggest.py (autocomplete, NOT volume)
  volume / search volume / avg. monthly searches -> real volume (Ahrefs, Semrush, Keyword Planner)
  impressions               -> Google Search Console
If ANY input has volume or impressions, the run is in DATA MODE and demand =
sum of volume (+ impressions) per tool idea. Otherwise FREE MODE: demand = sum
of autocomplete hits.

Outputs:
  candidates.csv   one row per tool idea, with an id (C01, C02, ...)
  review.txt       the ideas the agent must answer yes/no for (step 4)
"""
import argparse, collections, csv, re, sys

TYPES = [
 ("value lookup",       r"\b(price (checker|lookup|tracker|history)|value (checker|lookup)|worth|valuation|appraisal|sell for|price guide)\b"),
 ("fee calculator",     r"\b(fees?|commission|take (from|out)|takes|percentage does|percent does|payout|profit|margin|charge to sell)\b"),
 ("cost estimator",     r"\b(cost|costs|price|prices|pricing|price per|per pound|by weight|how much (is|are|does|do|for|to)|rates?|quote|estimate|estimator|budget)\b"),
 ("value lookup",       r"\b(value|resale)\b"),
 ("converter or sizing",r"\b(convert|converter|conversion|size|sizes|sizing|chart|dimensions?|measure)\b"),
 ("schedule tool",      r"\b(schedule|calendar|when (is|does|do|are)|what day|best (time|day)|hours|open on|restock|deadline|how long)\b"),
 ("checker",            r"\b(checker|eligib|qualify|am i|do i need|can i|is it legal|requirements?)\b"),
 ("comparison tool",    r"\b(vs|versus|compare|comparison|alternatives?)\b"),
 ("generator",          r"\b(generator|template|maker|builder)\b"),
 ("quiz",               r"\b(quiz|practice test)\b"),
 ("calculator",         r"\b(calculator|calc|calculate|formula|how many)\b"),
]
LOCAL = re.compile(r"\b(near me|near by|nearby|locations?|located|address|directions|open now|closest|reviews?)\b"
                   r"|\b(al|ak|az|ar|ca|co|ct|de|fl|ga|hi|id|il|in|ia|ks|ky|la|me|md|ma|mi|mn|ms|mo|mt|ne|nv|nh|nj|nm|ny|nc|nd|oh|ok|or|pa|ri|sc|sd|tn|tx|ut|vt|va|wa|wv|wi|wy)$"
                   r"|\bfort worth\b")
STOP = set(("the a an of for to in on at is are does do how much what when best my your and with by from vs near me per "
            "take takes sale sales sell selling seller sellers charge charges percent percentage much many it i "
            "calculator calculators calc fee fees cost costs price prices pricing value worth chart size sizes "
            "2023 2024 2025 2026 2027 2028 usa us uk app online free reddit today list increase pound pounds weight "
            "guide there average avg new really still actually much good per").split())
# words that may appear in a tool subject without making it off-topic
GENERIC = set("shipping tax taxes return returns label labels sold item items order orders buyer buyers listing listings "
              "time day days week month year hour hours fast cheap cheapest discount coupon post posting list go shop "
              "visit buy buying store stores outlet outlets success rate open close closed closing ship shipping "
              "deliver delivery have has can use you get pay paid holiday holidays sunday sundays saturday monday "
              "christmas easter thanksgiving memorial labor july 4th year's eve long gallon gallons litre litres liter liters "
              "inch inches feet ft cm kg lb lbs run running month monthly".split())
MESSY = re.compile(r"\b(reddit|quora|20\d\d|uk|usa|canada|australia|free|today)\b")
REVIEW_TOP = 25   # only the top 25 ideas are ever sent for a yes/no check
# other-country searches (the default market is the US; use --keep-countries to keep them)
COUNTRY = re.compile(r"\b(in|india|pakistan|bangladesh|bd|sri lanka|nepal|nigeria|kenya|ghana|philippines|malaysia|"
                     r"singapore|dubai|uae|qatar|saudi|kuwait|south africa|uk|canada|australia|nz|new zealand|ireland|kerala|chennai|"
                     r"england|scotland|wales|ontario|quebec|alberta|bc|nsw|victoria|queensland|"
                     r"mumbai|delhi|bangalore|hyderabad|karachi|lahore|dhaka|rupees?|rs|inr|pkr|bdt|lkr)\b(?! (a|the|my|your|one)\b)")
SHOP = re.compile(r"^(how much (is|are|does|do)( an?| the)? )?[a-z0-9' ]+? (price|prices|cost|costs|best price|price list|rates?)( in [a-z ]+| near me)?$|^how much (is|are|does|do)( an?| the)? [a-z0-9' ]+( cost)?$")
# question shapes that want a fact or statistic, not a tool
NOT_TOOL = re.compile(r"\bunder \d+|\bat (walmart|amazon|target|costco|petco|petsmart|lowes|home depot|tractor supply)\b|\b(cancel|refund|delete|login|log in|sign up|customer service|phone number|"
                      r"how long (does|do|is) .* (take|ship|deliver)|does \w+ have|worth it|worth selling|worth to|are there|how many \w+ (sellers|users|people|stores|locations)|net worth|stock price|share price|who owns|ceo|"
                      r"price increases?|price hikes?|how much is [a-z' ]+ worth|earnings|layoffs?|lawsuit|recall|bankrupt\w*|news|"
                      r"(business |company |shop |store )?names?|slogans?|logos?|captions?|bios?|usernames?|hashtags?|taglines?|"
                      r"\w+ (generator|maker) for (business|instagram|tiktok)|app|apps|software|crm|pos system|quiz|quizzes|exam|test questions|certification|course|jobs?|salary|license)\b|\b(generator|maker|ideas)$")

def read_seeds(path):
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"): continue
        b, s = line.split(":", 1) if ":" in line else ("core", line)
        out.append((b.strip().lower(), s.strip().lower()))
    if not out: sys.exit("ERROR: seeds.txt has no seeds")
    return out

def ttype(k):
    for name, rx in TYPES:
        if re.search(rx, k): return name
    return None

def subject(k, seed):
    words = [w for w in re.findall(r"[a-z0-9']+", k) if w not in STOP]
    words = [w for w in words if not any(re.fullmatch(rx, w) for _, rx in TYPES)]
    return " ".join(words[:3]) or seed

def read_any(path):
    """Read CSV/TSV exports from Ahrefs, Semrush, Search Console, Keyword Planner (UTF-8 or UTF-16, comma or tab)."""
    raw = open(path, "rb").read()
    enc = "utf-16" if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else "utf-8-sig"
    text = raw.decode(enc, "replace")
    lines = text.splitlines()
    # Keyword Planner puts 2 title lines above the header
    def is_header(l):
        cells = [c.strip().strip('"').lower() for c in re.split(r"[\t,]", l)]
        return len(cells) > 1 and any(c in ("keyword", "keywords", "query", "top queries", "search term", "search query") for c in cells)
    start = next((i for i, l in enumerate(lines[:6]) if is_header(l)), 0)
    body = "\n".join(lines[start:])
    delim = "\t" if body.split("\n")[0].count("\t") > body.split("\n")[0].count(",") else ","
    return list(csv.DictReader(body.splitlines(), delimiter=delim))

def find_col(row, names):
    return next((c for c in row if c and c.lower().strip() in names), None)

def num(x):
    try: return float(str(x).replace(",", "").strip() or 0)
    except ValueError: return 0.0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="+"); ap.add_argument("--out", default="candidates.csv")
    ap.add_argument("--seeds-file", required=True)
    ap.add_argument("--keep-countries", action="store_true", help="keep searches that name another country/currency")
    ap.add_argument("--min-demand", type=float, default=None,
                    help="drop ideas below this total demand (default: 3 in free mode, 50 in data mode)")
    a = ap.parse_args()
    seeds = read_seeds(a.seeds_file)
    vocab = set(w for _, s in seeds for w in s.split())

    # merge all input files by keyword
    K = {}   # keyword -> {"hits":, "volume":}
    data_mode = False
    for path in a.csv:
        rows = read_any(path)
        if not rows: print(f"WARNING: {path} is empty, skipped"); continue
        kc = find_col(rows[0], ("keyword", "query", "top queries", "keywords", "search term", "search query"))
        if not kc: sys.exit(f"ERROR: {path} has no keyword column. Columns found: {list(rows[0])}")
        hc = find_col(rows[0], ("hits",))
        vc = find_col(rows[0], ("volume", "search volume", "avg. monthly searches", "avg monthly searches", "impressions"))
        if vc: data_mode = True
        for r in rows:
            k = " ".join(str(r[kc]).lower().split())
            if not k: continue
            e = K.setdefault(k, {"hits": 0.0, "volume": 0.0})
            e["hits"] = max(e["hits"], num(r[hc]) if hc else 1.0)
            if vc: e["volume"] = max(e["volume"], num(r[vc]))
        print(f"read {len(rows)} rows from {path} (demand column: {vc or hc or 'none'})")
    mode = "DATA" if data_mode else "FREE"
    min_d = a.min_demand if a.min_demand is not None else (50 if data_mode else 3)

    groups = collections.defaultdict(lambda: {"kws": [], "hits": 0.0, "volume": 0.0, "buckets": collections.Counter()})
    kept = dropped = 0
    for k, e in K.items():
        seed = next(((b, s) for b, s in seeds if all(w in k.split() or w in k for w in s.split())), None)
        t = ttype(k) if seed else None
        if not seed or not t or LOCAL.search(k) or NOT_TOOL.search(k) or (not a.keep_countries and COUNTRY.search(k) and re.search(r"\b(in|rupees?|rs|inr|pkr|bdt|lkr)\b", k) and not re.search(r"\bin (a|the|my|your|one)\b", k)):
            dropped += 1; continue
        if seed[0] == "entity" and t == "cost estimator" and SHOP.match(k):
            dropped += 1; continue
        g = groups[(t, subject(k, seed[1]))]
        g["kws"].append((e["volume"] if data_mode else e["hits"], k))
        g["hits"] += e["hits"]; g["volume"] += e["volume"]; g["buckets"][seed[0]] += 1
        kept += 1
    dem = (lambda g: g["volume"]) if data_mode else (lambda g: g["hits"])
    out = sorted([x for x in groups.items() if dem(x[1]) >= min_d], key=lambda x: -dem(x[1]))

    review = []
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "tool_type", "subject", "main_keyword", "demand", "demand_source", "autocomplete_hits",
                    "n_keywords", "bucket", "needs_check", "top_keywords"])
        for i, ((t, s), g) in enumerate(out, 1):
            # main keyword: highest demand, but prefer clean phrasing (no reddit/years/countries)
            ks = sorted(g["kws"], key=lambda x: (bool(MESSY.search(x[1])), -x[0], len(x[1])))
            odd = [x for x in s.split() if x not in vocab and x.rstrip('s') not in vocab and x not in GENERIC]
            cid = f"C{i:02d}"
            if odd and i > REVIEW_TOP:
                continue   # odd words and low in the list: drop without asking (keeps step 4 short)
            needs = "yes" if odd else ""
            if needs: review.append((cid, t, s, ks[0][1], odd))
            w.writerow([cid, t, s, ks[0][1], round(dem(g), 1), "volume" if data_mode else "autocomplete",
                        round(g["hits"], 1), len(ks), g["buckets"].most_common(1)[0][0], needs,
                        "; ".join(k for _, k in ks[:8])])
    with open("review.txt", "w", encoding="utf-8") as f:
        f.write("# STEP 4. For each line: would a visitor of this website use this tool?\n")
        f.write("# Replace ?? with yes or no. Change nothing else on the line. Save the file.\n")
        for cid, t, s, mk, odd in review:
            f.write(f"{cid} ?? | {t} | main keyword: {mk} | unusual words: {', '.join(odd)}\n")

    print(f"DONE: {mode} MODE. {len(out)} tool ideas kept ({kept} keywords matched, {dropped} dropped, ideas under demand {min_d:g} removed) -> {a.out}")
    for (t, s), g in out[:15]:
        print(f"  {dem(g):>8.0f}  {t:<20} {s}  ({len(g['kws'])} kws)")
    print(f"REVIEW: {len(review)} ideas need a yes/no decision -> review.txt (step 4)")
    if len(out) < 10: print("WARNING: fewer than 10 candidates. Add 3 more entity seeds and redo steps 2 and 3.")

if __name__ == "__main__":
    main()
