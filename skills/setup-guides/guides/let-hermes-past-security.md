# Let Hermes past your site's security

**Why:** your site's security blocks simple scanners. For small checks Hermes reads pages with its web reader, but for checking every page (broken links, links between pages, page text), letting it in is faster and uses fewer AI credits. This lets in only requests that say "directory-ops"; everyone else is still checked as before.

**You need:** 2 minutes, a login to where your site is hosted (Vercel or Cloudflare).

**If your site is on Vercel:**
1. Go to **vercel.com**, log in and click your site's project.
2. Click **"Firewall"** in the left menu, then **"⋯"** at the top right, then **"Configure"**.
3. Click **"Add New…"**, then **"Rule"**. Name it: `Let directory-ops in`
4. Under **If**, choose **"User Agent"**, then **"Contains"**, and type: `directory-ops`
5. Under **Then**, choose **"Bypass"**.
6. Click **"Save Rule"**, then **"Review Changes"** at the top right, then **"Publish"**.

**If your site uses Cloudflare:**
1. Go to **dash.cloudflare.com**, log in and click your website.
2. Open **"Security"**, then **"Security rules"**, then **"Create rule"** → **"Custom rules"**. Name it: `Let directory-ops in`
3. Field **"User Agent"**, operator **"contains"**, value: `directory-ops`
4. Under **"Choose action"**, pick **"Skip"** and tick everything it offers (remaining custom rules, rate limiting, managed rules, Super Bot Fight Mode).
5. Save (**"Deploy"**).
6. If **Bot Fight Mode** is on (Security → **"Settings"**, filter **"Bot traffic"**), a rule can't get past it: turn it off, or tell me and we'll pick another way.

**You'll know it worked when** you tell me "done" and I say "I can read your site now."

**Good to know:** AI assistants like ChatGPT, Perplexity and Claude visit pages too when people ask about your topic. A strict challenge on every visitor can stop them from reading and recommending your site. If showing up in AI answers matters to you, ask me to check your bot settings once.

**Stuck?** Tell me what you see on your screen and I'll point to the right spot.

---
## For Hermes
- Check: `python3 /data/skills/directory-ops/check-my-setup/check_setup.py --skills-dir /data/skills/directory-ops --repo /data/workspace/directory-ops --website <site>`; the "can I read your site" check must be ✅. Or rerun `onboard-site/site_scan.py <site>` and confirm `blocked_by_security` is gone.
- Only offer this guide for jobs that read many pages (broken-links-and-seo-errors crawl, internal-links, page-copy-refresh checks, find_emails on the owner's own site). For onboarding and small checks, use your built-in web reader without asking.
- Vercel: the "Bot Protection" rule (Firewall → Rules → Bot Management) in Challenge mode, or a site-wide challenge ("Attack Challenge Mode", if switched on), challenges non-browsers; a Bypass custom rule runs before managed rulesets, so it lets the directory-ops user agent through both. If it still challenges, Attack Challenge Mode may need to be turned off temporarily (not verified in the docs; ask the owner what the Firewall page shows).
- Cloudflare: Bot Fight Mode can't be skipped by any rule (only IP Access rules or turning it off); Super Bot Fight Mode can be skipped.
- Other security (Sucuri, Wordfence, Akamai, host firewalls): ask the owner to allowlist the user agent containing `directory-ops`; their host's support can do it.

<sub>Checked 2026-11-17 against vercel.com/docs/vercel-firewall/vercel-waf/custom-rules, vercel.com/docs/vercel-firewall/vercel-waf/managed-rulesets, developers.cloudflare.com/waf/custom-rules/skip/, developers.cloudflare.com/bots/get-started/bot-fight-mode/. Not verified: Cloudflare's exact field/save labels in the new "Security rules" page ("User Agent", "contains", "Deploy"), and Vercel's "Attack Challenge Mode" toggle location.</sub>
