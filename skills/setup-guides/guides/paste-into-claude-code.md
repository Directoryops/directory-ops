# Make a change to your website with Claude Code

**Why:** Hermes can't edit your website's code. It writes the exact instructions, and Claude Code (an AI coding app on your computer) makes the change safely.

**You need:** 5 to 15 minutes, Claude Code, and your website's project folder. No Claude Code? Send the instructions to whoever built your site.

1. Open **Claude Code** in your website's project (the same folder you build the site in).
2. Copy the instructions Hermes gave you (the box starting with "Make these changes on a branch").
3. Paste them into Claude Code and press Enter.
4. Wait until it gives you a **preview link**.
5. Open the preview link and look at the page it changed. Does it look right?
6. If yes, tell Claude Code **"merge"**. If not, tell it what's wrong in plain words.
7. Tell me "done". I'll check the live site.

**You'll know it worked when** Hermes confirms the change is live.

**Stuck?** Tell me the last thing Claude Code said.

---
## For Hermes
- Every prompt you hand over: starts with "Make these changes on a branch, then give me the preview link and don't merge until I approve", lists each change exactly, and ends with how to verify.
- After "done": re-check the live page(s) with the relevant skill's check (e.g. `site_crawl.py` for links/redirects) and report.

<sub>Workflow guide (no third-party UI labels). Checked 2026-11-17.</sub>
