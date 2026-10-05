"""Centralized configuration for the React Course Sender pipeline.

Reads bot credentials from the project's .env file via python-decouple.
Fails fast at import time if any required variable is missing.
"""

from __future__ import annotations

from pathlib import Path

from decouple import config

TELEGRAM_BOT_TOKEN: str = config("TEMP_11_DAY_REACT_BOT")
TELEGRAM_CHAT_ID: str = config("USER_CHAT_ID")

PACKAGE_DIR = Path(__file__).resolve().parent
JSON_FILE_PATH: Path = PACKAGE_DIR / "lessons.json"
STATE_FILE_PATH: Path = PACKAGE_DIR / "react_state.json"
