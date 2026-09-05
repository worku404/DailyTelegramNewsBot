"""Generate technical concept infographics via Hugging Face Router Inference.

Gemini generates an architectural and conceptual description of the software engineering topic;
this module pairs it with clean technical diagram and vector infographic style constraints
before requesting an image suitable for Telegram delivery.

Design Decisions & Invariants:
- Separation of Concerns: The image provides high-level visual intuition (architecture/flow),
  while Telegram delivers the full detailed technical lesson text and code snippets.
- Concise Technical Labeling: The diffusion model is steered towards architectural flow
  diagrams and concise conceptual labels (e.g. O(1), Memory, Yield), avoiding noisy paragraphs
  or messy photo clutter.
- Stateless Byte Streaming: Image bytes remain in memory, avoiding temporary-file
  cleanup and disk I/O in ephemeral CI/CD environments.
- Fail-Fast Propagation: Upstream API failures raise RuntimeError with the response
  status and body rather than silently degrading the publishing pipeline.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

from src.config import HF_IMAGE_TOKENS
from src.prompts import IMAGE_NEGATIVE_PROMPT, IMAGE_STYLE_CONSTRAINTS

logger = logging.getLogger("telegram_micro_lesson_bot.image")

HF_MODEL = "stabilityai/stable-diffusion-3-medium-diffusers"
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{HF_MODEL}"

MAX_ROUNDS = 2
INITIAL_BACKOFF_SECONDS = 3.0


def build_image_prompt(lesson: dict[str, Any]) -> tuple[str, str]:
    """Build positive and negative prompts from Gemini's internal image prompt description.

    Pairs Gemini's conceptual architecture/diagram description with consistent technical
    vector infographic style constraints and dark-mode aesthetics.

    Args:
        lesson: Structured lesson containing the internal-only ``image_prompt``.

    Returns:
        A tuple of ``(positive_prompt, negative_prompt)``.
    """
    visual_metaphor = str(lesson.get("image_prompt", "")).strip()
    if not visual_metaphor:
        visual_metaphor = (
            "System architecture diagram showing modular software components, "
            "data flow arrows, and high contrast conceptual blocks"
        )

    return f"{visual_metaphor.rstrip('.')}. {IMAGE_STYLE_CONSTRAINTS}", IMAGE_NEGATIVE_PROMPT


def generate_concept_image(
    lesson: dict[str, Any],
    tokens: list[str] | None = None,
    max_retries: int = MAX_ROUNDS,
    initial_backoff: float = INITIAL_BACKOFF_SECONDS,
) -> bytes:
    """Generate a technical concept illustration with multi-token failover rotation.

    Rotates across configured Hugging Face API tokens upon encountering rate limits (429),
    authorization errors (401/403), or transient server/network issues (503/504).

    Args:
        lesson: Gemini lesson payload containing an internal ``image_prompt``.
        tokens: Optional list of HF API tokens for rotation. Defaults to HF_IMAGE_TOKENS.
        max_retries: Number of retry rounds across the token pool before raising RuntimeError.
        initial_backoff: Delay in seconds when backing off between retry rounds.

    Returns:
        Raw image bytes ready for Telegram multipart upload.

    Raises:
        RuntimeError: If all token attempts are exhausted without success.
    """
    active_tokens = list(tokens if tokens is not None else HF_IMAGE_TOKENS)

    prompt, negative_prompt = build_image_prompt(lesson)
    payload = {
        "inputs": prompt,
        "parameters": {
            "negative_prompt": negative_prompt,
            "guidance_scale": 5.0,  # SD3 Medium: >7 warps/deep-fries any text
            "num_inference_steps": 30,
        },
    }

    last_error_message = ""
    total_tokens = len(active_tokens)

    for round_idx in range(1, max_retries + 1):
        for token_idx, token in enumerate(active_tokens, start=1):
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            token_label = f"token {token_idx}/{total_tokens} (round {round_idx}/{max_retries})"
            logger.info("Requesting image from Hugging Face using %s...", token_label)

            try:
                response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)

                if response.status_code == 200:
                    logger.info("Hugging Face image generation succeeded using %s.", token_label)
                    return response.content

                last_error_message = f"HTTP {response.status_code} ({token_label}): {response.text}"

                # On 503 (model loading), honor server's estimated warmup time before failover
                if response.status_code == 503:
                    wait_time = initial_backoff
                    try:
                        data = response.json()
                        estimated = float(data.get("estimated_time", 0))
                        if estimated > 0:
                            wait_time = min(estimated + 2.0, 30.0)
                    except Exception:
                        pass
                    logger.warning(
                        "Model warming up on %s. Waiting %.1fs before token failover...",
                        token_label,
                        wait_time,
                    )
                    time.sleep(wait_time)
                else:
                    logger.warning(
                        "Hugging Face request failed on %s (%s). Failing over to next token...",
                        token_label,
                        last_error_message,
                    )

            except (requests.Timeout, requests.ConnectionError) as exc:
                last_error_message = f"Network error ({token_label}): {exc}"
                logger.warning(
                    "Network error on %s (%s). Failing over to next token...",
                    token_label,
                    exc,
                )

        # Back off before retrying all tokens in the next round
        if round_idx < max_retries:
            wait_time = initial_backoff * (2 ** (round_idx - 1))
            logger.info(
                "Completed round %d across all tokens. Retrying pool in %.1fs...",
                round_idx,
                wait_time,
            )
            time.sleep(wait_time)

    raise RuntimeError(
        f"Hugging Face image generation failed after {max_retries} rounds across {total_tokens} tokens: {last_error_message}"
    )
