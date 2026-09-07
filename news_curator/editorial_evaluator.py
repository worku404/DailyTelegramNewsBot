"""Evaluates candidate article batches using Gemini and stream-specific rubrics.

Employs Google GenAI structured outputs and API key failover rotation to select
top high-signal engineering stories for review, with explicit logging of data sent.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, List

from google import genai
from google.genai import types

from news_curator.config import GEMINI_API_KEYS, GEMINI_MODEL_NAME, MAX_STORIES_PER_STREAM
from news_curator.prompts import CURATION_RESPONSE_SCHEMA, STREAM_PROMPTS
from news_curator.rss_fetcher import CandidateArticle
from src.lesson_generator import _strip_fences, _repair_lesson_fields

logger = logging.getLogger("news_curator.evaluator")

EVALUATOR_TEMPERATURE = 0.25
MAX_ROUNDS = 2
INITIAL_BACKOFF_SECONDS = 3.0


def _format_candidates_payload(candidates: List[CandidateArticle]) -> str:
    """Format candidate articles into a structured text prompt for the LLM."""
    lines = ["Here are the candidate engineering articles published in the last 48 hours:\n"]
    for i, item in enumerate(candidates, start=1):
        lines.append(
            f"Candidate #{i}:\n"
            f"- Title: {item.title}\n"
            f"- Source: {item.source_name}\n"
            f"- Author: {item.author}\n"
            f"- URL: {item.url}\n"
            f"- Summary: {item.summary}\n"
        )
    lines.append(
        "Evaluate these candidates according to your system prompt rules. "
        f"Select at most {MAX_STORIES_PER_STREAM} of the highest signal engineering stories. "
        "If none meet your quality bar, return an empty selected_stories array."
    )
    return "\n".join(lines)


def evaluate_stream_candidates(
    stream_id: int,
    stream_name: str,
    candidates: List[CandidateArticle],
    api_keys: List[str] | None = None,
) -> List[dict[str, Any]]:
    """Evaluate candidate articles for a given stream and return curated selections.

    Args:
        stream_id: Editorial stream identifier (1 or 2).
        stream_name: Display name of the stream category.
        candidates: List of fresh CandidateArticle objects.
        api_keys: Optional override for Gemini API keys.

    Returns:
        List of dicts representing curated stories conforming to CURATION_RESPONSE_SCHEMA.
    """
    if not candidates:
        logger.info("No fresh candidate articles to evaluate for Stream %d (%s).", stream_id, stream_name)
        return []

    system_instruction = STREAM_PROMPTS.get(stream_id)
    if not system_instruction:
        raise ValueError(f"No system prompt registered for Stream {stream_id}")

    prompt_content = _format_candidates_payload(candidates)

    active_keys = list(api_keys if api_keys is not None else GEMINI_API_KEYS)
    total_keys = len(active_keys)
    last_error: Exception | None = None

    for round_idx in range(1, MAX_ROUNDS + 1):
        for key_idx, key in enumerate(active_keys, start=1):
            key_label = f"key {key_idx}/{total_keys} (round {round_idx}/{MAX_ROUNDS})"
            logger.info("Requesting Stream %d evaluation from Gemini using %s...", stream_id, key_label)

            try:
                client = genai.Client(api_key=key)
                response = client.models.generate_content(
                    model=GEMINI_MODEL_NAME,
                    contents=prompt_content,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=EVALUATOR_TEMPERATURE,
                        response_mime_type="application/json",
                        response_schema=CURATION_RESPONSE_SCHEMA,
                    ),
                )

                raw_text = getattr(response, "text", "")
                if not raw_text:
                    raise RuntimeError("Gemini returned empty response for editorial curation.")

                payload = json.loads(_strip_fences(raw_text))
                raw_stories = payload.get("selected_stories", [])
                logger.info(
                    "Gemini selected %d story/stories for Stream %d (%s) using %s.",
                    len(raw_stories),
                    stream_id,
                    stream_name,
                    key_label,
                )

                # Repair any double-escaping in string fields
                repaired_stories = []
                for story in raw_stories[:MAX_STORIES_PER_STREAM]:
                    repaired_stories.append(_repair_lesson_fields(story))

                return repaired_stories

            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Gemini evaluation failed on %s (%s). Failing over to next key...",
                    key_label,
                    exc,
                )

        if round_idx < MAX_ROUNDS:
            wait_time = INITIAL_BACKOFF_SECONDS * (2 ** (round_idx - 1))
            time.sleep(wait_time)

    raise RuntimeError(
        f"Editorial evaluation for Stream {stream_id} failed after {MAX_ROUNDS} rounds across {total_keys} keys: {last_error}"
    ) from last_error
