"""Validates candidate URLs to guarantee zero dead links in published lessons.

Probes candidate reference URLs with realistic User-Agent headers, fast timeouts,
and automatic HEAD/GET fallback to verify HTTP 200..399 status.
"""

from __future__ import annotations

import logging
from typing import Sequence
import requests

logger = logging.getLogger("telegram_micro_lesson_bot.url_validator")

DEFAULT_REQUEST_TIMEOUT = 3.0
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def is_url_valid(url: str, timeout: float = DEFAULT_REQUEST_TIMEOUT) -> bool:
    """Check if a URL responds with a successful status code (200-399).

    Tries HTTP HEAD first for efficiency; falls back to a stream-limited GET
    if the server rejects HEAD with 403 or 405.
    """
    if not url or not isinstance(url, str):
        return False

    trimmed = url.strip()
    if not trimmed.startswith(("http://", "https://")):
        return False

    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.head(
            trimmed,
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
        )
        if 200 <= resp.status_code < 400:
            return True

        # Many doc hosts (e.g. Cloudflare, Oracle) forbid HEAD; retry with stream GET
        if resp.status_code in (403, 405):
            get_resp = requests.get(
                trimmed,
                headers=headers,
                timeout=timeout,
                allow_redirects=True,
                stream=True,
            )
            return 200 <= get_resp.status_code < 400

        return False
    except Exception as exc:
        logger.debug("URL validation probe failed for '%s': %s", trimmed, exc)
        return False


def find_first_valid_url(
    urls: Sequence[str],
    timeout: float = DEFAULT_REQUEST_TIMEOUT,
) -> str | None:
    """Iterate through candidate URLs and return the first reachable one.

    Breaks immediately once a valid URL is discovered. If all candidates fail
    or timeout, returns None so dead links are omitted.
    """
    for url in urls:
        if not isinstance(url, str):
            continue
        cleaned = url.strip()
        if not cleaned:
            continue

        logger.info("Validating candidate reference URL: %s", cleaned)
        if is_url_valid(cleaned, timeout=timeout):
            logger.info("Candidate reference URL verified: %s", cleaned)
            return cleaned
        logger.warning("Candidate reference URL failed validation (dead/unreachable): %s", cleaned)

    logger.warning("All %d candidate reference URLs failed validation.", len(urls))
    return None
