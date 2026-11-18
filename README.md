# directory-ops: an AI employee for your directory website

directory-ops is a set of ready-made skills for **Hermes Agent** (an AI assistant you rent on Hostinger).
Once installed, Hermes keeps your listings accurate, finds what to add to your pages, brings traffic, and turns leads into money.
You chat with it in plain English. It asks before it changes anything.

> Final public GitHub address: TBD. Links below use `Directoryops/directory-ops` as a placeholder.

## Who it's for

People who run a directory (car washes, dentists, venues, anything with listings) or are building one, and want the boring work done without hiring anyone. No coding needed.

## What it can do

Hermes recommends the right ones for where you are. You can also just ask for any of them.

**Start: make your directory worth visiting**
- **Listing research:** reads real Reddit conversations to learn what people want to know before choosing a business, then fills those details in from each business's own website, with proof.
- **Tool ideas:** finds simple calculators and tools people search for in your niche (like a cost estimator), so you can build pages that bring traffic.
- **Article ideas:** finds the few articles actually worth writing, backed by evidence, and writes them with your own data.

**Grow: keep it accurate and get found**
- **Listing check:** re-checks your listings every week (open or closed, hours, phone, website) and fixes what changed.
- **Broken links and SEO errors:** finds broken links, dead old pages, and pages competing for the same search, and gives you the exact fix.
- **Internal links:** finds the exact sentences where links to your most important pages should go.
- **Page copy refresh:** rewrites the intro text on your city or category pages every few months, using real facts from your listings.
- **Keep pages up to date:** re-checks pages with changing facts (fees, prices, policies) against official sources.

**Earn: turn traffic into money**
- **Lead routing:** sends quote requests from your site to the right business (first one free), with follow ups.
- **Inbox helper:** reads your site's inbox, ignores spam, and handles "add my business" and "this place closed" emails.

**Helpers:** "check my setup" tests that everything is connected; "review changes" shows what's waiting for your OK.

## Quick start (3 steps)

1. **Get Hermes on Hostinger:** [Hostinger Hermes Agent link TBD]. Choose the **Hermes Agent WebUI** app.
2. **Install the skills:** open Hermes chat and paste the install message from [INSTALL.md](INSTALL.md). It takes about 2 minutes.
3. **Start a new chat and say: "Onboard a site".** Hermes asks where you are, what you want help with, looks at your site, and suggests 2 or 3 things to start with. It shows you a sample before anything runs.

## What it costs to run

- **Hermes on Hostinger:** your monthly plan.
- **AI credits:** most runs cost a few cents of AI credits. A weekly listing check on a small directory, or one article, is roughly 5 to 10 cents. Hermes tells you after the first runs.
- **Data:** free sources by default (Google search and Maps pages, Reddit's public archive, your own site).
- **Optional:** if you already pay for Ahrefs, Semrush or DataForSEO, some skills can use them. Never required.

## Safety

- **Nothing changes on your site or database without your approval.** The first run of every job only shows proposals. You say "approve 1 and 3" (or "approve all").
- **Your keys never go in the chat.** You add them in Hostinger's settings (hPanel → your Hermes app → Environments). Hermes only checks that they're there.
- **Nothing gets deleted.** Closed businesses get marked closed, never removed.
- **Every change is logged** with the old value, so anything can be undone.
- **Scheduled jobs** run on their own (for example every Monday) and send you a short summary.

## What's supported

| Your setup | What works |
|---|---|
| Listings in **Supabase** (a popular online database) | Everything |
| Listings in **your site's code on GitHub** (data files) | Everything; changes arrive as a "pull request" you click to accept |
| **WordPress**, Google Sheets, Airtable | Website jobs (SEO, links, articles, tools, research) work now; listing edits are coming |
| No website yet | Listing research, tool ideas and article ideas, to plan it right |

## FAQ

**Do I need to know how to code?** No. You chat with Hermes. When a change needs your website's code, Hermes writes a ready-to-paste instruction for Claude Code or your developer.

**Will it break my site?** It can't change anything until you approve it, and every change can be undone.

**How long does setup take?** Install is about 2 minutes. Onboarding a site is about 10 to 15 minutes of chatting.

**Can I use it for more than one site?** Yes. Say "Onboard a site" again for each one.

**What if I don't know what I want help with?** Say "not sure". Hermes walks you through each skill in one sentence and recommends based on where you are.

**Does it email businesses on its own?** Only if you turn that on. By default it writes drafts for you to approve.

**What's an "environment variable"?** A private setting in Hostinger where secret keys live, so they never appear in the chat. Hermes tells you exactly which one to add and where to click.

**Can I stop or change a job?** Yes, just tell Hermes: "pause the listing check", "run it every two weeks", "ask me before every change".

## Troubleshooting

| What you see | Fix |
|---|---|
| Hermes says it can't see your key | After adding a key, click **Save & redeploy** (that restarts Hermes), then start a **new chat** and say "continue". Old chats don't see new keys. |
| "401" or "key is wrong" | The key was copied wrong. Copy it again from the original site (Supabase, Gmail…), edit the value in hPanel, click Save & redeploy, new chat. |
| "I can't edit your website" | Hermes can't change your site's code itself. It gives you a prompt to paste into Claude Code (or send to your developer). |
| A job didn't run on schedule | Say "Run check my setup". It lists your scheduled jobs and their last run. |
| Results look wrong | Reply with what's wrong in plain words. Hermes saves it as a rule for next time. Nothing was changed without your OK. |

## License

MIT. Use it, change it, share it.
