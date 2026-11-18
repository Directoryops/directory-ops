# Send your Supabase project link

**Why:** so Hermes knows which database is yours. The link isn't secret.

**You need:** 30 seconds.

1. Go to **supabase.com/dashboard** and click your directory's project.
2. Click the web address at the very top of your browser window.
3. Copy it (**Cmd+C** on Mac, **Ctrl+C** on Windows).
4. Paste it here in the chat.

It looks like `https://supabase.com/dashboard/project/abcdefgh...`. That's the right one.

**You'll know it worked when** Hermes repeats your project's short name back to you.

**Stuck?** Tell me what the address at the top of your browser starts with.

---
## For Hermes
- Convert silently: `https://supabase.com/dashboard/project/<ref>[/anything]` → `https://<ref>.supabase.co`. A link already ending in `.supabase.co` is used as is.
- Save it as `database.url`. Never ask the owner for "the API URL".

<sub>Source: Supabase dashboard URL format, checked 2026-11-17.</sub>
