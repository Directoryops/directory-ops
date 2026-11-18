---
name: setup-guides
description: "Click-by-click guides for the one-time setup steps other helpers need (adding a setting in Hostinger, Gmail app password, Supabase key, GitHub access key, photo storage, Search Console export, pasting a prompt into Claude Code, letting Hermes past a site's security). Use when another skill needs the owner to do a manual setup step, or the owner asks how to connect something."
---

# Setup guides

One place for every manual step an owner does outside Hermes. Other skills never write their own click steps; they point here, so every guide is tested once and worded the same way.

## How to use a guide

1. Open the guide file in `guides/` and send the owner the part above **For Hermes**, adapted with the real names (the setting name, their site). Keep the numbered steps exactly as written: the words in quotes are the real button labels.
2. Send one guide at a time. Never paste the "For Hermes" section to the owner.
3. When the owner says done, run the check in **For Hermes**. Report only yes or no (never print a key, password or token).
4. If the check fails, say what failed in one plain sentence and the single thing to fix. Never ask the owner to paste a secret in chat.
5. If the owner says "I don't see that button", ask them to describe what they see, then match it to the closest step. Labels change; the "You'll know it worked" line is the real goal.

## Guides

| Guide | When |
|---|---|
| `add-a-setting-in-hostinger.md` | Any key, password or token Hermes needs (every other guide ends here) |
| `supabase-key.md` | Listings are in Supabase |
| `supabase-project-link.md` | Hermes needs the Supabase project address |
| `github-access-key.md` | Listings are in a file in the site's code on GitHub |
| `gmail-app-password.md` | Reading or sending from a Gmail / Google Workspace mailbox |
| `other-mailbox-password.md` | Outlook, Zoho, or a mailbox from the web host |
| `supabase-photo-storage.md` | Adding photos to new listings |
| `search-console-export.md` | Better link and content picks from real Google data |
| `paste-into-claude-code.md` | A change needs the website's code (Hermes writes the prompt) |
| `let-hermes-past-security.md` | The site's security blocks automated visitors and a job needs to read many pages (small checks use your built-in web reader instead) |
| `telegram-approvals.md` | Optional: approve changes from the phone |

## Words to use with the owner

"hPanel" always comes with its meaning the first time: "hPanel (your Hostinger dashboard, where you set up Hermes)". Say "a setting" not "environment variable", "access key" not "token" (then "GitHub calls it a token"), "your site's code on GitHub" not "repository".
