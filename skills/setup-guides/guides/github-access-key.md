# Make a GitHub access key

**Why:** your listings live in your site's code on GitHub. This key lets Hermes suggest changes there. Every change arrives as a request you approve on GitHub, so nothing changes without you.

**You need:** 3 minutes, your GitHub login. (GitHub calls this key a "token".)

1. On **github.com**, click your profile picture (top right) → **"Settings"**.
2. Scroll down the left side → **"Developer settings"**.
3. Click **"Personal access tokens"** → **"Fine-grained tokens"** → **"Generate new token"**.
4. **Token name:** `Hermes`. **Expiration:** 1 year.
5. Under **"Repository access"**, choose **"Only select repositories"**, then pick the project your listings are in.
6. Under **"Permissions"** → **"Repository permissions"**, set **"Contents"** to **"Read and write"** and **"Pull requests"** to **"Read and write"**. Leave the rest.
7. Click **"Generate token"**, then copy it. GitHub shows it only once.
8. Add it as a setting in Hostinger with the name Hermes gives you. Never paste it in this chat.

**You'll know it worked when** Hermes finds your listings file and tells you how many listings are in it.

**Rather not?** Send me your listings file instead (drag it into this chat). I'll send back an updated file for you, or Claude Code, to put into your project.

**Stuck?** Tell me which screen you're on.

---
## For Hermes
- Then send `add-a-setting-in-hostinger.md` with name `<SLUG>_GITHUB_TOKEN`.
- Check: `python3 /data/skills/directory-ops/directory-db/db.py tables --backend repo --repo <owner/name> --token-env <NAME>` → lists data files. 401 = key wrong or expired; 404 = wrong project picked in step 5; 403 = a permission in step 6 is missing (the error names it).
- File path instead: save the upload under `notes/<slug>/listings/` and use `--backend repo --local-dir` for reading; return edits as a file.

<sub>Source: docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens, checked 2026-11-17.</sub>
