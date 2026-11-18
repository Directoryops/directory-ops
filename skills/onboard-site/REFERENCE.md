# Onboard a site: reference

Details moved out of SKILL.md word for word. SKILL.md says which section to read and when.

## O1. How to talk (full)

- **One question per message.** Wait for the answer before the next one.
- **Plain words.** Never say these to the owner: slug, env var, environment variable, schema, table, column, API, config, YAML, cron, SQL, endpoint. You handle all of that silently. Say "your list of businesses", "your listings", "a setting", "a secret key".
- **Every question has a default** they can accept ("reply 1, 2, 3 or 'not sure'").
- **Short, friendly, confident.** No walls of text, never several questions at once. Playbook cards and the game plan are the only longer messages.
- **When the owner must click something themselves**, give exact clicks: which site, which button, what to type, what they'll see when it worked (use the setup guides).
- **Never stop on a technical problem you can solve yourself.** A site that isn't live, a test domain, a blocked page: note it, use the fallback, keep going.
- **Explain any outside name the first time it appears** in the same message: AI credits = "AI credits (the small usage fee for the AI that runs your helpers, from your Hostinger plan; a few cents a run)"; hPanel = "hPanel (your Hostinger dashboard, where you set up Hermes): hpanel.hostinger.com"; GitHub access key = "a GitHub access key (GitHub calls it a token)". Never name a product the owner didn't name (Supabase, GitHub, Reddit, Google Autocomplete…) unless you explain it in the same sentence.
- **Question budget:** at most 3 questions to understand them (Step 1), 1 for the plan, and at most 4 per helper (its playbook OK, teach me your way, sample OK, schedule OK), plus anything a connection needs.

## O2. The scan, and a blocked site (full)

Live site: about 1 to 2 minutes, free:
```
python3 /data/skills/directory-ops/onboard-site/site_scan.py https://<their site> --out $DIROPS_REPO/notes/<site>/scan.json
```
**If the scan says `blocked_by_security: true`** (`next_step: use_web_reader`): the site's security (Vercel, Cloudflare and similar) turns away simple scanners. It is NOT a rate limit or an outage; never call it that. Don't ask the owner anything here:
1. Say only `say_to_owner`: "Your site's security blocks simple scanners, so I used my web reader instead."
2. Read the pages in `web_reader_plan` with your built-in web reading tool (homepage, robots.txt, sitemap, then about 5 sample pages, one per page type).
3. Write the 3 to 5 "Here's what I found" bullets yourself from what you read (pages in the sitemap, what listing pages look like and roughly how long they are, forms, blog, ads). Skip what you couldn't see; never guess.
4. Remember `blocked_by` for the plan. If a recommended helper reads many pages (broken links, internal links, page copy checks, finding emails on the owner's own site), add one line to the plan: "One 2 minute step first: letting me past your site's security, so I can check every page cheaply." The click steps are `setup-guides/guides/let-hermes-past-security.md`; offer them during that helper's setup (Step 4), one yes/no: "Want to do that now, or start with a small sample today?"

If their list of businesses is easy to reach already (a file they sent, or a Supabase project you can already read), also run "Check the list" (below) now for numbers; otherwise it happens when the first listing helper connects.

## O3. Step 1 questions (full wording)

## Step 1: Understand them (3 questions at most)

If their first message already answers one, don't ask it again: confirm it in your next message.

**1a. Where are they at?**
> Hi! I'm going to set you up with an AI employee for your directory. I'll do the technical parts.
>
> First: where are you at with your directory?
> 1. Just an idea / still planning
> 2. Building it now
> 3. It's live
> 4. It's live and making money

Save `stage` (idea | building | live | earning).

**1b. What do they want most?**
> What do you want most right now?
> 1. More traffic
> 2. Accurate listings (hours, phones, closed businesses)
> 3. Leads and money from businesses
> 4. Richer listing pages (more useful than Google)
> 5. Not sure, suggest something

Save `goal` (traffic | accurate_listings | leads | richer_pages | not_sure). Infer the money model from it (traffic → ads, leads → leads) and state it in the plan; they can correct it there. Only ask "How does it make money?" if it changes the plan and you can't tell.

**1c. Their website.**
> What's your website address? (If it isn't live yet, just say "not live yet".)

Pick a short lowercase name for the site yourself (e.g. `scw` for sunrisecarwashes.com); never mention it. Not live: "No problem, I'll skip the website parts for now." Save `website` (or `none`).

