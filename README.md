# Chelsea FC Atom Feed

Unofficial Atom feed for Chelsea FC's "Latest News" page, built by polling
their internal news-listing JSON API (undocumented, may change/break).

## Files

- `chelsea_rss.py` - fetches the API and writes an Atom 1.0 XML file.
- `.github/workflows/update-feed.yml` - runs the script every 5 minutes and
  commits `docs/feed.xml` if it changed.
- `requirements.txt` - Python deps (just `requests`).

## Setup (one-time)

1. Push this repo to GitHub.
2. **Settings → Pages** → Source: "Deploy from a branch" → Branch: `main`,
   folder: `/docs` → Save.
3. **Settings → Actions → General → Workflow permissions** → select
   "Read and write permissions" (needed so the workflow can push
   `docs/feed.xml` back to the repo).
4. Wait for the first scheduled run (up to 5 min), or trigger it manually:
   **Actions tab → Update Chelsea FC Atom feed → Run workflow**.
5. Your feed will be live at:
   `https://<your-username>.github.io/<repo-name>/feed.xml`

## Notes / caveats

- GitHub's cron scheduler is best-effort: a 5-minute cron can be delayed
  under platform load, especially on repos with little recent activity.
  If you need guaranteed 5-minute freshness, an external cron host
  (e.g. a small VPS, or a service like cron-job.org hitting a webhook)
  is more reliable than GitHub's built-in scheduler.
- The API endpoint was found by reading the site's page source, not from
  official documentation - Chelsea could change or remove it at any time.
  If the workflow starts failing, check the Action logs first.
- For personal/accessibility use only - review Chelsea FC's Terms of Use
  before wider redistribution.
