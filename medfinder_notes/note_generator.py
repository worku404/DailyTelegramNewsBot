"""Gemini LLM client for generating MedFinder OOP study notes from PR diffs.

Uses the unified Google GenAI SDK (google-genai) with:
- Structured JSON output (NOTES_RESPONSE_SCHEMA) returning 0..N notes per PR
- Multi-key failover rotation with exponential backoff
- Guarded double-escape newline repair for clean Markdown rendering
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import re
import time
from typing import Any, Optional

from google import genai
from google.genai import types

from medfinder_notes.config import MAX_NOTES_PER_PR, get_gemini_config
from medfinder_notes.github_client import PullRequestInfo
from medfinder_notes.prompts import NOTES_RESPONSE_SCHEMA, build_pr_notes_prompt

logger = logging.getLogger("medfinder_notes.generator")

GEMINI_TEMPERATURE = 0.25
MAX_ROUNDS = 3
INITIAL_BACKOFF_SECONDS = 3.0
HTTP_TIMEOUT_MS = 60_000
MAX_SLUG_LENGTH = 60

_FENCE_OPEN = re.compile(r"^```(?:json)?\s*", re.IGNORECASE)
_FENCE_CLOSE = re.compile(r"\s*```$")
_NON_SLUG_CHARS = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class GeneratedNote:
    """Validated Markdown study note produced by Gemini."""

    slug: str
    title: str
    chapter_refs: list[str]
    markdown_content: str


def _strip_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = _FENCE_OPEN.sub("", cleaned)
        cleaned = _FENCE_CLOSE.sub("", cleaned)
        cleaned = cleaned.strip()
    return cleaned


def _repair_double_escaping(value: str) -> str:
    """Repair double-escaped control characters only when real ones are absent."""
    if not isinstance(value, str):
        return value

    repaired = value
    if "\\n" in repaired and "\n" not in repaired:
        repaired = repaired.replace("\\n", "\n")
    if "\\t" in repaired and "\t" not in repaired:
        repaired = repaired.replace("\\t", "\t")
    if "\\r" in repaired and "\r" not in repaired:
        repaired = repaired.replace("\\r", "\r")
    return repaired


def sanitize_slug(raw_slug: str, fallback_title: str = "") -> str:
    """Normalize a note slug into safe lowercase kebab-case without leading digits."""
    candidate = raw_slug.strip().lower()
    if candidate.endswith(".md"):
        candidate = candidate[:-3]
    candidate = re.sub(r"^\d+[-_\s]*", "", candidate)
    candidate = _NON_SLUG_CHARS.sub("-", candidate).strip("-")

    if not candidate and fallback_title:
        candidate = _NON_SLUG_CHARS.sub("-", fallback_title.lower()).strip("-")
        candidate = re.sub(r"^\d+[-_\s]*", "", candidate)

    if not candidate:
        candidate = "oop-concept"

    return candidate[:MAX_SLUG_LENGTH].rstrip("-")


def _parse_notes_payload(payload: dict[str, Any], max_notes: int) -> list[GeneratedNote]:
    raw_notes = payload.get("notes")
    if not isinstance(raw_notes, list):
        raise ValueError("Gemini response JSON missing 'notes' list.")

    parsed: list[GeneratedNote] = []
    used_slugs: set[str] = set()

    for entry in raw_notes[:max_notes]:
        if not isinstance(entry, dict):
            continue

        title = _repair_double_escaping(str(entry.get("title") or "")).strip()
        markdown = _repair_double_escaping(str(entry.get("markdown_content") or "")).strip()
        if not title or not markdown:
            continue

        base_slug = sanitize_slug(str(entry.get("slug") or ""), fallback_title=title)
        slug = base_slug
        suffix = 2
        while slug in used_slugs:
            slug = f"{base_slug[: MAX_SLUG_LENGTH - 4]}-{suffix}"
            suffix += 1
        used_slugs.add(slug)

        raw_refs = entry.get("chapter_refs") or []
        chapter_refs = [
            _repair_double_escaping(str(ref)).strip()
            for ref in raw_refs
            if str(ref).strip()
        ]

        parsed.append(
            GeneratedNote(
                slug=slug,
                title=title,
                chapter_refs=chapter_refs,
                markdown_content=markdown + "\n",
            )
        )

    return parsed


def generate_notes_for_pr(
    pr: PullRequestInfo,
    diff_text: str,
    topics_text: str,
    existing_titles: list[str],
    max_notes: int = MAX_NOTES_PER_PR,
    api_keys: Optional[list[str]] = None,
    model_name: Optional[str] = None,
    max_retries: int = MAX_ROUNDS,
    initial_backoff: float = INITIAL_BACKOFF_SECONDS,
) -> list[GeneratedNote]:
    """Call Gemini with multi-key failover to generate 0..max_notes study notes."""
    if not diff_text.strip():
        return []

    if api_keys is None or model_name is None:
        cfg_keys, cfg_model = get_gemini_config()
        api_keys = api_keys if api_keys is not None else cfg_keys
        model_name = model_name if model_name is not None else cfg_model

    prompt = build_pr_notes_prompt(
        pr=pr,
        diff_text=diff_text,
        topics_text=topics_text,
        existing_titles=existing_titles,
        max_notes=max_notes,
    )

    last_error: Optional[Exception] = None
    total_keys = len(api_keys)

    for round_idx in range(1, max_retries + 1):
        for key_idx, key in enumerate(api_keys, start=1):
            key_label = f"key {key_idx}/{total_keys} (round {round_idx}/{max_retries})"
            logger.info(
                "Requesting study notes for PR #%d from Gemini (%s)...",
                pr.number,
                key_label,
            )

            try:
                client = genai.Client(
                    api_key=key,
                    http_options=types.HttpOptions(timeout=HTTP_TIMEOUT_MS),
                )
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=GEMINI_TEMPERATURE,
                        response_mime_type="application/json",
                        response_schema=NOTES_RESPONSE_SCHEMA,
                    ),
                )

                raw_text = getattr(response, "text", "") or ""
                if not raw_text.strip():
                    raise RuntimeError("Gemini returned an empty response.")

                payload = json.loads(_strip_fences(raw_text))
                notes = _parse_notes_payload(payload, max_notes=max_notes)
                logger.info(
                    "Gemini generated %d note(s) for PR #%d using %s.",
                    len(notes),
                    pr.number,
                    key_label,
                )
                return notes

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Gemini request failed on %s (%s). Failing over to next key...",
                    key_label,
                    exc,
                )

        if round_idx < max_retries:
            wait_seconds = initial_backoff * (2 ** (round_idx - 1))
            logger.info(
                "Completed round %d across all Gemini keys. Retrying in %.1fs...",
                round_idx,
                wait_seconds,
            )
            time.sleep(wait_seconds)

    raise RuntimeError(
        f"Gemini note generation for PR #{pr.number} failed after "
        f"{max_retries} rounds across {total_keys} keys: {last_error}"
    ) from last_error
