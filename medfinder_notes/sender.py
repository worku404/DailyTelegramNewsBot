"""Telegram document delivery client for MedFinder study notes."""

from __future__ import annotations

import logging
from pathlib import Path
import time
from typing import Any, Optional

import requests

from medfinder_notes.state import extract_markdown_title, extract_note_number

logger = logging.getLogger("medfinder_notes.sender")

TELEGRAM_CAPTION_LIMIT = 1024
UPLOAD_TIMEOUT_SECONDS = 45
MAX_RETRIES = 4
INITIAL_RETRY_BACKOFF_SECONDS = 2.0
TRANSIENT_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})


def format_caption(
    filename: str,
    metadata: Optional[dict[str, Any]] = None,
    file_path: Optional[Path] = None,
) -> str:
    """Format the Telegram document caption.

    Format:
    - PR-generated note: ``Note #15 — <Title> (PR #7 by @author)``
    - Backlog note:      ``Note #04 — <Title>``
    """
    meta = metadata or {}
    note_num = extract_note_number(filename)
    num_label = f"#{note_num:02d}" if note_num is not None else filename

    title = str(meta.get("title") or "").strip()
    if not title and file_path is not None:
        title = extract_markdown_title(file_path)
    if not title:
        title = Path(filename).stem

    pr_number = meta.get("pr_number")
    pr_author = meta.get("pr_author")

    if pr_number is not None and pr_author:
        caption = f"Note {num_label} — {title} (PR #{pr_number} by @{pr_author})"
    else:
        caption = f"Note {num_label} — {title}"

    if len(caption) > TELEGRAM_CAPTION_LIMIT:
        caption = caption[: TELEGRAM_CAPTION_LIMIT - 3].rstrip() + "..."

    return caption


def send_telegram_document(
    bot_token: str,
    chat_id: str,
    file_path: Path,
    caption: str = "",
    thread_id: Optional[int] = None,
    max_retries: int = MAX_RETRIES,
    initial_backoff: float = INITIAL_RETRY_BACKOFF_SECONDS,
) -> None:
    """Deliver a Markdown file to Telegram via the Bot API sendDocument endpoint.

    Automatically retries transient network/SSL timeouts and HTTP 429/5xx
    responses with exponential backoff. Non-transient 4xx errors fail fast.

    Args:
        bot_token: Telegram bot token.
        chat_id: Target supergroup / channel chat ID.
        file_path: Local path to the ``.md`` file to upload.
        caption: Optional caption shown below the document.
        thread_id: Optional topic thread ID (``message_thread_id``).
                   When set, the document is delivered into that specific
                   topic instead of the General topic.
        max_retries: Maximum number of upload attempts on transient errors.
        initial_backoff: Initial delay in seconds before the first retry.

    Raises:
        FileNotFoundError: If ``file_path`` does not exist.
        RuntimeError: If Telegram returns an HTTP error or ``ok: false``.
    """
    if not file_path.is_file():
        raise FileNotFoundError(f"Note file not found: {file_path}")

    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    data: dict[str, str] = {"chat_id": chat_id}
    if caption:
        data["caption"] = caption
    if thread_id is not None:
        data["message_thread_id"] = str(thread_id)

    backoff = initial_backoff
    for attempt in range(1, max_retries + 1):
        try:
            with file_path.open("rb") as doc:
                response = requests.post(
                    url,
                    data=data,
                    files={"document": (file_path.name, doc, "text/markdown")},
                    timeout=UPLOAD_TIMEOUT_SECONDS,
                )
        except (
            requests.exceptions.Timeout,
            requests.exceptions.SSLError,
            requests.exceptions.ConnectionError,
        ) as exc:
            if attempt >= max_retries:
                raise
            logger.warning(
                "Telegram upload of %s failed (%s) on attempt %d/%d. Retrying in %.1fs...",
                file_path.name,
                type(exc).__name__,
                attempt,
                max_retries,
                backoff,
            )
            time.sleep(backoff)
            backoff *= 2
            continue

        if response.status_code in TRANSIENT_STATUS_CODES and attempt < max_retries:
            retry_delay = backoff
            if response.status_code == 429:
                try:
                    retry_after = response.json().get("parameters", {}).get("retry_after")
                    if isinstance(retry_after, (int, float)) and retry_after > 0:
                        retry_delay = float(retry_after)
                except ValueError:
                    pass
            logger.warning(
                "Telegram API returned HTTP %d for %s (attempt %d/%d). Retrying in %.1fs...",
                response.status_code,
                file_path.name,
                attempt,
                max_retries,
                retry_delay,
            )
            time.sleep(retry_delay)
            backoff *= 2
            continue

        try:
            payload = response.json()
        except ValueError:
            payload = {}

        if not response.ok or not payload.get("ok", False):
            raise RuntimeError(
                f"Telegram API delivery failed ({response.status_code}): {response.text}"
            )
        return
