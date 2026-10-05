"""Entry-point for the React Course Sender pipeline.

Loads structured lesson data from lessons.json, formats the scheduled day into
Telegram-ready chunks (plain text + MessageEntity dicts), dispatches them
to Telegram, and advances the persistent state cursor in react_state.json.

Usage:
    python -m react_course_sender.main              # send scheduled day and advance state
    python -m react_course_sender.main --day 2       # test/send only Day 2 (does not advance state)
    python -m react_course_sender.main --all         # send ALL days sequentially
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time

from react_course_sender.config import JSON_FILE_PATH, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from react_course_sender.formatter import format_day
from react_course_sender.scheduler import advance_state, get_current_lesson
from react_course_sender.sender import send_chunks

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("react_course_sender.main")

# Pause between days if sending multiple days.
INTER_DAY_PAUSE_SECONDS = 2


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send React course lessons to Telegram.")
    parser.add_argument(
        "--day",
        type=int,
        default=None,
        help="Send only this day number without advancing state (e.g. --day 1).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Send all days in curriculum sequentially.",
    )
    return parser.parse_args()


def main() -> int:
    """Load curriculum and deliver scheduled or selected day(s) to Telegram."""
    args = _parse_args()

    logger.info("Loading curriculum from %s ...", JSON_FILE_PATH)

    with open(JSON_FILE_PATH, encoding="utf-8") as f:
        data = json.load(f)

    all_days = data.get("days", [])
    if not all_days:
        logger.error("No 'days' array found in JSON — nothing to send.")
        return 1

    book_title = data.get("book", "Unknown Book")
    logger.info("Book: %s (%d total days available)", book_title, len(all_days))

    # Mode 1: Manual override for a specific day
    if args.day is not None:
        target_days = [d for d in all_days if d.get("day") == args.day]
        if not target_days:
            logger.error("Day %d not found in JSON (available: %s).",
                         args.day, [d.get("day") for d in all_days])
            return 1

        day_entry = target_days[0]
        day_num = day_entry.get("day", "?")
        logger.info("Manual send for Day %s: %s (state will not advance)", day_num, day_entry.get("title"))
        chunks = format_day(day_entry)
        logger.info("Day %s split into %d chunk(s).", day_num, len(chunks))
        send_chunks(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, chunks)
        logger.info("✓ Day %s delivered successfully.", day_num)
        return 0

    # Mode 2: Send all days
    if args.all:
        logger.info("Sending all %d days sequentially...", len(all_days))
        for day_entry in all_days:
            day_num = day_entry.get("day", "?")
            logger.info("Formatting Day %s: %s", day_num, day_entry.get("title"))
            chunks = format_day(day_entry)
            send_chunks(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, chunks)
            logger.info("✓ Day %s delivered successfully.", day_num)
            if day_entry is not all_days[-1]:
                time.sleep(INTER_DAY_PAUSE_SECONDS)
        logger.info("All days delivered.")
        return 0

    # Mode 3: Default scheduled execution (1 day per run + advance state)
    current_index, current_lesson = get_current_lesson(all_days)
    if current_lesson is None:
        logger.info("Course is already completed! All %d days posted.", len(all_days))
        return 0

    day_num = current_lesson.get("day", current_index + 1)
    day_title = current_lesson.get("title", "Untitled")
    logger.info("Delivering scheduled Day %s (index %d): %s", day_num, current_index, day_title)

    chunks = format_day(current_lesson)
    logger.info("Day %s split into %d chunk(s).", day_num, len(chunks))

    send_chunks(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, chunks)
    logger.info("✓ Day %s delivered to Telegram.", day_num)

    next_idx = advance_state(current_index, len(all_days), current_lesson)
    logger.info("State advanced. Next scheduled index: %d", next_idx)
    return 0


if __name__ == "__main__":
    sys.exit(main())