## O3b. Step 4 per-helper steps (full wording)

Tell them where they are: "Helper 2 of 4: Connect your pages." For each chosen helper, in order:

1. **Show its Playbook card** (the `## Playbook card` section in that helper's SKILL.md) in plain words, about 8 lines: what it does, why it works, how I work, what you approve, how often, what you get, what I need. Then ask: **"Anything you'd change about how I do this? (or 'looks good')"** Changes become rules for that helper (save them like "Teach me your way" rules).
2. **"Teach me your way"**: ask the helper's own question (in its SKILL.md), **made specific with what you found on their site**, never generic. Not "Any rules for checking listings?" but "Most of your 1,256 centers belong to 3 chains. Should each chain's own location page be the final word on hours?" Name their real numbers, chains, page types or gaps, and offer your best guess as the default. They can ramble, send a voice note, or skip. Show the rules back once and save them under `## <Helper name> rules` in `notes/<site>.md`.
3. **Connect only what it needs** (its card's "What I need"; see "Connecting" below). Nothing needed: skip silently.
4. **Settings, silently:** run the helper's Step 0 in quick mode: ask only its `[essential]` questions you can't answer (one per message), fill everything else with defaults or what you know, and write it all into that helper's section of `sites/<site>.yaml` with `settings_done: true`. Skip a question the owner's answers already cover.
5. **Its Onboarding sample:** run exactly what its Playbook card's "Onboarding sample" says, on their real site or data. Show it, then ask **"Good? (yes / change …)"**. Long ones (tool ideas, Reddit research) run in the background: say "I'll message you here when it's ready (about N minutes)" and continue with the next helper's card meanwhile; come back to show it.
6. **Its rhythm:** one question: "I'll run this every Monday at 9 AM your time. OK?" (one-time helpers: "Want me to repeat this every few months?"). Then schedule it (rules in Step 5).

**When a sample fails** (blocked site, noisy results, thin data, a missing key): use the helper's documented fallback (web reader for blocked sites, its plan B for thin data, a smaller or narrower run). Still failing: tell the owner in plain words what happened and exactly how to fix it, mark it blocked in the tracker (reason + fix + told), give it a "starts when …" rhythm, and **move on to the next helper. Never wrap up early.**

## O3c. The step tracker (full)

```
python3 /data/skills/directory-ops/onboard-site/onboard_next.py --slug <site>
```

It prints the exact next step. Record each answer with `--set` (see its help). **Never end onboarding unless it prints DONE.** It refuses until every chosen helper has delivered its sample, or is marked blocked with the reason AND the fix told to the owner. If a helper fails, that is never a reason to wrap up: fix it, use its fallback, or explain it and move to the next helper.

## O4. The decisions follow-up after a sample (full)

**Samples hold only proposed changes** and end with "Good?". Anything needing the owner's decision (an address conflict, a listing that looks like test data) goes in ONE follow-up after their answer:
> A few things need your call:
> 1. Mister Car Wash: your address says 2702, their own page says 2720. Which is right?
> 2. Sparkle Bay Car Wash: I can't find it anywhere and the phone looks made up.
>
> Reply with the numbers you want me to fix, or "later".

Nothing is written to their site or database during onboarding: changes become proposals in `notes/<site>/pending.md`; approved ones go through review-changes ("approve 1 and 2"). **Never say a change was made unless the database confirmed it.** When they reject or correct something, ask once whether to remember it as a rule.

## C1. Connecting the list of businesses (full)

If a helper needs their list of businesses and it isn't connected yet:

> Where is your list of businesses stored?
> 1. Supabase
> 2. In your site's code on GitHub
> 3. WordPress
> 4. A spreadsheet (Google Sheets, Airtable, Excel)
> 5. Not sure

- **Not sure:** use the scan. If it found Supabase or WordPress: "It looks like your site uses Supabase. Does that sound right?" Otherwise: "No problem. Who built the site? If you built it with an AI tool, it's most likely Supabase or files in your code." Then ask again.
- **Supabase:** follow "Connecting Supabase" below. The owner pastes one link and, at most, adds one secret key.
- **GitHub (in the code):** offer the two ways in ONE message, easiest first:
  > Your listings are in your site's code on GitHub. Two ways I can work with them:
  > 1. **Quickest:** send me a copy of the file. With a copy I can do a one-time check and send fixes back as a file. No setup. (The file is usually named "listings" or "businesses", often in a "data" folder. In GitHub, open it, click the "Download raw file" button, then attach it here. If you're not sure which file it is, Claude Code can tell you.)
  > 2. **Hands-off:** for automatic weekly checks, the access key is better. You make it once (about 3 minutes, I'll walk you through it), and every week I send my fixes as a change you approve on GitHub with one click.
  >
  > Which do you prefer? (default: 1)
  **1:** save the file under `notes/<site>/listings/`, then read it with `db.py --backend repo --local-dir notes/<site>/listings --table <file>` (read only), then do "Check the list" below. Fixes go to `pending.md` as usual; after approval, write the updated file into `notes/<site>/listings/out/` and tell the owner "Here's your updated listings file: put it back in your project in place of the old one (or ask Claude Code to)." **With a copy there is no weekly schedule** (a copy goes stale). Instead ask one yes/no: "Want me to remind you once a month to send a fresh copy?" and save `listings_copy_reminder: monthly` if yes. **2:** walk them through `/data/skills/directory-ops/setup-guides/guides/github-access-key.md`, then `/data/skills/directory-ops/setup-guides/guides/add-a-setting-in-hostinger.md` (setting name `<SITE>_GITHUB_TOKEN`), then find the file yourself with `db.py tables --backend repo` (if several could fit, ask which one in plain words), then do "Check the list" below. Never show the owner file paths like `data/listings.json` unless they ask.
- **WordPress or a spreadsheet:** "Automatic weekly checks need your list in an online database. With a spreadsheet (or WordPress), I'll send fixes as a list you paste in, and everything else still works." Adjust the plan (no weekly listing schedule) and continue. To read a spreadsheet: "Please send me a copy: in Google Sheets click **File → Download → Comma-separated values (.csv)**, then attach the file here." Save it under `notes/<site>/listings/` and read it with `db.py --backend repo --local-dir notes/<site>/listings --table <file>` (read only).

## C2. Connecting Supabase (full)

1. Ask: "Please paste your Supabase project link. It isn't secret. Open supabase.com, click your project, then click the web address at the very top of your browser window, copy it (Cmd+C on Mac, Ctrl+C on Windows) and paste it here."
   **Turn it into the project address silently:** a dashboard link `https://supabase.com/dashboard/project/<ref>` (anything after `<ref>` doesn't matter) becomes `https://<ref>.supabase.co`. A link that's already `https://<ref>.supabase.co` is used as is. Never ask the owner for "the API URL".
2. **Find the secret key yourself.** List only the NAMES your terminal can see, never values: `env | cut -d= -f1 | grep -i -E "supabase|_key"`. One name clearly for this site: use it. None: walk them through "Adding the secret key" with the exact name `<SITE>_SUPABASE_KEY`. Several: "I see two keys, A and B. Which one is for this site?"
3. **Find their list of businesses yourself:**
   ```
   python3 /data/skills/directory-ops/directory-db/db.py tables --site-url <url> --key-env <NAME> --guess "<the niche in 1 to 3 words>"
   ```
   If several could fit, ask "Is **car_washes** your list of businesses?" (yes/no). Only if nothing fits: "Open Supabase → **Table Editor** and tell me the names you see on the left." Then do "Check the list" below.
4. Test read only: `db.py count --site-url <url> --key-env <NAME> --table <name>`. An error says in plain words what's wrong; fix that one thing.

**Adding the secret key:** walk the owner through `/data/skills/directory-ops/setup-guides/guides/supabase-key.md`, then `/data/skills/directory-ops/setup-guides/guides/add-a-setting-in-hostinger.md` with the setting name `<SITE>_SUPABASE_KEY`. (The project link itself: `/data/skills/directory-ops/setup-guides/guides/supabase-project-link.md`.)

If a key gets pasted into the chat: "Please delete that key in Supabase and make a new one, since it's now in our chat history." If the variable exists but you can't see it, add the name to `terminal.env_passthrough` in your Hermes settings, ask them to click "Save & redeploy" once more, and check again.

## C3. Check the list (full)

Silently: `db.py select --limit 3` (the real field names), then save all rows (`db.py select --all ... > notes/<site>/tmp/rows.json`, or use the file they sent) and run:
```
python3 /data/skills/directory-ops/onboard-site/listing_quality.py <rows.json or their file>
```
Then ONE question that confirms the count, with one useful finding from `plain_summary`:
> I found 44 car washes in your list. 23 are missing a phone number. Is that all of your car washes?

If the owner earlier said a different number ("about 60"), say it: "I found 6 groomers in your file, and you mentioned about 60. Is the file complete?" A wrong count = wrong file or an old copy: sort that out before any sample.

**Test data:** if `placeholder.likely` is true, say it plainly and hold every helper that needs real listings: "Your list looks like test data (the phone numbers and websites are made up), so checking it wouldn't help yet. I'll start Keep listings accurate once your real listings are in; just tell me when." Never sample or schedule those helpers on test data. Helpers that don't need the list (tool ideas, Reddit research on the niche) still go ahead. If only a few rows look like test data, list them later in the decisions follow-up (the follow-up after the sample), not here.

**Read-only key (Supabase):** run `python3 /data/skills/directory-ops/check-my-setup/check_setup.py --site-url <url> --key-env <NAME> --tables <list>` and read its `key_can_write` check. If the key can only read, say its `owner_message` ("This key can only read your list, so I can't save approved fixes yet. Want to swap it for the full key? (2 minutes)") before promising any fixes; yes → `/data/skills/directory-ops/setup-guides/guides/supabase-key.md` (they're replacing an existing setting, so use the guide's "Change a setting" part). When they say "done", run the check again: only continue as "can save" if `key_can_write` now passes; otherwise say plainly it's still the read-only key and what to try. Samples can still run (they're previews). **Never say a change was made unless the database confirmed it**: with a read-only key say "Approved: saved in your approval list, and I'll apply it as soon as the full key is in."


A mailbox (inbox-triage, lead-routing): `/data/skills/directory-ops/setup-guides/guides/gmail-app-password.md` or `other-mailbox-password.md`, then `add-a-setting-in-hostinger.md`. Photos: `supabase-photo-storage.md`. Search Console: `search-console-export.md`. A site that blocks page reading, for helpers that read many pages: `let-hermes-past-security.md` (offer it once; meanwhile run a small sample with your web reader).

## O5. Scheduling rules (full)

Scheduling rules (for each helper's rhythm in Step 4):
1. Work out their time zone from the city or area you already know (Austin → Central time). Ask "Which time zone are you in?" only if you don't know their city or state.
2. Tell the owner only local time, e.g. "I'll run it Mondays at 9 AM Central time." Never show UTC. Then create the schedule with your scheduler (in Hermes: its cron jobs) in UTC yourself (9 AM Central = 15:00 UTC in winter, 14:00 in summer; pick the current offset and note that daylight saving shifts it by an hour twice a year).
3. Set `enabled: true` for that helper in `jobs:` with the day, the UTC time and the job id (silently).

## O6. Adding a helper later (full)

When the owner says "add the <X> helper", "can you also do <Y>?" or "what else can you do?":
1. **"What else can you do?"**: list the helpers that serve their goal (Step 3 table) with one sentence each, mark which are running, and recommend ONE next helper with a why from their site. "Want me to add it?"
2. **"Can you also do <Y>?"**: name the helper that does it, or honestly: "Not yet. The closest is <helper>, which <one sentence>."
3. Then run that helper through Step 4 (card, teach me your way, connect, settings, sample, rhythm), using the tracker with `--set chosen` extended by the new helper.

## O7. Behind the scenes (full)

1. Write `sites/<site>.yaml` fresh (`sites/example.yaml` is a reference for names only; never copy it whole): `slug`, `name`, `url`, `stage_of_journey`, `stage` (new for idea/building, growing for live/earning, lost_rankings if they mention a drop), `money`, `database` (url, key_env and the real names you saw), `never_touch`, `approvals`, one section per chosen helper with its settings, and `jobs:` with only the chosen helpers (`enabled: false` until their rhythm is agreed). Every field name comes from what you actually saw; leave out anything that doesn't exist.
2. Run check-my-setup once; it must pass before any scheduled run. Fix what it reports.
3. `notes/<site>.md`: the owner's answers and rules in plain bullets, plus the scan summary and a link to `notes/<site>/game-plan.md`; "later" helpers under "Roadmap".
4. Approvals live in `notes/<site>/pending.md`; the owner approves with review-changes. Nothing to create.
5. Commit and push `sites/` and `notes/`. If the folder isn't linked to GitHub, skip it and add this one line to the wrap-up: "Your settings aren't backed up to GitHub yet (optional). Just say 'back up my settings' anytime."
