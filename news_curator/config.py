"""Configuration gateway for the editorial news scout subsystem.

Provides centralized access to runtime secrets and environment variables for the
review bot and Gemini evaluation, maintaining fail-fast invariants.
"""

from __future__ import annotations

from decouple import config

from src.config import GEMINI_API_KEYS, GEMINI_MODEL_NAME

# The review bot communicates exclusively with the editor's private chat to stage
# curated drafts before public broadcast.
REVIEW_BOT_TOKEN: str = config("REVIEW_BOT_TOKEN")
REVIEW_CHAT_ID: str = config("REVIEW_CHAT_ID")

# Maximum age of candidate RSS feed items to evaluate (in hours)
RECENCY_WINDOW_HOURS: int = config("RECENCY_WINDOW_HOURS", default=48, cast=int)

# Maximum number of top stories Gemini is permitted to select per editorial stream
MAX_STORIES_PER_STREAM: int = config("MAX_STORIES_PER_STREAM", default=5, cast=int)
