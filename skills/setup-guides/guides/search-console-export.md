# Download your Google Search Console data

**Why:** it shows which pages Google already likes and which are almost on page 1, so Hermes picks better links and topics. Optional, free.

**You need:** 2 minutes, a Search Console account for your site.

1. Go to **search.google.com/search-console** and pick your site.
2. Click **"Performance"** (it may say "Search results") in the left menu.
3. At the top, click the date and choose **"Last 3 months"**.
4. Under the chart, click the **"Pages"** tab.
5. Click **"Export"** (top right, a download icon) → **"Download CSV"**.
6. Drag the downloaded file into this chat.

**You'll know it worked when** Hermes says how many pages it read.

**No Search Console yet?** That's fine: everything works without it. (Setting it up takes a day for Google to collect data; ask me later.)

**Stuck?** Tell me what you see at the top of the Performance page.

---
## For Hermes
- Save the file to `notes/<slug>/tmp/gsc-pages.csv`; internal-links reads it with `--gsc`. The download may be a zip with several CSVs: use `Pages.csv`.
- Limit: 1,000 rows; "~" and "-" export as 0.

<sub>Source: support.google.com/webmasters/answer/12919797 (export formats incl. CSV, 1,000-row cap) and answer/7576553; exact button wording NOT in the docs, from the live UI: confirm on screen. Checked 2026-11-17.</sub>
