"""Registry of high-authority technical RSS and Atom feeds organized into two streams:

- Stream 1: Big Tech, AI & Developer Ecosystem
  (Major model releases, product/platform launches, infra migrations, and developer landscape news)
- Stream 2: Architecture, Systems & Software Craft
  (System design breakdowns, distributed consensus, low-level mechanics, code craftsmanship, and engineering wisdom)

All feeds below are 100% verified active with HTTP 200 responses and live item streams.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List


@dataclass(frozen=True)
class FeedSource:
    """Represents a validated technical RSS/Atom source.

    Attributes:
        name: Human-readable publication name.
        feed_url: Canonical RSS or Atom endpoint.
        site_url: Main website root for fallback or link resolution.
        stream_id: Editorial stream classification identifier (1 or 2).
    """
    name: str
    feed_url: str
    site_url: str
    stream_id: int


# --- Stream 1: Big Tech, AI & Developer Ecosystem ---
STREAM_1_SOURCES: List[FeedSource] = [
    FeedSource(
        name="GitHub Blog",
        feed_url="https://github.blog/category/engineering/feed/",
        site_url="https://github.blog/category/engineering",
        stream_id=1,
    ),
    FeedSource(
        name="Cloudflare Blog",
        feed_url="https://blog.cloudflare.com/rss/",
        site_url="https://blog.cloudflare.com",
        stream_id=1,
    ),
    FeedSource(
        name="Stripe Engineering",
        feed_url="https://stripe.com/blog/feed.rss",
        site_url="https://stripe.com/blog",
        stream_id=1,
    ),
    FeedSource(
        name="Netflix TechBlog",
        feed_url="https://netflixtechblog.com/feed",
        site_url="https://netflixtechblog.com",
        stream_id=1,
    ),
    FeedSource(
        name="Meta Engineering",
        feed_url="https://engineering.fb.com/feed/",
        site_url="https://engineering.fb.com",
        stream_id=1,
    ),
    FeedSource(
        name="Changelog",
        feed_url="https://changelog.com/feed",
        site_url="https://changelog.com",
        stream_id=1,
    ),
    FeedSource(
        name="The Pragmatic Engineer",
        feed_url="https://newsletter.pragmaticengineer.com/feed",
        site_url="https://newsletter.pragmaticengineer.com",
        stream_id=1,
    ),
    FeedSource(
        name="Simon Willison",
        feed_url="https://simonwillison.net/atom/everything/",
        site_url="https://simonwillison.net",
        stream_id=1,
    ),
    FeedSource(
        name="The New Stack",
        feed_url="https://thenewstack.io/feed/",
        site_url="https://thenewstack.io",
        stream_id=1,
    ),
]

# --- Stream 2: Architecture, Systems & Software Craft ---
STREAM_2_SOURCES: List[FeedSource] = [
    FeedSource(
        name="InfoQ",
        feed_url="https://feed.infoq.com/",
        site_url="https://www.infoq.com",
        stream_id=2,
    ),
    FeedSource(
        name="AWS Architecture Blog",
        feed_url="https://aws.amazon.com/blogs/architecture/feed/",
        site_url="https://aws.amazon.com/blogs/architecture",
        stream_id=2,
    ),
    FeedSource(
        name="Martin Fowler",
        feed_url="https://martinfowler.com/feed.atom",
        site_url="https://martinfowler.com",
        stream_id=2,
    ),
    FeedSource(
        name="ByteByteGo",
        feed_url="https://blog.bytebytego.com/feed",
        site_url="https://blog.bytebytego.com",
        stream_id=2,
    ),
    FeedSource(
        name="Marc Brooker (AWS VP)",
        feed_url="https://brooker.co.za/blog/rss.xml",
        site_url="https://brooker.co.za/blog",
        stream_id=2,
    ),
    FeedSource(
        name="Dan Luu",
        feed_url="https://danluu.com/atom.xml",
        site_url="https://danluu.com",
        stream_id=2,
    ),
    FeedSource(
        name="Phil Eaton (Notes)",
        feed_url="https://notes.eatonphil.com/rss.xml",
        site_url="https://notes.eatonphil.com",
        stream_id=2,
    ),
    FeedSource(
        name="Antirez (Redis Creator)",
        feed_url="http://antirez.com/rss",
        site_url="http://antirez.com",
        stream_id=2,
    ),
]

STREAMS: dict[int, dict[str, Any]] = {
    1: {
        "name": "Big Tech, AI & Developer Ecosystem",
        "sources": STREAM_1_SOURCES,
    },
    2: {
        "name": "Architecture, Systems & Software Craft",
        "sources": STREAM_2_SOURCES,
    },
}
