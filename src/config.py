"""Centralized runtime configuration management (Single Source of Truth).

This module acts as the sole authoritative gateway for runtime secrets and
environment variables across the entire application.

Design Decisions & Invariants:
- Fail-Fast Principle: No fallback values or silent default degradation are
  provided for core secrets. If an essential environment variable is omitted,
  decouple.UndefinedValueError is raised at import time to abort execution
  immediately before attempting any network or LLM operations.
- Single Source of Truth (SSOT): Modules must import configuration variables
  directly from this module rather than reading decouple.config or os.environ
  locally.
"""

from decouple import config

GEMINI_API_KEYS: list[str] = [
    config("API1_KEY"),
    config("API2_KEY"),
    config("API3_KEY"),
]

HF_IMAGE_TOKENS: list[str] = [
    config("HF_IMAGE_TOKEN_1"),
    config("HF_IMAGE_TOKEN_2"),
    config("HF_IMAGE_TOKEN_3"),
]

GEMINI_MODEL_NAME: str = config("GEMINI_MODEL_NAME")
TELEGRAM_BOT_TOKEN: str = config("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: str = config("TELEGRAM_CHAT_ID")

