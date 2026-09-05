"""Sequential topic progression and state persistence.

Maintains cursor state across scheduled executions so the bot delivers exactly
one software engineering topic per day, progressing sequentially and wrapping
around only when all topics are exhausted.

Design Decisions & Invariants:
- Deterministic Ordering: Topics are served strictly in the order defined in
  seeds.py without random shuffling.
- Atomic File Persistence: State writes write to a temporary file first and
  replace state.json atomically to prevent state corruption during interruptions.
- Bounds Resilience: If seeds.py is edited and shrinks, the index is safely
  clamped using modulus arithmetic rather than raising IndexError.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

from src.topics import SEED_TOPICS

STATE_FILE = Path(__file__).resolve().parents[1] / "state.json"


def get_current_topic(
    seeds: list[str] = SEED_TOPICS,
    state_path: Path = STATE_FILE,
) -> Tuple[int, str]:
    """Retrieve the index and topic string scheduled for the current run.

    Defaults to the first topic (index 0) if state.json does not yet exist.
    """
    if not seeds:
        raise ValueError("Topic list (seeds.py) cannot be empty.")

    if not state_path.exists():
        return 0, seeds[0]

    with open(state_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Modulus ensures safe wrap-around even if SEED_TOPICS length changes
    raw_index = int(data.get("current_index", 0))
    current_index = raw_index % len(seeds)

    return current_index, seeds[current_index]


def advance_state(
    current_index: int,
    seeds: list[str] = SEED_TOPICS,
    state_path: Path = STATE_FILE,
) -> int:
    """Advance the state cursor to the next sequential topic and persist to disk.

    Wraps back to 0 when the final topic in seeds.py is reached.
    """
    next_index = (current_index + 1) % len(seeds)
    payload = {
        "current_index": next_index,
        "last_topic_posted": seeds[current_index],
        "last_posted_at": datetime.now(timezone.utc).isoformat(),
    }

    temp_path = state_path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    temp_path.replace(state_path)
    return next_index
