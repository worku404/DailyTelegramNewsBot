"""Main orchestration module for the Two-Stream Editorial News Scout.

Coordinates:
1. Fetching candidate articles across two broad RSS/Atom streams within the recency window.
2. Filtering previously evaluated URLs via the HistoryManager.
3. Invoking stream-specific Gemini editorial evaluators with broad rubrics.
4. Validating article links via the dead link checker (src.url_validator).
5. Logging exact payloads dispatched to Gemini and Telegram in the terminal.
6. Delivering structured review cards to the editor's private Telegram chat.
7. Persisting evaluated URLs to guarantee zero duplicate alerts.
"""

from __future__ import annotations

import logging
import sys
import time
from typing import List

import feedparser
import requests

from news_curator.config import REVIEW_BOT_TOKEN, REVIEW_CHAT_ID
from news_curator.editorial_evaluator import evaluate_stream_candidates
from news_curator.history import HistoryManager
from news_curator.review_formatter import format_review_card
from news_curator.rss_fetcher import FEED_HEADERS, fetch_candidates_for_stream
from news_curator.sources import STREAMS
from src.pipeline import send_telegram_message
from src.url_validator import is_url_valid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("news_curator.main")


def check_all_feeds() -> None:
    """Diagnostic utility to probe all registered RSS/Atom feeds and display their status."""
    print("=" * 80)
    print("PROBING ALL REGISTERED RSS/ATOM FEEDS (TWO STREAMS)")
    print("=" * 80)

    for stream_id, stream_meta in STREAMS.items():
        print(f"\n--- STREAM {stream_id}: {stream_meta['name'].upper()} ---")
        for source in stream_meta["sources"]:
            try:
                resp = requests.get(source.feed_url, headers=FEED_HEADERS, timeout=10)
                feed = feedparser.parse(resp.content)
                status_label = f"HTTP {resp.status_code}"
                entry_count = len(feed.entries)
                latest_title = feed.entries[0].title[:50] + "..." if entry_count > 0 else "N/A"
                print(f"  [OK] {source.name:<25} | {status_label} | {entry_count:>3} entries | Latest: {latest_title}")
            except Exception as exc:
                print(f"  [FAIL] {source.name:<23} | Error: {exc}")

    print("\n" + "=" * 80)


def test_bot_connection() -> bool:
    """Verify bot token authentication and dispatch a test message to REVIEW_CHAT_ID."""
    print("=" * 80)
    print("TESTING TELEGRAM REVIEW BOT CONNECTION")
    print("=" * 80)

    # 1. Verify Bot Token via getMe
    me_url = f"https://api.telegram.org/bot{REVIEW_BOT_TOKEN}/getMe"
    try:
        me_resp = requests.get(me_url, timeout=10)
        me_data = me_resp.json()
        if not me_resp.ok or not me_data.get("ok"):
            print(f"❌ Bot Token Error: {me_data.get('description', 'Invalid token')}")
            return False

        bot_username = me_data.get("result", {}).get("username", "UnknownBot")
        print(f"✅ Bot Token Valid! Connected as @{bot_username}")
    except Exception as exc:
        print(f"❌ Network error contacting Telegram API: {exc}")
        return False

    # 2. Send test message to REVIEW_CHAT_ID
    msg_url = f"https://api.telegram.org/bot{REVIEW_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": REVIEW_CHAT_ID,
        "text": (
            f"🚀 *Editorial Review Bot Connection Test*\n\n"
            f"Connection verified! Messages dispatched from @{bot_username} will arrive here."
        ),
        "parse_mode": "Markdown",
    }
    logger.info(
        "\n" + "=" * 80 +
        "\n[DATA SENT TO TELEGRAM] Test Message\n" +
        "=" * 80 +
        f"\n{payload['text']}\n" +
        "=" * 80
    )

    try:
        msg_resp = requests.post(msg_url, json=payload, timeout=10)
        msg_data = msg_resp.json()
        if msg_resp.ok and msg_data.get("ok"):
            print(f"✅ Test Message Sent! Successfully delivered to chat ID {REVIEW_CHAT_ID}")
            print(f"👉 Check your Telegram chat with @{bot_username} to confirm.")
            print("=" * 80)
            return True

        error_desc = msg_data.get("description", "Unknown error")
        print(f"❌ Delivery Failed to Chat ID {REVIEW_CHAT_ID}: {error_desc}")
        if "chat not found" in error_desc.lower():
            print("\n💡 HOW TO FIX 'chat not found':")
            print(f"   1. Open Telegram and search for: @{bot_username}")
            print("   2. Click 'Start' (or send /start)")
            print("   3. Run this test command again!")
        print("=" * 80)
        return False
    except Exception as exc:
        print(f"❌ Error sending test message: {exc}")
        return False


