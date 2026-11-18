#!/usr/bin/env python3
"""Onboarding step tracker. Tells you (Hermes) exactly what to do next, so onboarding never ends early.

Run it after EVERY step. Never end onboarding unless it prints DONE.

    python3 onboard_next.py --slug <slug>                         # what's next
    python3 onboard_next.py --slug <slug> --set stage=building    # record an answer (repeat --set as needed)
    python3 onboard_next.py --slug <slug> --set chosen='["listing-check","content-opportunities"]'
    python3 onboard_next.py --slug <slug> --helper listing-check --set sample_status=done
    python3 onboard_next.py --slug <slug> --helper internal-links --set sample_status=blocked \\
        --set blocked_reason="site security blocks page reading" \\
        --set blocked_fix="2 minute step: let Hermes past your site's security" --set blocked_told=true
    python3 onboard_next.py --slug <slug> --status                 # print the saved state

State lives in $DIROPS_REPO/notes/<slug>/onboarding.json (default repo /data/workspace/directory-ops).
Values given to --set are read as JSON when possible (true, 3, ["a","b"]), otherwise as text.

Top level keys: stage (idea|building|live|earning), goal (traffic|accurate_listings|leads|richer_pages|not_sure),
website (address or "none"), scan_done (true|skipped), plan_shown, chosen (list of helper names), summary_sent.
Per helper (--helper NAME): card_shown, card_ok, teach_me ("answered"|"skip"), connected (true|"not_needed"),
settings_done, sample_status ("done"|"blocked"), blocked_reason, blocked_fix, blocked_told, sample_ok,
cadence (e.g. "Mondays 9 AM", "one-time", "held until real listings").
"""
import argparse
import json
import os
import sys

STEPS_PER_HELPER = ["card_shown", "card_ok", "teach_me", "connected", "settings_done", "sample_status",
                    "sample_ok", "cadence"]

# Helpers that serve each goal, strongest first. The game plan picks 3 to 6 that fit the site.
GOAL_HELPERS = {
    "traffic": ["broken-links-and-seo-errors", "internal-links", "content-opportunities", "tool-page-finder",
                "reddit-listing-research", "page-copy-refresh", "keep-pages-up-to-date"],
    "accurate_listings": ["listing-check", "inbox-triage", "keep-pages-up-to-date", "reddit-listing-research"],
    "leads": ["lead-routing", "inbox-triage", "listing-check", "content-opportunities"],
    "richer_pages": ["reddit-listing-research", "listing-check", "page-copy-refresh", "tool-page-finder"],
    "not_sure": [],  # use the stage defaults in SKILL.md Step 3
}
PLAIN = {
    "listing-check": "Keep listings accurate", "inbox-triage": "Handle your inbox",
    "lead-routing": "Send leads to businesses", "content-opportunities": "Articles people search for",
    "reddit-listing-research": "Richer listing pages", "tool-page-finder": "Free tools that bring traffic",
    "broken-links-and-seo-errors": "Fix SEO problems", "internal-links": "Connect your pages",
    "page-copy-refresh": "Fresh page text", "keep-pages-up-to-date": "Keep fee and price pages current",
}
SKILLS = os.environ.get("DIROPS_SKILLS", "/data/skills/directory-ops")


def state_path(repo, slug):
    return os.path.join(repo, "notes", slug, "onboarding.json")


def load(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"helpers": {}}


def save(path, st):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, path)


def parse_value(v):
    try:
        return json.loads(v)
    except ValueError:
        return v


def helper_missing(h):
    """First unfinished sub step for one helper, or None when it's complete."""
    for k in STEPS_PER_HELPER:
        if k == "sample_ok" and h.get("sample_status") == "blocked":
            continue  # a blocked sample can't be approved; the owner was told the reason and fix instead
        if k == "sample_status" and h.get("sample_status") == "blocked":
            if not (h.get("blocked_reason") and h.get("blocked_fix") and h.get("blocked_told") is True):
                return "blocked_explained"
            continue
        if h.get(k) in (None, "", False):
            return k
    return None


