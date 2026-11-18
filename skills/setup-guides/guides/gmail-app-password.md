# Make a Gmail app password

**Why:** Hermes reads your site's inbox (and, if you choose, sends emails) with a special password just for it. Your real password stays private.

**You need:** 3 minutes, the Gmail account's login, and your phone for the security step.

1. Sign in to the Gmail account your site uses.
2. Turn on **2-Step Verification** if it isn't on yet: **myaccount.google.com** → **"Security"** → **"2-Step Verification"** → follow the steps.
3. Go to **myaccount.google.com/apppasswords** (or search "App passwords" in the search box at the top of your Google Account).
4. Type a name: `Hermes`, then click **"Create"**.
5. Copy the 16-letter password Google shows. Spaces don't matter. It's shown only once.
6. Add it as a setting in Hostinger with the name Hermes gives you. Never paste it in this chat.

**No "App passwords" option?** It's usually because 2-Step Verification isn't on, or it's a work (Google Workspace) account whose admin turned it off. Ask whoever manages that account to allow it, or use a regular Gmail address for the site.

**You'll know it worked when** Hermes says "I can read your inbox".

**Stuck?** Tell me what you see on the App passwords page.

---
## For Hermes
- Then `add-a-setting-in-hostinger.md` with name `<SLUG>_MAIL_PASSWORD`.
- Check (read only, last day): `python3 /data/skills/directory-ops/check-my-setup/check_setup.py --mail-host imap.gmail.com --mail-user <address> --mail-password-env <NAME>`
- "Invalid credentials": check the mailbox ADDRESS first (most common), then make a new app password. Changing the Google password revokes app passwords.

<sub>Source: support.google.com/mail/answer/185833 and support.google.com/accounts/answer/185839, checked 2026-11-17.</sub>
