"""Telegram Bot API message dispatcher with retry logic and atomic rollback.

Delivers plain-text messages with explicit MessageEntity structures to a
Telegram chat via the sendMessage endpoint. Handles multi-chunk delivery
with conservative rate-limit pacing, exponential backoff for transient
network drops, and atomic all-or-nothing rollback on unrecoverable failures.

Design Decisions:
- Entity-Only Payload: Formatting is expressed entirely through ``entities``.
- Transient Network Resilience: Retries up to 4 times with exponential backoff
  on ConnectionResetError / WinError 10054 / Timeouts.
- Rate-Limit Awareness: Respects Telegram's 429 ``retry_after`` directive.
- All-or-Nothing Atomicity: If any chunk fails after exhausting all retries,
  all previously delivered chunks for that day are rolled back (deleted)
  so no partial lessons remain in the chat and state does not desynchronize.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Tuple

import requests

logger = logging.getLogger("react_course_sender.sender")

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}/{method}"
MAX_CHUNK_RETRIES = 4
INITIAL_BACKOFF_SECONDS = 2.0

# Persistent session to reuse TCP connections across chunks
_SESSION = requests.Session()


def delete_messages(bot_token: str, chat_id: str, message_ids: List[int]) -> None:
    """Best-effort deletion of messages to preserve atomic all-or-nothing delivery."""
    if not message_ids:
        return

    logger.warning("Rolling back %d previously sent chunk(s) from chat %s...", len(message_ids), chat_id)

    # 1. Try batch deleteMessages endpoint (Telegram Bot API 7.0+)
    try:
        url = TELEGRAM_API_BASE.format(token=bot_token, method="deleteMessages")
        resp = _SESSION.post(url, json={"chat_id": chat_id, "message_ids": message_ids}, timeout=10)
        if resp.ok and resp.json().get("ok", False):
            logger.info("Rollback successful. %d messages deleted via batch delete.", len(message_ids))
            return
    except Exception as e:
        logger.debug("Batch deleteMessages failed (%s); falling back to single delete.", e)

    # 2. Fallback to individual deleteMessage calls
    deleted_count = 0
    for msg_id in message_ids:
        try:
            url = TELEGRAM_API_BASE.format(token=bot_token, method="deleteMessage")
            resp = _SESSION.post(url, json={"chat_id": chat_id, "message_id": msg_id}, timeout=8)
            if resp.ok and resp.json().get("ok", False):
                deleted_count += 1
            time.sleep(0.2)
        except Exception as e:
            logger.warning("Could not delete message %d: %s", msg_id, e)

    logger.info("Rollback complete. %d/%d chunks removed.", deleted_count, len(message_ids))


def send_message_with_retry(
    bot_token: str,
    chat_id: str,
    text: str,
    entities: List[Dict[str, Any]],
    chunk_index: int,
    total_chunks: int,
) -> int:
    """Deliver a single message chunk with exponential backoff retry.

    Returns:
        The Telegram message_id of the successfully sent message.

    Raises:
        RuntimeError: If all retries are exhausted or non-retryable error occurs.
    """
    url = TELEGRAM_API_BASE.format(token=bot_token, method="sendMessage")
    payload = {
        "chat_id": chat_id,
        "text": text,
        "entities": entities,
        "disable_web_page_preview": True,
    }

    backoff = INITIAL_BACKOFF_SECONDS

    for attempt in range(1, MAX_CHUNK_RETRIES + 1):
        try:
            logger.info("  Sending chunk %d/%d (%d chars, attempt %d/%d)...",
                        chunk_index, total_chunks, len(text), attempt, MAX_CHUNK_RETRIES)
            response = _SESSION.post(url, json=payload, timeout=20)

            # Success
            if response.ok:
                data = response.json()
                if data.get("ok", False):
                    return data.get("result", {}).get("message_id")

            # Handle 429 Too Many Requests
            if response.status_code == 429:
                retry_after = 3.0
                try:
                    retry_after = float(response.json().get("parameters", {}).get("retry_after", 3.0))
                except Exception:
                    pass
                logger.warning("Rate-limited by Telegram (429). Sleeping %0.1fs before retry...", retry_after)
                time.sleep(retry_after)
                continue

            # Non-retryable 4xx client errors (400 Bad Request, 403 Forbidden, 404 Not Found)
            if 400 <= response.status_code < 500:
                raise RuntimeError(
                    f"Telegram client error ({response.status_code}): {response.text}"
                )

            # Server errors (5xx)
            logger.warning("Telegram returned server error %d. Retrying in %0.1fs...", response.status_code, backoff)
            time.sleep(backoff)
            backoff *= 2

        except requests.exceptions.RequestException as exc:
            # Handles WinError 10054, connection drops, and timeouts
            if attempt == MAX_CHUNK_RETRIES:
                logger.error("Network failure on chunk %d/%d after %d attempts: %s",
                             chunk_index, total_chunks, attempt, exc)
                raise RuntimeError(
                    f"Network delivery failed after {MAX_CHUNK_RETRIES} attempts: {exc}"
                ) from exc

            logger.warning("Network blip on chunk %d/%d (attempt %d/%d): %s. Reconnecting in %0.1fs...",
                           chunk_index, total_chunks, attempt, MAX_CHUNK_RETRIES, exc, backoff)
            time.sleep(backoff)
            backoff *= 2

    raise RuntimeError(f"Failed to deliver chunk {chunk_index}/{total_chunks} after {MAX_CHUNK_RETRIES} retries.")


def send_chunks(
    bot_token: str,
    chat_id: str,
    chunks: List[Tuple[str, List[Dict[str, Any]]]],
) -> List[int]:
    """Deliver an ordered sequence of message chunks with atomic rollback on failure.

    Args:
        bot_token: Secret bot authentication token.
        chat_id: Target chat or channel identifier.
        chunks: Ordered list of (text, entities) tuples from the formatter.

    Returns:
        List of message_ids successfully created in Telegram.

    Raises:
        RuntimeError: If delivery fails. All partially sent messages will be rolled back.
    """
    total = len(chunks)
    sent_message_ids: List[int] = []

    try:
        for i, (text, entities) in enumerate(chunks, 1):
            msg_id = send_message_with_retry(
                bot_token=bot_token,
                chat_id=chat_id,
                text=text,
                entities=entities,
                chunk_index=i,
                total_chunks=total,
            )
            sent_message_ids.append(msg_id)

            # Conservative rate-limit pacing between chunks
            if i < total:
                time.sleep(1.2)

        return sent_message_ids

    except Exception as exc:
        # ATOMIC ALL-OR-NOTHING ROLLBACK:
        # If any chunk fails midway, clean up everything sent so far
        if sent_message_ids:
            logger.error("Delivery aborted at chunk %d/%d. Initiating atomic rollback of %d sent chunks.",
                         len(sent_message_ids) + 1, total, len(sent_message_ids))
            delete_messages(bot_token, chat_id, sent_message_ids)
        raise RuntimeError(
            f"Atomic delivery aborted: chunk {len(sent_message_ids) + 1}/{total} failed. "
            f"All {len(sent_message_ids)} prior chunks were rolled back from the chat."
        ) from exc
