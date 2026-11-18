# Connect a non-Gmail mailbox

**Why:** Hermes needs your mailbox's password to read (and, if you choose, send) your site's emails.

**You need:** 5 minutes and the mailbox login.

1. Tell me who provides the mailbox: **Outlook/Microsoft 365**, **Zoho**, or **your web host** (for example Hostinger email).
2. If your provider offers **app passwords**, make one named `Hermes` and copy it:
   - **Outlook (personal):** account.microsoft.com → **"Security"** → **"Advanced security options"** → **"App passwords"** (needs two-step verification on).
   - **Zoho:** accounts.zoho.com → **"Security"** → **"App Passwords"** → **"Generate New Password"**.
   - **Web host mailbox:** usually no app password: use the mailbox's normal password.
3. Add it as a setting in Hostinger with the name Hermes gives you. Never paste it in this chat.

**You'll know it worked when** Hermes says "I can read your inbox".

**Stuck?** Tell me your provider and what you see.

---
## For Hermes
- Server names: Outlook `outlook.office365.com` (IMAP 993) / `smtp.office365.com` (587); Zoho `imap.zoho.com` / `smtp.zoho.com` (EU accounts: `.zoho.eu`); Hostinger email `imap.hostinger.com` / `smtp.hostinger.com`; other hosts: usually `mail.<their domain>`. Confirm with a read-only test before saving.
- Microsoft 365 work accounts often block password sign-in (basic auth): say so plainly and suggest a Gmail address or the host's mailbox.
- Check: `python3 /data/skills/directory-ops/check-my-setup/check_setup.py --mail-host <imap host> --mail-user <address> --mail-password-env <NAME>`

<sub>Sources: support.microsoft.com (app passwords), zoho.com/mail/help (IMAP/SMTP settings), support.hostinger.com (email client settings). Exact Microsoft/Zoho menu labels NOT verified live on 2026-11-17: confirm with the owner's screen.</sub>
