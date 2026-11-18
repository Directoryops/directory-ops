# Add a setting in Hostinger

**Why:** Hermes needs this key to connect, and it's kept in a private setting so it's never shown in chat.

**You need:** 2 minutes, your Hostinger login.

1. Go to **hpanel.hostinger.com** and log in. hPanel is your Hostinger dashboard, where you set up Hermes.
2. Open your **Hermes** app (it's in your list of apps).
3. In its menu, click **"Environments"**.
4. Click **"Add environment variable"**.
5. In **Key**, type exactly: `<NAME HERMES GIVES YOU>`
6. In **Value**, paste what you copied. Nothing else, no spaces or quotes.
7. Click **"Save & redeploy"**, then confirm. Hermes restarts (about a minute).
8. Open a **new chat** with Hermes and say **"continue"**. The old chat can't see new settings.

**Changing a setting you already have** (for example swapping a key): same steps 1 to 3, then click the **edit (pencil) icon** next to the setting's name, replace the value with the new one, and click **"Save & redeploy"**. Then a new chat and "continue".

**You'll know it worked when** your new name shows in the Environments list and Hermes says "I can see it" in the new chat.

**Stuck?** Tell me what you see on your screen and I'll point to the right spot.

---
## For Hermes
- Check (names only, never values): `python3 /data/skills/directory-ops/check-my-setup/check_setup.py --env <NAME>`
- Not visible after restart: confirm they started a NEW chat; if still missing, add the name to `terminal.env_passthrough` in /data/config.yaml and ask for one more restart.
- Values are trimmed of spaces, line breaks and quotes by the scripts, so a messy paste is fine.

<sub>Source: hostinger.com/support/how-to-manage-environment-variables-in-managed-hermes ("Environments", "Add environment variable", "Save & redeploy"), checked 2026-11-17.</sub>
