# Tool Page Finder: reference

Details moved out of SKILL.md word for word. SKILL.md says which section to read and when.

## R0. Step 0 inputs (full)

**Quick mode (during onboarding):** don't ask these. The website is known; write the visitor sentence yourself from what the owner said ("Visitors look for a <business> near them, then <next step>"); skip the SEO-tool question (say once: "I'll use free Google data. If you ever have an Ahrefs, Semrush or Search Console export, send it and I'll redo the ranking.").
1. Ask the user these questions if they have not already answered, one per message (skip any the site setup already answers; skip the SEO-tool question when the site isn't live):
   - "What is your website URL?"
   - "In one sentence, what do your visitors do on your site, and what do they do right after?" (Site not launched yet: ask instead "What do people choosing a <business type> try to figure out first?", or in quick mode write this sentence yourself from what onboarding knows.)
   - "Do you use an SEO tool like Ahrefs or Semrush, or Google Search Console? If yes, you can send me a keyword download from it for better picks. If not, that's fine: I'll use free Google data."
2. Run:
   ```
   mkdir -p ~/tool-page-finder-runs/<site> && cd ~/tool-page-finder-runs/<site>
   ```
   `<site>` is the domain, e.g. `example.com`. Run every later command from this folder.
3. If the user sent CSV files, copy them into this folder unchanged. Do not rename them to suggestions.csv, candidates.csv, serp.csv, scored.csv or trends.csv.

**Done when:** you are in the folder and have the URL and the one-sentence answer.


## R0b. Teach me your way (full)

This is what makes the helper yours instead of generic. Ask once (in quick mode it replaces settings questions, it doesn't add many):

> Tell me what people choosing a <business type> try to figure out before they choose, and any kind of tool you'd love (or never want) to build. Ramble or send a voice note; it makes me much better. (Or say "skip".)
> For example:
> - Roofing: "People always ask what a new roof costs per square foot."
> - Car wash: "Tools for drivers only, never for car wash owners."
> - Wedding venue: "A guest count to budget calculator would be perfect."

Turn the owner's OWN answer (never invent rules when they said skip) into 3 to 7 short numbered rules in plain words, show them back ("Got it, I'll: 1) … 2) … Anything to change?"; in quick mode end with "Say 'change …' anytime." instead of a question, so onboarding stays short), and save them in `notes/<slug>.md` under `## Tool ideas rules` (create the section if it's missing). **Every run reads that section first and follows it; this skill's own safety rules still win** (a rule can't make it skip approval, delete things, or use competitors as sources).

**Learn from corrections:** when the owner rejects or edits one of your proposals, or says "no, because …", ask once: "Want me to remember that as a rule for next time? (yes/no)". Yes: add it to `## Tool ideas rules` in plain words with today's date.


## R1. Step 1 seeds (full rules and example)

A seed is a short search phrase of 1–3 words. Write **8 to 12 seeds** into `seeds.txt`, one per line, in this format:
```
bucket: seed
```
Use exactly these three buckets:

| Bucket | What it is | How many |
|---|---|---|
| core | the site's main topic | 2–3 |
| entity | brands, platforms, companies or products the visitors use | 3–5 |
| next | the job visitors do right after using the site (from the step 0 answer) | 2–3 |

Example for an aquarium store directory:
```
core: aquarium
core: fish tank
entity: fluval
entity: api
entity: seachem
next: aquascaping
next: cycling a tank
```
Rules:
- Use lowercase.
- Each seed is 1–3 words.
- Do not use a single word with several meanings. Example: "tank" pulls in gas tanks and army tanks, so write "fish tank" instead.
- Do not put tool words in seeds (calculator, cost, fees, price). The script adds those itself.

**Done when:** `python3 ${HERMES_SKILL_DIR}/scripts/next.py` no longer says seeds.txt is invalid.


## R2. Step 2 and 3 problems

```
python3 ${HERMES_SKILL_DIR}/scripts/suggest.py --seeds-file seeds.txt --out suggestions.csv
```
This takes about 1 minute per seed. Wait for it to finish.

**Done when:** the last line starts with `DONE:` and shows at least 500 suggestions.
- If there are under 500: add 3 more entity seeds to seeds.txt, delete suggestions.csv, and run step 2 again.
- If it prints `ERROR: more than half the requests failed`: stop and tell the user: "This server can't reach Google Autocomplete (suggestqueries.google.com). Please check the internet connection or firewall."

