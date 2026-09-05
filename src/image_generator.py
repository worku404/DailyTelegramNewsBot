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

from src.config import HF_IMAGE_TOKEN
from src.prompts import IMAGE_NEGATIVE_PROMPT, IMAGE_STYLE_CONSTRAINTS

logger = logging.getLogger("telegram_micro_lesson_bot.image")

HF_MODEL = "stabilityai/stable-diffusion-3-medium-diffusers"
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{HF_MODEL}"

MAX_RETRIES = 3
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
    max_retries: int = MAX_RETRIES,
    initial_backoff: float = INITIAL_BACKOFF_SECONDS,
) -> bytes:
    """Generate a technical concept illustration for a structured lesson with automatic retry.

    Retries transient errors (503 model loading, 429 rate limit, 5xx gateway errors,
    network drops) using exponential backoff or the server's estimated warmup time.

    Args:
        lesson: Gemini lesson payload containing an internal ``image_prompt``.
        max_retries: Maximum number of generation attempts before raising RuntimeError.
        initial_backoff: Base delay in seconds before the first retry.

    Returns:
        Raw image bytes ready for Telegram multipart upload.

    Raises:
        RuntimeError: If Hugging Face fails after exhausting all retry attempts.
    """
    prompt, negative_prompt = build_image_prompt(lesson)
    headers = {
        "Authorization": f"Bearer {HF_IMAGE_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "negative_prompt": negative_prompt,
            "guidance_scale": 5.0,  # SD3 Medium: >7 warps/deep-fries any text
            "num_inference_steps": 30,
        },
    }

    last_error_message = ""
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Requesting image from Hugging Face (attempt %d/%d)...", attempt, max_retries)
            response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)

            if response.status_code == 200:
                logger.info("Hugging Face image generation prompt: %s", prompt)
                return response.content

            # Calculate backoff delay; honor server's estimated warmup time if provided
            wait_time = initial_backoff * (2 ** (attempt - 1))
            if response.status_code == 503:
                try:
                    data = response.json()
                    estimated = float(data.get("estimated_time", 0))
                    if estimated > 0:
                        wait_time = min(estimated + 2.0, 30.0)
                except Exception:
                    pass

            last_error_message = f"HTTP {response.status_code}: {response.text}"
            logger.warning(
                "Hugging Face attempt %d/%d failed (%s). Retrying in %.1fs...",
                attempt,
                max_retries,
                last_error_message,
                wait_time,
            )

            # Only retry on transient server or rate-limit codes
            if response.status_code not in (429, 500, 502, 503, 504):
                break

            if attempt < max_retries:
                time.sleep(wait_time)

        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error_message = f"Network error: {exc}"
            wait_time = initial_backoff * (2 ** (attempt - 1))
            logger.warning(
                "Hugging Face network error on attempt %d/%d (%s). Retrying in %.1fs...",
                attempt,
                max_retries,
                exc,
                wait_time,
            )
            if attempt < max_retries:
                time.sleep(wait_time)

    raise RuntimeError(
        f"Hugging Face image generation failed after {max_retries} attempts: {last_error_message}"
    )
