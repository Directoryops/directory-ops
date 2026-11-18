# Install directory-ops on Hermes (about 2 minutes)

You need: Hermes Agent WebUI running on Hostinger. That's it. No keys, no GitHub account.

## Step 1: Install

Open your Hermes chat, start a **new chat**, and paste this whole message:

```
Install directory-ops for me:
1. Clone https://github.com/Directoryops/directory-ops.git into /data/workspace/directory-ops (if that folder already exists, run git pull there instead).
2. Copy every folder inside skills/ into /data/skills/directory-ops/ as its own skill (replace older copies, remove skills that no longer exist in the repo).
3. Read CATALOG.md and remember it.
4. Run python3 --version and git --version and tell me both work.
5. Reply with: how many skills you installed, then "Done. Say 'Onboard a site' to start."
```

What success looks like: Hermes lists about 15 skills and ends with **"Done. Say 'Onboard a site' to start."**

## Step 2: Start

Start a **new chat** and say:

```
Onboard a site
```

Hermes asks where you are with your directory, what you want help with, and walks you through the rest one question at a time.

## Updating later

When a new version comes out, start a new chat and paste:

```
Update directory-ops: run git pull in /data/workspace/directory-ops, then copy every folder in skills/ into /data/skills/directory-ops/ again (replace older copies, remove ones that no longer exist). Tell me what changed.
```

Your settings and notes live in `/data/workspace/directory-ops/sites/` and `notes/`. Updating never deletes them.

## Do I need to fork the repo?

No, not to get started. A fork is your own copy on GitHub. It only matters if you want (a) an off-server backup of your settings and notes, or (b) to change the skills yourself. If you want that later, make a fork, then tell Hermes: "Switch directory-ops to my fork at https://github.com/<you>/directory-ops and back up my sites and notes there." Hermes will walk you through giving it permission to save to your fork.

## If something goes wrong

| What you see | What to do |
|---|---|
| "git: command not found" or "python3: not found" | Your Hermes app is too old. In hPanel, update or redeploy the Hermes Agent app, then repeat Step 1. |
| "Repository not found" | The address in the message is wrong. Copy it again from this page. |
| Hermes says it installed 0 skills | Paste the install message again in a **new chat**. |
| Anything else | Say "Run check my setup". It tests everything and tells you the exact fix. |
