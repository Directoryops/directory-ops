# Make a photo folder in Supabase

**Why:** so new listings can have photos. Hermes saves them in a folder anyone can view (that's what "public" means: the photos show on your site; nothing else in your database becomes public).

**You need:** 1 minute, your Supabase login.

1. Go to **supabase.com/dashboard** and click your directory's project.
2. Click **"Storage"** in the left menu.
3. Click **"New bucket"** (a bucket is just a folder).
4. **Name:** `listing-photos`.
5. Turn on **"Public bucket"**.
6. Click **"Create bucket"** (or **"Save"**).

**You'll know it worked when** `listing-photos` shows in your Storage list with a "Public" label.

**Stuck?** Tell me what you see after clicking Storage.

---
## For Hermes
- Check: `python3 /data/skills/directory-ops/check-my-setup/check_setup.py --site-url <url> --key-env <NAME> --bucket listing-photos`
- Also make sure the website is allowed to show images from `<ref>.supabase.co` (most Next.js sites need it in their image settings; if photos don't show, send a `paste-into-claude-code.md` prompt).

<sub>Source: supabase.com/docs/guides/storage/buckets/creating-buckets ("New Bucket", "Create Bucket"; default private). The "Public bucket" toggle label is from the dashboard, not the doc text: confirm on screen. Checked 2026-11-17.</sub>
