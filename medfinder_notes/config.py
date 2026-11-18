"""Centralized configuration for the MedFinder Notes pipeline.

Editable scheduling and generation knobs live at the top of this file so
changing delivery cadence (e.g. MAX_FILES_PER_RUN = 1, 2, or 3) requires
editing only one constant.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

from decouple import UndefinedValueError, config

# ==============================================================================
# Easy-to-edit pipeline constants
# ==============================================================================

# Maximum number of .md notes sent to Telegram per scheduled run.
MAX_FILES_PER_RUN: int = 2

# Maximum number of .md notes Gemini may generate for a single Pull Request.
MAX_NOTES_PER_PR: int = 4

# Which PRs qualify for automatic sync:
#   "merged" -> only merged PRs (merged_at is set) — recommended default
#   "all"    -> any PR (open or closed)
PR_TRIGGER_MODE: str = "merged"

# Upper bound on PR diff characters sent to Gemini to protect token limits.
MAX_DIFF_CHARS: int = 40_000

# Pause between sequential Telegram document uploads (seconds).
INTER_FILE_PAUSE_SECONDS: float = 1.5

# Target GitHub repository (public)
GITHUB_OWNER: str = "worku404"
GITHUB_REPO: str = "MedFinder-java"

# ==============================================================================
# Package paths
# ==============================================================================

PACKAGE_DIR: Path = Path(__file__).resolve().parent
NOTES_DIR: Path = PACKAGE_DIR / "notes"
TOPICS_FILE: Path = PACKAGE_DIR / "topics.md"
STATE_FILE: Path = PACKAGE_DIR / "state.json"


# ==============================================================================
# Credential loaders (fail-fast when invoked by the stage that needs them)
# ==============================================================================


def get_telegram_credentials() -> Tuple[str, str, Optional[int]]:
    """Return (bot_token, chat_id, topic_thread_id) from .env / environment variables.

    topic_thread_id is None when USER_TOPIC_ID is not set or is blank,
    which means messages go to the General topic (default Telegram behaviour).
    Set USER_TOPIC_ID to the numeric thread ID of the target topic to route
    all notes into that specific topic thread.
    """
    bot_token: str = config("TEMP_11_DAY_REACT_BOT")
    chat_id: str = config("USER_CHAT_ID")
    raw_topic: str = config("USER_TOPIC_ID", default="")
    topic_thread_id: Optional[int] = int(raw_topic.strip()) if raw_topic.strip() else None
    return bot_token, chat_id, topic_thread_id


def get_gemini_config() -> Tuple[list[str], str]:
    """Return (api_keys, model_name) from .env / environment variables."""
    keys: list[str] = []
    for idx in range(1, 9):
        try:
            val = config(f"API{idx}_KEY")
        except UndefinedValueError:
            continue
        if val and val.strip():
            keys.append(val.strip())

    if not keys:
        raise RuntimeError(
            "No Gemini API keys found. Set at least API1_KEY in .env or GitHub Secrets."
        )

    model_name: str = config("GEMINI_MODEL_NAME")
    return keys, model_name


def get_github_token() -> Optional[str]:
    """Return optional GITHUB_TOKEN (used automatically in GitHub Actions)."""
    token = config("GITHUB_TOKEN", default="")
    return token.strip() or None
