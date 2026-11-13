# Chelsea FC Atom Feed (moved)

**This feed has moved.** Subscribe to
<https://thechelsuk.github.io/uk.thechels.cfcnews/feed.xml> instead. The new home is the
[uk.thechels.cfcnews](https://github.com/thechelsuk/uk.thechels.cfcnews) repo, which also has a quick-loading page of
the same headlines.

This repo no longer polls Chelsea. Its `docs/feed.xml` holds a single entry pointing to the new feed, so existing
subscribers see where to go.

---

# Chelsea FC Atom Feed

This is an unofficial Atom feed for Chelsea FC's "Latest News" page, built by polling
their internal news-listing JSON API on a 5 minute cron schedule

## Files

- `chelsea_rss.py` - fetches the API and writes an Atom 1.0 XML file.
- `.github/workflows/update-feed.yml` - runs the script every 5 minutes and
  commits `docs/feed.xml` if it changed.
- `requirements.txt` - Python deps (just `requests`).

## One Time Set-up

1. **Settings → Pages** → Source: "Deploy from a branch" → Branch: `main`,
   folder: `/docs` → Save.
1. **Settings → Actions → General → Workflow permissions** → select
   "Read and write permissions" (needed so the workflow can push
   `docs/feed.xml` back to the repo).
1. Wait for the first scheduled run (up to 5 min), or trigger it manually:
   **Actions tab → Update Chelsea FC Atom feed → Run workflow**.
1. Your feed will be live at:
   `https://<your-username>.github.io/<repo-name>/feed.xml`

## Notes / caveats

- GitHub's cron scheduler is best-effort and is set at 5-minute intervals
  however, cron can be delayed under platform load, especially on repos
  with little recent activity.
- The API endpoint was found by reading the site's page source and
  Chelsea could change or remove it at any time.
- Built for my personal use and accessibility needs