### Step 3. Turn keywords into tool ideas
If there are **no** extra CSV files in the folder:
```
python3 ${HERMES_SKILL_DIR}/scripts/classify.py suggestions.csv --seeds-file seeds.txt --out candidates.csv
```
If the user gave CSV files, list them after suggestions.csv:
```
python3 ${HERMES_SKILL_DIR}/scripts/classify.py suggestions.csv ahrefs_export.csv --seeds-file seeds.txt --out candidates.csv
```
The output says `FREE MODE` or `DATA MODE`. Write down which one.

**Done when:** the output has a line starting with `DONE:` and shows at least 10 tool ideas.
- If it prints `WARNING: fewer than 10 candidates`: add 3 more entity seeds, then redo steps 2 and 3.
- If it prints `ERROR: ... has no keyword column`: that file is not a keyword export. Remove it from the command and run again.


## R4. Step 4 yes/no check (full)

**Quick mode:** answer every line yourself using the owner's visitor sentence (would THAT visitor use this tool?), and list your yes/no choices in the sample so the owner can change them.
**Before Step 5 (every mode), also check the top 10 ideas in candidates.csv yourself**, even the ones not in review.txt, and add a line `C<nn> no | <tool type> | main keyword: <its main keyword exactly as in candidates.csv> | <reason>` to review.txt for any that fail:
- **For the business, not the visitor** ("cost to build a car wash", "how to start a groomer business", software for owners) → no.
- **One competitor's own product** ("<brand> membership cost") → no, unless that brand IS the platform the visitors use (like a marketplace's fee calculator for its sellers) → yes.
- **Pure shopping or a store's hours/locations** → no (those are listing pages, not tools).
Open `review.txt`. Each line looks like this:
```
C07 ?? | cost estimator | main keyword: how much to donate plasma | unusual words: plasma
```
For every line, ask one question: **"Would a visitor of this website use this tool?"**
- Yes → replace `??` with `yes`.
- No → replace `??` with `no`.
- Not sure → write `no`.

Change nothing else on the line. Save the file. If review.txt has no lines starting with C, skip this step.

**Done when:** no line starting with `C` still has `??` (the header lines can mention ?? — ignore them).


## R6. Step 6 who ranks (full)

`serp.csv` has 10 keywords. Each keyword has 5 rows with empty `url` and `dr` cells. For each keyword:
1. Use your web search tool on the keyword exactly as written.
2. Take the first 5 normal web results, in order. Skip ads, videos and "People also ask".
3. Paste each result's full URL, starting with `https://`, into the `url` cell of the matching rank row.
4. Leave `dr` empty, unless the user has Ahrefs, Moz or Semrush. In that case, put each result's Domain Rating or Domain Authority (a number from 0 to 100) in `dr`.

Rules:
- Copy URLs exactly as they appear in the results. Never type a URL from memory.
- If there are fewer than 5 results, leave the remaining url cells empty.
- Do not change the `keyword` or `rank` columns.

**Done when:** every keyword has at least 3 URLs. Step 7 checks this and tells you if any are missing or broken.


## R6b. Google Trends (optional)

1. Create `trends.csv` with the header `keyword,trend`.
2. For each keyword in serp.csv, open Google Trends, set **United States** and **Past 5 years**, and look at the line.
3. Compare the last 12 months with the first 12 months:
   - clearly higher (more than about 20%) → `up`
   - clearly lower (more than about 20%) → `down`
   - otherwise, or if there isn't enough data → `flat`

Trends only adds or removes a few points. It never decides alone. Skip this step if you can't open Google Trends.


## R7. How the score works

```
python3 ${HERMES_SKILL_DIR}/scripts/score.py candidates.csv --decisions review.txt --serp serp.csv --out scored.csv
```
If you made trends.csv in step 6b, add `--trends trends.csv` before `--out`.

The script scores every idea out of 100 using fixed rules. **You do not score anything.**

