"""Shared helpers. Standard library only. Do not edit unless a step says so."""
import json, os, sys, time, urllib.request, urllib.parse

if any(a in ("-h", "--help") for a in sys.argv[1:]):
    # Every script's own docstring is its help text; works even before research.json exists.
    print((sys.modules["__main__"].__doc__ or "See SKILL.md").strip())
    sys.exit(0)

ARCTIC = "https://arctic-shift.photon-reddit.com/api"
UA = "directory-research-skill/1.0"


def load_config(path="research.json"):
    with open(path) as f:
        return json.load(f)


ARCTIC_DOWN = [0]   # calls in a row that failed every retry; after 2, the archive counts as down for this run


def arctic_get(endpoint, params, tries=4, wait=8):
    """Call the Arctic Shift archive. Returns a list of rows, or None if it kept failing.
    A list (even empty) means the call worked. None means it timed out every time.
    The archive is slow by nature (heavy queries take up to a minute), so it keeps a longer timeout than websites;
    but once 2 calls in a row fail every retry, later calls return None at once, so a dead archive can't stall a run."""
    if ARCTIC_DOWN[0] >= 2:
        print("  archive did not answer twice in a row: skipping further archive calls this run (rerun later)",
              file=sys.stderr)
        return None
    url = f"{ARCTIC}/{endpoint}?" + urllib.parse.urlencode(params)
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            raw = urllib.request.urlopen(req, timeout=60).read().decode("utf8", "ignore")
            data = json.loads(raw, strict=False)
            if data.get("data") is not None:
                ARCTIC_DOWN[0] = 0
                return data["data"]
        except Exception:
            pass
        if attempt < tries - 1:
            time.sleep(wait * (attempt + 1))
    ARCTIC_DOWN[0] += 1
    return None


def save_json(obj, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
    os.replace(tmp, path)
