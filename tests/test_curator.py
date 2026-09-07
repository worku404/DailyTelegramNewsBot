"""Automated unit test suite for the news_curator package.

Covers:
- HistoryManager persistence, deduplication, and automated pruning.
- RSS parsing, 48-hour timestamp extraction, and seen-URL filtering.
- Tier prompt definitions and structured schema synchronization.
- Editorial evaluation payload handling with mock LLM outputs.
- Telegram review card AST markdown-to-entities formatting.
"""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from news_curator.history import HistoryManager
from news_curator.prompts import CURATION_RESPONSE_SCHEMA, STREAM_PROMPTS
from news_curator.review_formatter import format_review_card
from news_curator.rss_fetcher import (
    CandidateArticle,
    _extract_published_datetime,
    fetch_candidates_for_source,
)
from news_curator.sources import FeedSource


class TestHistoryManager(unittest.TestCase):
    """Validate article deduplication and history file management."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.history_path = Path(self.temp_dir.name) / "seen_articles.json"
        self.mgr = HistoryManager(self.history_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_unseen_url_returns_false(self) -> None:
        self.assertFalse(self.mgr.is_seen("https://blog.cloudflare.com/new-post"))

    def test_mark_seen_and_persistence(self) -> None:
        url = "https://blog.cloudflare.com/incident-123/"
        self.mgr.mark_seen([url])
        self.assertTrue(self.mgr.is_seen(url))
        self.assertTrue(self.mgr.is_seen("https://blog.cloudflare.com/incident-123"))

        # Re-initialize manager from same file to verify persistence
        reloaded = HistoryManager(self.history_path)
        self.assertTrue(reloaded.is_seen(url))

    def test_pruning_removes_expired_entries(self) -> None:
        old_date = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
        fresh_date = datetime.now(timezone.utc).isoformat()

        # Seed with one old and one fresh record
        payload = {
            "seen_urls": {
                "https://example.com/old": old_date,
                "https://example.com/fresh": fresh_date,
            }
        }
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        mgr = HistoryManager(self.history_path)
        # Marking a new URL triggers _prune()
        mgr.mark_seen(["https://example.com/new"])

        self.assertFalse(mgr.is_seen("https://example.com/old"))
        self.assertTrue(mgr.is_seen("https://example.com/fresh"))
        self.assertTrue(mgr.is_seen("https://example.com/new"))


class TestRssFetcher(unittest.TestCase):
    """Validate RSS parsing and recency filtering."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.history = HistoryManager(Path(self.temp_dir.name) / "seen.json")
        self.dummy_source = FeedSource(
            name="Test Blog",
            feed_url="https://test.com/rss",
            site_url="https://test.com",
            stream_id=1,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_extract_published_datetime(self) -> None:
        # Create a mock entry with published_parsed 9-tuple
        now = datetime.now(timezone.utc)
        mock_entry = MagicMock()
        mock_entry.published_parsed = now.timetuple()
        mock_entry.updated_parsed = None

        extracted = _extract_published_datetime(mock_entry)
        self.assertIsNotNone(extracted)
        self.assertEqual(extracted.year, now.year)

    @patch("requests.get")
    def test_fetch_candidates_filters_old_and_seen(self, mock_get: MagicMock) -> None:
        # Construct raw RSS XML with one fresh item and one seen item
        now_rfc822 = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%a, %d %b %Y %H:%M:%S GMT")
        old_rfc822 = (datetime.now(timezone.utc) - timedelta(hours=100)).strftime("%a, %d %b %Y %H:%M:%S GMT")

        rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Test Blog</title>
                <link>https://test.com</link>
                <item>
                    <title>Fresh Article</title>
                    <link>https://test.com/fresh</link>
                    <pubDate>{now_rfc822}</pubDate>
                    <description>Technical summary</description>
                </item>
                <item>
                    <title>Old Article</title>
                    <link>https://test.com/old</link>
                    <pubDate>{old_rfc822}</pubDate>
                    <description>Old summary</description>
                </item>
                <item>
                    <title>Seen Article</title>
                    <link>https://test.com/seen</link>
                    <pubDate>{now_rfc822}</pubDate>
                    <description>Already seen</description>
                </item>
            </channel>
        </rss>"""

        mock_get.return_value.status_code = 200
        mock_get.return_value.content = rss_xml.encode("utf-8")

        # Mark 'seen' article in history
        self.history.mark_seen(["https://test.com/seen"])

        candidates = fetch_candidates_for_source(self.dummy_source, self.history, recency_hours=48)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0].title, "Fresh Article")
        self.assertEqual(candidates[0].url, "https://test.com/fresh")


class TestReviewFormatter(unittest.TestCase):
    """Validate review card Markdown compilation and entity structure."""

    def test_format_review_card_content(self) -> None:
        story = {
            "title": "BGP Dampening Cascade",
            "author": "John Doe",
            "source_name": "Cloudflare Blog",
            "url": "https://blog.cloudflare.com/bgp-cascade",
            "why_it_matters": "Shows memory buffer saturation under routing convergence loops.",
            "key_takeaway": "Decouple control plane timers from data plane packet queues.",
            "ready_to_ship_draft": "🚨 **Architecture Case Study: BGP Cascade**\n\n• Point 1\n• Point 2",
        }

        text, entities = format_review_card(story, 1, "Big Tech, AI & Developer Ecosystem")

        self.assertIn("STREAM 1", text)
        self.assertIn("BIG TECH, AI & DEVELOPER ECOSYSTEM", text)
        self.assertIn("BGP Dampening Cascade", text)
        self.assertIn("John Doe", text)
        self.assertIn("Cloudflare Blog", text)
        self.assertIn("Why This Matters", text)
        self.assertIn("READY-TO-SHIP DRAFT", text)
        self.assertIn("Architecture Case Study: BGP Cascade", text)

        entity_types = {e["type"] for e in entities}
        self.assertIn("bold", entity_types)
        self.assertIn("blockquote", entity_types)


class TestPromptsAndEvaluator(unittest.TestCase):
    """Validate stream prompt registration and evaluator contracts."""

    def test_all_streams_have_prompts(self) -> None:
        for stream_id in (1, 2):
            self.assertIn(stream_id, STREAM_PROMPTS)
            prompt = STREAM_PROMPTS[stream_id]
            self.assertIn("ready_to_ship_draft", prompt)
            self.assertIn("why_it_matters", prompt)

    def test_schema_requires_story_properties(self) -> None:
        item_schema = CURATION_RESPONSE_SCHEMA["properties"]["selected_stories"]["items"]
        required = item_schema["required"]
        self.assertIn("title", required)
        self.assertIn("why_it_matters", required)
        self.assertIn("ready_to_ship_draft", required)

    @patch("news_curator.editorial_evaluator.genai.Client")
    def test_evaluate_stream_candidates_success(self, mock_client_cls: MagicMock) -> None:
        from news_curator.editorial_evaluator import evaluate_stream_candidates

        fake_client = MagicMock()
        mock_client_cls.return_value = fake_client

        mock_payload = {
            "selected_stories": [
                {
                    "title": "Test Title",
                    "author": "Test Author",
                    "source_name": "Test Blog",
                    "url": "https://test.com/post",
                    "why_it_matters": "Matter 1. Matter 2.",
                    "key_takeaway": "Takeaway invariant.",
                    "ready_to_ship_draft": "Draft text",
                }
            ]
        }

        fake_response = MagicMock()
        fake_response.text = json.dumps(mock_payload)
        fake_client.models.generate_content.return_value = fake_response

        candidate = CandidateArticle(
            source_name="Test Blog",
            stream_id=1,
            title="Raw Title",
            url="https://test.com/post",
            author="Author",
            summary="Summary",
        )

        results = evaluate_stream_candidates(1, "Big Tech, AI & Developer Ecosystem", [candidate], api_keys=["mock_key"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Test Title")


if __name__ == "__main__":
    unittest.main()
