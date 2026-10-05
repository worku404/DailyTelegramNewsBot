"""Telegram Bot API message dispatcher.

Delivers plain-text messages with explicit MessageEntity structures to a
Telegram chat via the sendMessage endpoint. Handles multi-chunk delivery
with conservative rate-limit pacing.

Design Decisions:
- Entity-Only Payload: Messages are sent without parse_mode. Formatting is
  expressed entirely through the ``entities`` field, eliminating all escaping
  concerns for special characters.
- Fail-Fast: Any non-ok API response raises RuntimeError immediately.
- Conservative Pacing: 1-second sleep between chunks within a day to stay
  well within Telegram's 30 msg/sec bot limit.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Tuple

import requests

logger = logging.getLogger("react_course_sender.sender")

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/sendMessage"


def send_message(
    bot_token: str,
    chat_id: str,
    text: str,
    entities: List[Dict[str, Any]],
) -> None:
    """Deliver a single message to Telegram via the Bot API sendMessage endpoint.

    Args:
        bot_token: Secret bot authentication token.
        chat_id: Target chat or channel identifier.
        text: Plain-text string (no markup — formatting lives in entities).
        entities: List of serialized Telegram MessageEntity dictionaries.

    Raises:
        RuntimeError: If Telegram API returns an HTTP error or ``ok: false``.
    """
    url = TELEGRAM_API_BASE.format(token=bot_token)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "entities": entities,
        "disable_web_page_preview": True,
    }

    response = requests.post(url, json=payload, timeout=15)

    if not response.ok or not response.json().get("ok", False):
        raise RuntimeError(
            f"Telegram API delivery failed ({response.status_code}): {response.text}"
        )


def send_chunks(
    bot_token: str,
    chat_id: str,
    chunks: List[Tuple[str, List[Dict[str, Any]]]],
) -> None:
    """Deliver an ordered sequence of message chunks to Telegram.

    Sends each chunk via ``send_message`` with a 1-second pause between chunks
    to respect Telegram rate limits.

    Args:
        bot_token: Secret bot authentication token.
        chat_id: Target chat or channel identifier.
        chunks: Ordered list of (text, entities) tuples from the formatter.

    Raises:
        RuntimeError: Propagated from ``send_message`` on any API failure.
    """
    total = len(chunks)
    for i, (text, entities) in enumerate(chunks, 1):
        logger.info("  Sending chunk %d/%d (%d chars)...", i, total, len(text))
        send_message(bot_token, chat_id, text, entities)

        # Rate-limit pacing: pause between chunks but not after the last one.
        if i < total:
            time.sleep(1)
