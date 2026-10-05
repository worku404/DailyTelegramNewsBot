"""Sequential lesson progression and state persistence for the React course.

Maintains cursor state across scheduled executions so the bot delivers exactly
one React chapter per day, progressing sequentially and marking completion.

Design Decisions:
- Deterministic Ordering: Lessons are served strictly in order (Day 1 -> Day 2 -> ...).
- Atomic File Persistence: State writes write to a temporary file first and
  replace react_state.json atomically to prevent state corruption during interruptions.
- Bounds Resilience: Clamps gracefully if the days list is updated.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from react_course_sender.config import STATE_FILE_PATH

logger = logging.getLogger("react_course_sender.scheduler")


def load_state(state_path: Path = STATE_FILE_PATH) -> Dict[str, Any]:
    """Read the current state from disk or return default initial state."""
    if not state_path.exists():
        return {
            "current_index": 0,
            "last_day_posted": None,
            "last_chapter_posted": None,
            "last_posted_at": None,
            "completed": False,
        }

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {
                    "current_index": 0,
                    "last_day_posted": None,
                    "last_chapter_posted": None,
                    "last_posted_at": None,
                    "completed": False,
                }
            return json.loads(content)
    except Exception as e:
        logger.warning("Could not read %s (%s). Using default state.", state_path, e)
        return {
            "current_index": 0,
            "last_day_posted": None,
            "last_chapter_posted": None,
            "last_posted_at": None,
            "completed": False,
        }


def get_current_lesson(
    days: List[Dict[str, Any]],
    state_path: Path = STATE_FILE_PATH,
) -> Tuple[int, Dict[str, Any] | None]:
    """Retrieve the index and lesson scheduled for the current run.

    Returns:
        (current_index, lesson_dict) or (current_index, None) if course is completed.
    """
    if not days:
        raise ValueError("Lesson list cannot be empty.")

    state = load_state(state_path)
    current_index = int(state.get("current_index", 0))

    if current_index >= len(days):
        logger.info("All %d lessons in curriculum have already been posted.", len(days))
        return current_index, None

    return current_index, days[current_index]


def advance_state(
    current_index: int,
    total_days: int,
    day_entry: Dict[str, Any],
    state_path: Path = STATE_FILE_PATH,
) -> int:
    """Advance the state cursor to the next sequential day and persist to disk."""
    next_index = current_index + 1
    completed = next_index >= total_days

    payload = {
        "current_index": next_index,
        "last_day_posted": day_entry.get("day"),
        "last_chapter_posted": day_entry.get("chapter"),
        "last_posted_at": datetime.now(timezone.utc).isoformat(),
        "completed": completed,
    }

    state_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = state_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    temp_path.replace(state_path)
    return next_index
