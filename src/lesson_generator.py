"""Gemini LLM client for structured micro-lesson generation.

Encapsulates generation using the unified Google GenAI SDK (google-genai) and
structured output schemas.

Design Decisions & Invariants:
- Single Source of Truth (SSOT): API keys and model names are imported exclusively
  from config.py with no local fallbacks.
- Fail-Fast Execution: Redundant exception wrapping and silent error recovery
  are deliberately omitted. Network, auth, or schema validation failures
  propagate directly to the caller with full stack traces.
- Structured Response: Configured with response_mime_type='application/json' and
  response_schema=LESSON_SCHEMA to enforce reliable JSON extraction without
  probabilistic parsing heuristics.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from google import genai
from google.genai import types

from src.config import GEMINI_API_KEYS, GEMINI_MODEL_NAME
from src.prompts import LESSON_SCHEMA

logger = logging.getLogger("telegram_micro_lesson_bot.llm")

GEMINI_TEMPERATURE = 0.2
MAX_ROUNDS = 2
INITIAL_BACKOFF_SECONDS = 3.0

_FENCE_OPEN = re.compile(r"^```(?:json)?\s*", re.IGNORECASE)
_FENCE_CLOSE = re.compile(r"\s*```$")


def _strip_fences(text: str) -> str:
    """Strip optional Markdown code fences in case the model wraps JSON output."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = _FENCE_OPEN.sub("", cleaned)
        cleaned = _FENCE_CLOSE.sub("", cleaned)
        cleaned = cleaned.strip()
    return cleaned


def _repair_double_escaping(value: str) -> str:
    """Repair double-escaped control characters emitted by the model.

    Under response_mime_type='application/json', Gemini occasionally emits
    double-escaped sequences (e.g. the two literal characters ``\\`` + ``n``
    instead of a real line feed). json.loads() faithfully decodes those into
    literal ``\\n`` text, which downstream breaks CommonMark fenced code blocks
    (a fence must start on a real newline) and surfaces as visible ``\\n`` in
    Telegram.

    Guarded on purpose: the repair only runs when a field carries literal
    escape sequences AND lacks the corresponding real control character. This
    avoids corrupting a lesson whose *content* legitimately contains the text
    ``\\n`` (e.g. a regex, a Windows path, or a lesson about escape sequences)
    where real newlines are already present.

    A per-sequence str.replace is used rather than codecs 'unicode_escape'
    because the latter is latin-1 based and would mangle multibyte UTF-8 such
    as the emoji used elsewhere in the pipeline.
    """
    if not isinstance(value, str):
        return value

    repaired = value
    # Repair only the sequence that is double-escaped without its real counterpart,
    # so a field already containing real newlines/tabs is left untouched.
    if "\\n" in repaired and "\n" not in repaired:
        repaired = repaired.replace("\\n", "\n")
    if "\\t" in repaired and "\t" not in repaired:
        repaired = repaired.replace("\\t", "\t")
    if "\\r" in repaired and "\r" not in repaired:
        repaired = repaired.replace("\\r", "\r")
    return repaired


def _repair_lesson_fields(lesson: dict[str, Any]) -> dict[str, Any]:
    """Apply the guarded double-escape repair to every string field in-place.

    Repairing at this decode boundary (rather than in the presentation layer)
    fixes the defect once for all consumers of the lesson dict, not just the
    explanation body.
    """
    for key, value in lesson.items():
        if isinstance(value, str):
            repaired = _repair_double_escaping(value)
            if repaired != value:
                logger.warning(
                    "Repaired double-escaped sequence in lesson field '%s'.", key
                )
                lesson[key] = repaired
    return lesson


def generate_lesson(
    prompt: str,
    api_keys: list[str] | None = None,
    max_retries: int = MAX_ROUNDS,
    initial_backoff: float = INITIAL_BACKOFF_SECONDS,
) -> dict[str, Any]:
    """Generate a structured software engineering micro-lesson with multi-key failover rotation.

    Rotates across configured Gemini API keys upon encountering rate limits, quota exhaustion,
    or transient errors.

    Args:
        prompt: Formatted prompt string specifying the topic and rules.
        api_keys: Optional list of Gemini API keys. Defaults to GEMINI_API_KEYS.
        max_retries: Number of retry rounds across all keys before raising RuntimeError.
        initial_backoff: Delay in seconds when backing off between retry rounds.

    Returns:
        A dictionary conforming to LESSON_SCHEMA (title, concept_summary,
        explanation, key_takeaway, image_prompt).

    Raises:
        RuntimeError: If Gemini fails after exhausting all keys across all retry rounds.
    """
    active_keys = list(api_keys if api_keys is not None else GEMINI_API_KEYS)

    last_error: Exception | None = None
    total_keys = len(active_keys)

    for round_idx in range(1, max_retries + 1):
        for key_idx, key in enumerate(active_keys, start=1):
            key_label = f"key {key_idx}/{total_keys} (round {round_idx}/{max_retries})"
            logger.info("Requesting structured lesson from Gemini using %s...", key_label)

            try:
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model=GEMINI_MODEL_NAME,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=GEMINI_TEMPERATURE,
                        response_mime_type="application/json",
                        response_schema=LESSON_SCHEMA,
                    ),
                )

                raw_text = getattr(response, "text", "")
                if not raw_text:
                    raise RuntimeError("Gemini returned an empty response.")

                lesson = json.loads(_strip_fences(raw_text))
                logger.info("Gemini lesson generation succeeded using %s.", key_label)
                return _repair_lesson_fields(lesson)

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Gemini request failed on %s (%s). Failing over to next key...",
                    key_label,
                    exc,
                )

        if round_idx < max_retries:
            wait_time = initial_backoff * (2 ** (round_idx - 1))
            logger.info(
                "Completed round %d across all Gemini keys. Retrying in %.1fs...",
                round_idx,
                wait_time,
            )
            time.sleep(wait_time)

    raise RuntimeError(
        f"Gemini lesson generation failed after {max_retries} rounds across {total_keys} keys: {last_error}"
    ) from last_error
