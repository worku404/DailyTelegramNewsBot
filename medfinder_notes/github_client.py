"""GitHub REST API client for reading Pull Requests and filtered diffs.

Designed for the public worku404/MedFinder-java repository, with optional
GITHUB_TOKEN authentication for higher GitHub Actions rate limits.

File filtering policy:
- Java files are included ONLY when located under ``src/main/``.
- All test files (``src/test/``) are completely excluded.
- Key build/config files (``pom.xml``, ``config/config.properties.example``,
  ``src/main/resources/ai/system-prompt.txt``) are included when modified.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
import time
from typing import Any, Optional

import requests

from medfinder_notes.config import MAX_DIFF_CHARS

logger = logging.getLogger("medfinder_notes.github_client")

GITHUB_API_BASE = "https://api.github.com"
REQUEST_TIMEOUT_SECONDS = 45
MAX_RETRIES = 4
INITIAL_RETRY_BACKOFF_SECONDS = 2.0
TRANSIENT_STATUS_CODES: frozenset[int] = frozenset({500, 502, 503, 504})

EXACT_INCLUDED_FILES: frozenset[str] = frozenset(
    {
        "pom.xml",
        "config/config.properties.example",
        "src/main/resources/ai/system-prompt.txt",
    }
)


@dataclass(frozen=True)
class PullRequestInfo:
    """Normalized metadata for a GitHub Pull Request."""

    number: int
    title: str
    author: str
    state: str
    merged_at: Optional[str]
    html_url: str
    head_sha: str


@dataclass(frozen=True)
class PrFileChange:
    """Normalized diff record for a single file changed in a Pull Request."""

    filename: str
    status: str
    additions: int
    deletions: int
    patch: str


def _build_headers(github_token: Optional[str] = None) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "DailyTelegramNewsBot-MedFinderNotes",
    }
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    return headers


def _get_with_retry(
    url: str,
    headers: dict[str, str],
    params: Optional[dict[str, Any]] = None,
    timeout: int = REQUEST_TIMEOUT_SECONDS,
    max_retries: int = MAX_RETRIES,
    initial_backoff: float = INITIAL_RETRY_BACKOFF_SECONDS,
) -> requests.Response:
    """Perform a GitHub GET request with automatic retry on transient network/SSL errors."""
    last_exc: Optional[Exception] = None
    backoff = initial_backoff

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=timeout,
            )
            if response.status_code in TRANSIENT_STATUS_CODES and attempt < max_retries:
                logger.warning(
                    "GitHub API returned HTTP %d for %s (attempt %d/%d). Retrying in %.1fs...",
                    response.status_code,
                    url,
                    attempt,
                    max_retries,
                    backoff,
                )
                time.sleep(backoff)
                backoff *= 2
                continue
            return response
        except (
            requests.exceptions.Timeout,
            requests.exceptions.SSLError,
            requests.exceptions.ConnectionError,
        ) as exc:
            last_exc = exc
            if attempt >= max_retries:
                raise
            logger.warning(
                "GitHub request failed (%s) on attempt %d/%d. Retrying in %.1fs...",
                type(exc).__name__,
                attempt,
                max_retries,
                backoff,
            )
            time.sleep(backoff)
            backoff *= 2

    raise RuntimeError(f"GitHub request failed after {max_retries} attempts: {last_exc}")


def _parse_pr(raw: dict[str, Any]) -> PullRequestInfo:
    return PullRequestInfo(
        number=int(raw["number"]),
        title=str(raw.get("title") or "").strip(),
        author=str((raw.get("user") or {}).get("login") or "unknown"),
        state=str(raw.get("state") or ""),
        merged_at=raw.get("merged_at"),
        html_url=str(raw.get("html_url") or ""),
        head_sha=str((raw.get("head") or {}).get("sha") or ""),
    )


def is_relevant_file(filename: str) -> bool:
    """Return True if a PR file path should be sent to Gemini for note analysis.

    Java files are strictly limited to ``src/main/``. Test folders (``src/test/``)
    are completely excluded.
    """
    normalized = filename.replace("\\", "/").lstrip("./")

    if normalized.startswith("src/test/") or "/test/" in f"/{normalized}":
        return False

    if normalized in EXACT_INCLUDED_FILES:
        return True

    if normalized.startswith("src/main/") and normalized.endswith(".java"):
        return True

    return False


def is_eligible_pr(pr: PullRequestInfo, trigger_mode: str = "merged") -> bool:
    """Return True if a PR qualifies under the configured trigger mode."""
    if trigger_mode == "merged":
        return bool(pr.merged_at)
    if trigger_mode == "all":
        return True
    raise ValueError(
        f"Invalid PR_TRIGGER_MODE {trigger_mode!r}; expected 'merged' or 'all'."
    )


def fetch_pull_requests(
    owner: str,
    repo: str,
    github_token: Optional[str] = None,
) -> list[PullRequestInfo]:
    """Fetch all Pull Requests (state=all) sorted by PR number ascending."""
    headers = _build_headers(github_token)
    prs: list[PullRequestInfo] = []
    page = 1

    while True:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls"
        response = _get_with_retry(
            url,
            headers=headers,
            params={
                "state": "all",
                "sort": "created",
                "direction": "asc",
                "per_page": 100,
                "page": page,
            },
        )
        if not response.ok:
            raise RuntimeError(
                f"GitHub API error fetching PRs ({response.status_code}): {response.text}"
            )

        batch = response.json()
        if not batch:
            break

        prs.extend(_parse_pr(item) for item in batch)
        if len(batch) < 100:
            break
        page += 1

    prs.sort(key=lambda item: item.number)
    return prs


def fetch_pull_request(
    owner: str,
    repo: str,
    pr_number: int,
    github_token: Optional[str] = None,
) -> PullRequestInfo:
    """Fetch a single Pull Request by number."""
    headers = _build_headers(github_token)
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}"
    response = _get_with_retry(url, headers=headers)
    if not response.ok:
        raise RuntimeError(
            f"GitHub API error fetching PR #{pr_number} ({response.status_code}): {response.text}"
        )
    return _parse_pr(response.json())


def fetch_pr_relevant_files(
    owner: str,
    repo: str,
    pr_number: int,
    github_token: Optional[str] = None,
) -> list[PrFileChange]:
    """Fetch changed files for a PR, filtered strictly to relevant src/main/ & config files."""
    headers = _build_headers(github_token)
    relevant: list[PrFileChange] = []
    page = 1

    while True:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        response = _get_with_retry(
            url,
            headers=headers,
            params={"per_page": 100, "page": page},
        )
        if not response.ok:
            raise RuntimeError(
                f"GitHub API error fetching files for PR #{pr_number} "
                f"({response.status_code}): {response.text}"
            )

        batch = response.json()
        if not batch:
            break

        for item in batch:
            filename = str(item.get("filename") or "")
            if not is_relevant_file(filename):
                continue
            status = str(item.get("status") or "modified")
            if status == "removed":
                continue
            relevant.append(
                PrFileChange(
                    filename=filename,
                    status=status,
                    additions=int(item.get("additions") or 0),
                    deletions=int(item.get("deletions") or 0),
                    patch=str(item.get("patch") or ""),
                )
            )

        if len(batch) < 100:
            break
        page += 1

    return relevant


def format_diff_for_prompt(
    files: list[PrFileChange],
    max_chars: int = MAX_DIFF_CHARS,
) -> str:
    """Serialize relevant PR file diffs into a bounded prompt string."""
    if not files:
        return ""

    sections: list[str] = []
    total_len = 0

    for change in files:
        patch_body = change.patch.strip() or "(patch omitted by GitHub API — file too large or binary)"
        block = (
            f"=== FILE: {change.filename} "
            f"(status={change.status}, +{change.additions}/-{change.deletions}) ===\n"
            f"{patch_body}\n"
        )

        if total_len + len(block) > max_chars:
            remaining = max_chars - total_len
            if remaining > 200:
                sections.append(
                    block[: remaining - 60]
                    + f"\n... [diff truncated at {max_chars} chars total] ...\n"
                )
            else:
                sections.append(f"... [remaining files truncated at {max_chars} chars total] ...\n")
            break

        sections.append(block)
        total_len += len(block)

    return "\n".join(sections)
