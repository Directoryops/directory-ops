# tool-page-finder

Finds calculator and tool page opportunities for any website.
- **FREE MODE:** runs on Google Autocomplete plus web search.
- **DATA MODE:** switches on automatically when you add a keyword export with volume (Ahrefs, Semrush, Keyword Planner, or Search Console).

Written as a literal step-by-step SOP so smaller models can run it.

## Files
- `SKILL.md`: the procedure
- `scripts/next.py`: looks at the work folder and prints the exact next step and command
- `scripts/suggest.py`: Google Autocomplete expansion (step 2)
- `scripts/classify.py`: groups keywords into tool ideas, filters noise, detects the mode and writes review.txt (steps 3–4)
- `scripts/score.py`: makes the search-results template, validates it, scores out of 100 and merges duplicates (steps 5–7)
- `scripts/brief.py`: report with pre-filled briefs (step 8)
- `scripts/sitemap_tools.py`: optional; lists a competitor's tool pages

## Requirements
- Python 3.8+ (standard library only)
- Access to suggestqueries.google.com
- A web search tool

## Install
- **Hermes:** copy this folder to `~/.hermes/skills/seo/tool-page-finder/`.
- **Claude Code:** copy it to `~/.claude/skills/tool-page-finder/`.
- **Other agents:** replace `${HERMES_SKILL_DIR}` with the folder path.
