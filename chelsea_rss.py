#!/usr/bin/env python3
"""
Chelsea FC News -> Atom feed generator

Source: Chelsea FC's internal news-listing JSON API (found in the page's
inline __webSettings__ / NewsListModule data-props, not publicly documented,
so it may change without notice).

API: https://www.chelseafc.com/en/api/news/listing/7rJyiGvKIDGe6kNF0jRwJ5

IMPORTANT LIMITATIONS (verified against live API response):
- The API returns only: id, title, type, category, url, thumbnail. There is
  NO article body/snippet/description field. <summary> is therefore limited
  to "type / category" - there is no richer content available from this
  endpoint without fetching each article page individually.
- The API returns NO publish-date field. This script derives a best-effort
  <published> date from (in order of preference):
    1. A YYYY/MM/DD date embedded in the thumbnail asset path
       (e.g. ".../editorial/news/2026/08/02/...")
    2. The Cloudinary asset version number in the thumbnail URL
       (e.g. "v1785686546"), which is a Unix timestamp of when the image
       was uploaded - usually same-day as publish, but not guaranteed.
    3. Fallback: current time (script run time), same as <updated>.
  This is NOT a verified article-publish timestamp. Treat it as an estimate.

Usage:
    python3 chelsea_rss.py                 # writes feed.xml (Atom 1.0)
    python3 chelsea_rss.py --out feed.xml
    python3 chelsea_rss.py --limit 30
"""

import argparse
import hashlib
import re
import sys
from datetime import datetime, timezone
from xml.sax.saxutils import escape

import requests

API_URL = "https://www.chelseafc.com/en/api/news/listing/7rJyiGvKIDGe6kNF0jRwJ5"
SITE_BASE = "https://www.chelseafc.com"
FEED_TITLE = "Chelsea FC - Latest News"
FEED_ALT_LINK = "https://www.chelseafc.com/en/news/latest-news"
FEED_SUBTITLE = "Unofficial Atom feed generated from Chelsea FC's news listing API."
FEED_ID = "tag:chelseafc.com,2026:latest-news"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

# Matches .../2026/08/02/... in an asset path
DATE_PATH_RE = re.compile(r"/(\d{4})/(\d{2})/(\d{2})/")
# Matches Cloudinary version prefix like v1785686546
CLOUDINARY_VERSION_RE = re.compile(r"/v(\d{9,13})/")


def fetch_items(limit: int) -> list[dict]:
    """Fetch news items from the Chelsea FC API. Handles a couple of
    plausible JSON shapes since the exact schema wasn't verified live."""
    resp = requests.get(API_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if isinstance(data, dict) and "items" in data:
        items = data["items"]
    elif isinstance(data, list):
        items = data
    elif isinstance(data, dict) and "initialContent" in data:
        items = data["initialContent"].get("items", [])
    else:
        raise ValueError(
            "Unrecognized JSON shape from API. Top-level keys: "
            f"{list(data.keys()) if isinstance(data, dict) else type(data)}"
        )

    return items[:limit]


def extract_published(item: dict, now_str: str) -> tuple[str, str]:
    """
    Best-effort published date for an item.
    Returns (rfc3339_string, method) where method is one of:
      "path-date", "cloudinary-version", "fallback-now"
    """
    thumb_id = ""
    thumb_url = ""
    try:
        thumb_id = item["thumbnail"]["id"] or ""
    except (KeyError, TypeError):
        pass
    try:
        thumb_url = item["thumbnail"]["file"]["url"] or ""
    except (KeyError, TypeError):
        pass

    # 1. Date embedded in asset path, e.g. editorial/news/2026/08/02/...
    for source in (thumb_id, thumb_url):
        m = DATE_PATH_RE.search(source)
        if m:
            year, month, day = (int(x) for x in m.groups())
            try:
                dt = datetime(year, month, day, tzinfo=timezone.utc)
                return dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "path-date"
            except ValueError:
                pass  # bad date components, fall through

    # 2. Cloudinary version number = unix timestamp of upload
    m = CLOUDINARY_VERSION_RE.search(thumb_url)
    if m:
        try:
            ts = int(m.group(1))
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%SZ"), "cloudinary-version"
        except (ValueError, OSError, OverflowError):
            pass

    # 3. Fallback - same logic as <updated>
    return now_str, "fallback-now"


def normalise(item: dict, now_str: str) -> dict:
    """Map a Chelsea API item to standard feed fields."""
    rel_url = item.get("url", "")
    link = rel_url if rel_url.startswith("http") else SITE_BASE + rel_url

    thumb = ""
    try:
        thumb = item["thumbnail"]["file"]["url"]
    except (KeyError, TypeError):
        pass

    category = ""
    try:
        category = item["category"]["title"]
    except (KeyError, TypeError):
        pass

    item_id = item.get("id") or hashlib.sha1(link.encode()).hexdigest()

    published, method = extract_published(item, now_str)

    return {
        "id": item_id,
        "title": item.get("title", "Untitled"),
        "link": link,
        "category": category,
        "type": item.get("type", ""),
        "thumbnail": thumb,
        "published": published,
        "date_method": method,
    }


def build_atom(items: list[dict], self_url: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    entries = []
    for it in items:
        n = normalise(it, now)
        summary_bits = [n["type"], n["category"], f"date-source:{n['date_method']}"]
        summary = " / ".join(b for b in summary_bits if b)
        thumb_link = (
            f'<link rel="enclosure" type="image/jpeg" href="{escape(n["thumbnail"])}"/>'
            if n["thumbnail"]
            else ""
        )
        entries.append(f"""
  <entry>
    <title>{escape(n['title'])}</title>
    <link rel="alternate" href="{escape(n['link'])}"/>
    {thumb_link}
    <id>tag:chelseafc.com,2026:news:{escape(n['id'])}</id>
    <published>{n['published']}</published>
    <updated>{now}</updated>
    <summary>{escape(summary)}</summary>
  </entry>""")

    self_link = f'<link rel="self" href="{escape(self_url)}"/>' if self_url else ""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>{escape(FEED_TITLE)}</title>
  <link rel="alternate" href="{escape(FEED_ALT_LINK)}"/>
  {self_link}
  <id>{escape(FEED_ID)}</id>
  <updated>{now}</updated>
  <subtitle>{escape(FEED_SUBTITLE)}</subtitle>{''.join(entries)}
</feed>
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="feed.xml", help="Output file path")
    parser.add_argument("--limit", type=int, default=20, help="Max items in feed")
    parser.add_argument(
        "--self-url",
        default="",
        help="Public URL this feed will be served at (used for the atom:link rel=self tag)",
    )
    args = parser.parse_args()

    try:
        items = fetch_items(args.limit)
    except Exception as e:
        print(f"ERROR fetching/parsing API: {e}", file=sys.stderr)
        sys.exit(1)

    if not items:
        print("WARNING: no items returned - check API response shape.", file=sys.stderr)

    xml = build_atom(items, args.self_url)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(xml)

    print(f"Wrote {len(items)} items to {args.out}")


if __name__ == "__main__":
    main()
