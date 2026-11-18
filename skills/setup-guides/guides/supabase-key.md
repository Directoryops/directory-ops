# Copy your Supabase key

**Why:** this key lets Hermes read your listings and, after you approve, update them.

**You need:** 2 minutes, your Supabase login.

1. Go to **supabase.com/dashboard** and click your directory's project.
2. Click **"Project Settings"** (the gear at the bottom left), then **"API Keys"**.
3. Find the **secret** key:
   - If you see a **"Secret keys"** section, copy the key that starts with `sb_secret_` (click the eye or **"Reveal"**, then the copy icon).
   - If you only see **"service_role"** (older projects), reveal and copy that one. It's a long key starting with `eyJ`.
4. Don't copy the "publishable" or "anon" key: Hermes can't save changes with it.
5. Now add it as a setting in Hostinger with the name Hermes gives you (I'll walk you through it).

**Important:** this key can change anything in your database. Never paste it in a chat, email or document. Hostinger's private settings are the only place it goes.

**You'll know it worked when** Hermes says "I can see your database" after the restart.

**Stuck?** Tell me what you see under "API Keys".

---
## For Hermes
- Then send `add-a-setting-in-hostinger.md` with name `<SLUG>_SUPABASE_KEY`.
- Check: `python3 /data/skills/directory-ops/directory-db/db.py tables --site-url <url> --key-env <NAME>` → a full table list means a secret key; a guessed list means an anon/publishable key: ask them to copy the secret one instead.

<sub>Source: supabase.com/docs/guides/getting-started/api-keys (Settings → API Keys; secret `sb_secret_…` replaces legacy `service_role`, legacy deprecated by end of 2026), checked 2026-11-17.</sub>
