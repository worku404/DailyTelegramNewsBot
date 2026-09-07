"""RSS and Atom feed fetcher with recency filtering and deduplication.

Design Decisions & Invariants:
- Requests Transport Layer: Rather than relying on feedparser's built-in urllib fetcher,
  we fetch XML payloads using requests with an explicit browser User-Agent, Accept headers,
  and strict timeout. This prevents HTTP 403 Forbidden and 406 Not Acceptable rejections.
- 48-Hour Recency Boundary: Discards articles published outside the configured recency
  window to guarantee fresh news.
- History Interception: Discards articles whose canonical links already exist in
  the seen_articles.json registry before presenting to the LLM.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import time

import feedparser
import requests

from news_curator.config import RECENCY_WINDOW_HOURS
from news_curator.history import HistoryManager
from news_curator.sources import FeedSource

logger = logging.getLogger("news_curator.rss_fetcher")

FEED_FETCH_TIMEOUT_SECONDS = 15
FEED_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
}


@dataclass
class CandidateArticle:
    """Represents an unreviewed candidate engineering article fetched from a feed."""
    source_name: str
    stream_id: int
    title: str
    url: str
    author: str
    summary: str
    published_at: Optional[datetime] = None


def _extract_published_datetime(entry: feedparser.FeedParserDict) -> Optional[datetime]:
    """Extract and normalize publication timestamp to a timezone-aware UTC datetime."""
    time_struct = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if time_struct:
        try:
            # feedparser parsed time tuples are UTC
            timestamp = time.mktime(time_struct)
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except Exception:
            pass
    return None


def fetch_candidates_for_source(
    source: FeedSource,
    history: HistoryManager,
    recency_hours: int = RECENCY_WINDOW_HOURS,
) -> List[CandidateArticle]:
    """Fetch and filter candidate articles from a single technical RSS/Atom source.

    Args:
        source: Feed metadata containing the endpoint and stream_id.
        history: HistoryManager instance for deduplication check.
        recency_hours: Number of hours in the past to accept articles from.

    Returns:
        List of CandidateArticle objects meeting the freshness and uniqueness criteria.
    """
    logger.info("Fetching RSS feed for '%s' (%s)...", source.name, source.feed_url)
    try:
        response = requests.get(
            source.feed_url,
            headers=FEED_HEADERS,
            timeout=FEED_FETCH_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except Exception as exc:
        logger.warning("Failed to fetch RSS for '%s': %s", source.name, exc)
        return []

    feed = feedparser.parse(response.content)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=recency_hours)
    candidates: List[CandidateArticle] = []

    for entry in feed.entries:
        link = getattr(entry, "link", "").strip()
        title = getattr(entry, "title", "").strip()

        if not link or not title:
            continue

        # Skip already-reviewed stories immediately
        if history.is_seen(link):
            continue

        pub_date = _extract_published_datetime(entry)
        if pub_date and pub_date < cutoff:
            # Article is older than our recency threshold (e.g. 48 hours)
            continue

        # Extract author with fallback to publication source name
        author = getattr(entry, "author", "") or getattr(entry, "author_detail", {}).get("name", "")
        author = author.strip() or source.name

        # Clean summary/description snippet (up to 1000 chars for good context)
        raw_summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
        clean_summary = " ".join(raw_summary.split())[:1000]

        candidates.append(
            CandidateArticle(
                source_name=source.name,
                stream_id=source.stream_id,
                title=title,
                url=link,
                author=author,
                summary=clean_summary,
                published_at=pub_date,
            )
        )

    logger.info("Found %d fresh candidate(s) from '%s'.", len(candidates), source.name)
    return candidates


def fetch_candidates_for_stream(
    sources: List[FeedSource],
    history: HistoryManager,
    recency_hours: int = RECENCY_WINDOW_HOURS,
) -> List[CandidateArticle]:
    """Aggregate fresh candidate articles across all sources belonging to an editorial stream."""
    all_candidates: List[CandidateArticle] = []
    for source in sources:
        candidates = fetch_candidates_for_source(source, history, recency_hours=recency_hours)
        all_candidates.extend(candidates)
    return all_candidates
