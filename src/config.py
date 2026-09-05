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

import decouple
from decouple import config


def _load_hf_image_tokens() -> list[str]:
    """Discover all configured Hugging Face image tokens for failover rotation.

    Checks indexed environment variables (HF_IMAGE_TOKEN_1, HF_IMAGE_TOKEN_2, ...)
    and falls back to the legacy single HF_IMAGE_TOKEN. Preserves discovery order.

    Raises:
        decouple.UndefinedValueError: If no valid Hugging Face token is found.
    """
    tokens: list[str] = []

    # 1. Discover indexed tokens: HF_IMAGE_TOKEN_1, HF_IMAGE_TOKEN_2, ...
    i = 1
    while True:
        tok = config(f"HF_IMAGE_TOKEN_{i}", default=None)
        if tok and tok.strip():
            tokens.append(tok.strip())
            i += 1
        else:
            break

    # 2. Check legacy single HF_IMAGE_TOKEN
    legacy = config("HF_IMAGE_TOKEN", default=None)
    if legacy and legacy.strip() and legacy.strip() not in tokens:
        tokens.append(legacy.strip())

    if not tokens:
        raise decouple.UndefinedValueError(
            "Missing Hugging Face image token. Declare at least HF_IMAGE_TOKEN or HF_IMAGE_TOKEN_1."
        )

    return tokens


GEMINI_API_KEY: str = config("GEMINI_API_KEY")
HF_IMAGE_TOKENS: list[str] = _load_hf_image_tokens()
HF_IMAGE_TOKEN: str = HF_IMAGE_TOKENS[0]
GEMINI_MODEL_NAME: str = config("GEMINI_MODEL_NAME")
TELEGRAM_BOT_TOKEN: str = config("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID: str = config("TELEGRAM_CHAT_ID")
