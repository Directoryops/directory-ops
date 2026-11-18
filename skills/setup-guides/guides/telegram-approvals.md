# Approve changes from Telegram (optional)

**Status: coming later.** For now, approvals happen in your Hermes chat. This guide is a placeholder until it's tested on Hostinger.

**Why:** get "I found 3 fixes, approve?" on your phone and reply yes or no.

**What it will take (about 5 minutes):**
1. In Telegram, message **@BotFather**, send `/newbot`, pick a name. Copy the bot key it sends you.
2. Message **@userinfobot** to get your user number.
3. Add both as settings in Hostinger (Hermes gives you the names).
4. Click "Save & redeploy" (that restarts Hermes), then start a new chat.

**You'll know it worked when** your new bot says hello in Telegram.

---
## For Hermes
- Hermes Agent's Telegram gateway reads `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ALLOWED_USERS` (numeric IDs; all users denied by default). Upstream setup: `hermes gateway setup` → Telegram. Not verified on Hostinger Managed Hermes (no shell; the WebUI may expose this differently): don't offer this to owners until tested.

<sub>Note to Frey: verify on your Hermes before enabling. Sources: hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram, checked 2026-11-17.</sub>