| Part | Points | What earns them |
|---|---|---|
| Demand | 0–30 | Rank among all ideas. Uses volume in DATA MODE; autocomplete frequency in FREE MODE |
| Small sites ranking | 0–25 | Top-5 results from small sites. Uses DR ≤ 40 if you filled `dr`; otherwise "not a big brand" |
| Tool proof | 0–15 | Top-5 results that are already tool pages, proving searchers want a tool |
| Forums ranking | 0–5 | Reddit or forums in the top 5, meaning people can't find a good answer |
| Shopping search | −15 | 3 or more of the top 5 are store, category or home pages, so people want to buy, not use a tool |
| Fit | 0–15 | Core seed 15, next 12, entity 10 |
| Fresh data | 0–5 | Data that changes (fees, prices, schedules) is a moat |
| Easy build | 0–5 | Simple formulas score highest |
| Trend | −10 to +5 | Only if trends.csv was given |

It also merges ideas that share 2 or more top-5 URLs, because those are the same search intent. Each idea gets a **confidence** label:
- **HIGH:** real volume plus DR for every result.
- **MEDIUM:** real volume, or 5 results.
- **LOW:** anything less.

**Done when:** it prints `DONE: scored ...`. If it prints `ERROR: serp.csv has problems`, fix exactly the lines it lists, then run again.


## R9. Filling the CHECK lines (full)

Each tool section has one line starting with `**CHECK:**`. For each one:
1. Open the URL on the "Official data source" line. If it says "none in the top 5", open the first URL on the "Tool pages already ranking" line.
2. Find the current numbers the tool needs: fee %, flat fees, price per pound, hours, and so on.
3. Replace the whole CHECK line with:
   `- **Current numbers (checked YYYY-MM-DD from <URL>):** <the numbers, copied exactly>`
4. If a page blocks you (403, 404, captcha), try its newest Internet Archive copy (`https://web.archive.org/web/2/<url>`). Never use numbers from search snippets.
5. If the section says "none in the top 5" for both the official source and tool pages: do ONE web search for `<main keyword> official` and use the first result from the maker, a government site or the industry association. If there is none, use the line below.
6. If the page doesn't show the numbers, write:
   `- **Current numbers:** unknown. Check before building.`

**Done when:** tool-pages-report.md contains no `**CHECK:**`.


## R10. Deliver (full)

Send the user:
1. The "Ranked shortlist" table, copied from the report.
2. The "Why it's here" line for each of the 5 tools.
3. One line offering the full report ("Say 'show the full tool report' for the build details"); give the file path only if they ask.
4. One line: "When you build one of these, I'll add its official data sources to keep-pages-up-to-date so its numbers stay current." (Only if that skill is installed.)
5. In FREE MODE only, add this sentence exactly: "These rankings use Google Autocomplete, not search volume. Check the top 2–3 picks in Search Console, Keyword Planner or an SEO tool before building."


## Pitfalls

- Never call the FREE MODE demand number "searches per month".
- If two picks look like the same tool (for example, "mercari fees" and "what percentage does mercari take"), that's fine. The script already merged ideas that share search results.
- "Near me", hours-at-one-location and store-review searches are removed on purpose. They need location pages, not tools.
- If Google Autocomplete returns `429` errors, the script waits by itself. If it keeps failing, wait 10 minutes and redo step 2.
- A big site at #1 does not mean "skip". Look at the small-sites score instead. If small sites are in the top 5, the search is winnable.


## Verification

- [ ] seeds.txt has 8–12 seeds, with at least 2 core, 3 entity and 2 next.
- [ ] suggestions.csv has 500 or more rows.
- [ ] review.txt has no `??`.
- [ ] score.py finished without `ERROR`.
- [ ] tool-pages-report.md has 5 tool sections and no `**CHECK:**`.
- [ ] `next.py` says step 10.


## Tested results (Nov 2026)

- **A resale directory, FREE MODE:** 2,381 suggestions became 63 ideas. The top 3 were marketplace fee calculators for resellers.
- **The same site, DATA MODE (keyword export):** the same top 3 fee calculators.
- **Both modes agreed on the top 3 tools.**
- **Aquarium niche, FREE MODE (new niche, no tuning):** 1,369 suggestions became 82 ideas. The top 3 were a tank volume calculator, an aquarium heater wattage calculator and a filter size calculator. Small sites such as fishtankmath.com and freeaquariumcalculator.com rank for all three.