def run_editorial_curation(history: HistoryManager | None = None) -> int:
    """Execute editorial scout run across two broad streams.

    Args:
        history: Optional HistoryManager instance. Defaults to loading from standard file.

    Returns:
        Total count of review cards successfully dispatched to the editor.
    """
    history_mgr = history if history is not None else HistoryManager()
    total_dispatched = 0
    urls_to_mark: List[str] = []

    logger.info("Starting Two-Stream Editorial News Scout run...")

    for stream_id, stream_meta in STREAMS.items():
        stream_name = stream_meta["name"]
        sources = stream_meta["sources"]
        logger.info("--- Processing Stream %d: %s (%d feeds) ---", stream_id, stream_name, len(sources))

        candidates = fetch_candidates_for_stream(sources, history_mgr)
        logger.info("Stream %d returned %d fresh candidate article(s).", stream_id, len(candidates))

        if not candidates:
            continue

        selected_stories = evaluate_stream_candidates(stream_id, stream_name, candidates)
        logger.info("Stream %d evaluator selected %d story/stories.", stream_id, len(selected_stories))

        for story in selected_stories:
            article_url = story.get("url", "").strip()

            # Reuse dead link checker to guarantee the selected article URL is live
            if article_url and not is_url_valid(article_url):
                logger.warning(
                    "Selected story '%s' URL failed validation (%s). Skipping dead link.",
                    story.get("title"),
                    article_url,
                )
                continue

            card_text, card_entities = format_review_card(story, stream_id, stream_name)

            # Log exact data being sent to Telegram in terminal using logger.info
            logger.info(
                "\n" + "=" * 80 +
                f"\n[DATA SENT TO TELEGRAM] Stream {stream_id}: {story.get('title')}\n" +
                "=" * 80 +
                f"\n{card_text}\n" +
                "=" * 80
            )

            logger.info("Dispatching review card for '%s' to review chat %s...", story.get("title"), REVIEW_CHAT_ID)
            send_telegram_message(
                bot_token=REVIEW_BOT_TOKEN,
                chat_id=REVIEW_CHAT_ID,
                text=card_text,
                entities=card_entities,
            )

            total_dispatched += 1
            if article_url:
                urls_to_mark.append(article_url)

            # Brief pause to respect Telegram Bot API burst limits
            time.sleep(1.2)

        # Mark all evaluated candidate URLs as seen to prevent re-evaluation on next run
        for c in candidates:
            urls_to_mark.append(c.url)

    # Persist all seen URLs
    history_mgr.mark_seen(urls_to_mark)
    logger.info("Editorial curation run complete. Dispatched %d review cards.", total_dispatched)
    return total_dispatched


def main() -> int:
    """CLI entry point supporting diagnostic flags."""
    if "--check-feeds" in sys.argv or "-c" in sys.argv:
        check_all_feeds()
        return 0

    if "--test-bot" in sys.argv or "-t" in sys.argv:
        success = test_bot_connection()
        return 0 if success else 1

    try:
        dispatched = run_editorial_curation()
        print(f"Editorial Scout completed successfully. Dispatched {dispatched} review card(s).")
        return 0
    except Exception as exc:
        logger.error("Editorial Scout run encountered an unhandled exception: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