def say(step, text, run=""):
    print(f"NEXT: {step}")
    print(text)
    if run:
        print(f"RUN: {run}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Onboarding step tracker (run after every step).")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--repo", default=os.environ.get("DIROPS_REPO", "/data/workspace/directory-ops"))
    ap.add_argument("--helper", default="", help="apply --set values to this helper")
    ap.add_argument("--set", action="append", default=[], help="key=value (repeatable)")
    ap.add_argument("--status", action="store_true", help="print the saved state")
    a = ap.parse_args()

    path = state_path(a.repo, a.slug)
    st = load(path)
    st.setdefault("helpers", {})
    if a.set:
        target = st["helpers"].setdefault(a.helper, {}) if a.helper else st
        for kv in a.set:
            if "=" not in kv:
                sys.exit(f"ERROR: --set needs key=value, got {kv!r}")
            k, v = kv.split("=", 1)
            val = parse_value(v.strip())
            if k.strip() == "chosen" and isinstance(val, str):   # accept "a,b" as well as ["a","b"]
                val = [h.strip() for h in val.split(",") if h.strip()]
            target[k.strip()] = val
        if "chosen" in st:
            for h in st["chosen"]:
                st["helpers"].setdefault(h, {})
        unfinished = [h for h in (st.get("chosen") or []) if helper_missing(st["helpers"].get(h, {}))]
        if st.get("summary_sent") and (unfinished or not st.get("chosen")):
            st["summary_sent"] = False
            print("REFUSED: onboarding isn't finished. Not set up yet: "
                  + (", ".join(PLAIN.get(h, h) for h in unfinished) or "no helpers chosen")
                  + ". Do not wrap up. Continue with the step below.")
        save(path, st)
    if a.status:
        print(json.dumps(st, indent=1))
        return 0

    # Step 1: understand (at most 3 questions)
    if not st.get("stage"):
        return say("1a stage", "Ask: where are they at? (idea / building / live / earning). Skip if their first "
                   "message already said it, and save it with --set stage=<value>.")
    if not st.get("goal"):
        return say("1b goal", "Ask what they want most: 1 more traffic, 2 accurate listings, 3 leads and money, "
                   "4 richer listing pages, 5 not sure. Save --set goal=traffic|accurate_listings|leads|richer_pages|not_sure.")
    if not st.get("website"):
        return say("1c website", "Ask for the website address ('not live yet' is fine). Save --set website=<address or none>.")
    # Step 2: look
    if not st.get("scan_done"):
        if st["website"] in ("none", "not live", "not_live"):
            return say("2 look", "No live site: skip the scan. Save --set scan_done=skipped, then send 'Here's what "
                       "I see' from what they told you (and their list of businesses later, if a helper needs it).")
        return say("2 look", "Scan the site silently, then send 'Here's what I see' (3 to 5 bullets with numbers). "
                   "If the scan says blocked_by_security, use your web reader (SKILL.md Step 2). Save --set scan_done=true.",
                   f"python3 {SKILLS}/onboard-site/site_scan.py {st['website']} --out {a.repo}/notes/{a.slug}/scan.json")
    # Step 3: the game plan
    if not st.get("plan_shown"):
        sugg = [f"{h} ({PLAIN.get(h, h)})" for h in GOAL_HELPERS.get(st["goal"], [])]
        return say("3 game plan", "Write the game plan for their goal (SKILL.md Step 3): 3 to 6 helpers, each with "
                   "what it does, WHY for their site (evidence from step 2), cadence, and what they get in month 1. "
                   f"Save it to {a.repo}/notes/{a.slug}/game-plan.md, then list EVERY other helper under 'Also available' (one plain line each, numbered on; never hide one), send it, end with "
                   "'Which should I set up? (1 to N / all / pick any numbers)'. The owner decides. Then --set plan_shown=true.\nHelpers for this goal, strongest first: "
                   + (", ".join(sugg) if sugg else "use the stage defaults in SKILL.md Step 3"))
    chosen = st.get("chosen") or []
    if not chosen:
        return say("3b owner picks", "Wait for the owner's pick, then save --set chosen='[\"helper-a\",\"helper-b\"]' "
                   "(in their order).")
    # Step 4: one helper at a time
    for i, name in enumerate(chosen, 1):
        h = st["helpers"].get(name, {})
        miss = helper_missing(h)
        if miss is None:
            continue
        where = f"Helper {i} of {len(chosen)}: {PLAIN.get(name, name)}"
        guide = {
            "card_shown": f"Tell them '{where}'. Show this helper's Playbook card from {SKILLS}/{name}/SKILL.md "
                          "(plain words, about 8 lines). Then ask: 'Anything you'd change about how I do this? (or "
                          f"\"looks good\")'. --helper {name} --set card_shown=true",
            "card_ok": f"Save their answer about the card (changes go into the helper's rules). --helper {name} --set card_ok=true",
            "teach_me": f"Ask this helper's 'Teach me your way' question (its SKILL.md, or the REFERENCE.md section it points to). Save the rules if they "
                        f"answer. --helper {name} --set teach_me=answered (or skip)",
            "connected": "Connect only what this helper needs (its card's 'What I need'; SKILL.md 'Connecting'). "
                         f"Nothing needed → --helper {name} --set connected=not_needed, else connected=true",
            "settings_done": f"Run this helper's Step 0 in quick mode ([essential] questions only, defaults for the "
                             f"rest) and write its settings. --helper {name} --set settings_done=true",
            "sample_status": "Run this helper's Onboarding sample (its Playbook card) and show it. If it fails, "
                             "use its fallback; still failing → explain the reason and the fix in plain words, then "
                             f"--helper {name} --set sample_status=blocked --set blocked_reason=... --set blocked_fix=... "
                             f"--set blocked_told=true. Worked → --helper {name} --set sample_status=done",
            "blocked_explained": "This helper is marked blocked but the owner hasn't been told the reason AND the fix. "
                                 f"Tell them in plain words, then --helper {name} --set blocked_reason=... "
                                 "--set blocked_fix=... --set blocked_told=true",
            "sample_ok": f"Ask 'Good? (yes / change …)'. Apply changes, then --helper {name} --set sample_ok=true",
            "cadence": "Ask one question to set its rhythm (e.g. 'Every Monday at 9 AM your time, OK?'; one-time "
                       "helpers: 'Want me to repeat this every few months?'; blocked or held: say when it will start). "
                       f"Then --helper {name} --set cadence=\"<what was agreed>\"",
        }[miss]
        return say(f"4 {where} -> {miss}", guide)
    # Step 5: month-1 summary
    if not st.get("summary_sent"):
        return say("5 month-1 summary", "Send the month-1 summary (SKILL.md Step 5): what's running and when, what "
                   "they'll receive this month, anything blocked with its fix, where to see results, how to change "
                   "things. Then --set summary_sent=true")
    print("DONE: every chosen helper delivered its sample or the owner knows exactly why not and how to fix it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
