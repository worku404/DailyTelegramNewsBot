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

from typing import Any

import requests
import logging
logger = logging.getLogger("telegram_micro_lesson_bot.llm")

from src.config import HF_IMAGE_TOKEN
from src.prompts import IMAGE_NEGATIVE_PROMPT, IMAGE_STYLE_CONSTRAINTS

HF_MODEL = "stabilityai/stable-diffusion-3-medium-diffusers"
HF_API_URL = f"https://router.huggingface.co/hf-inference/models/{HF_MODEL}"




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


def generate_concept_image(lesson: dict[str, Any]) -> bytes:
    """Generate a text-free concept illustration for a structured lesson.

    Args:
        lesson: Gemini lesson payload containing an internal ``image_prompt``.

    Returns:
        Raw image bytes ready for Telegram multipart upload.

    Raises:
        RuntimeError: If Hugging Face responds with a non-200 status.
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

    response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)

    if response.status_code != 200:
        raise RuntimeError(
            f"Hugging Face image generation failed ({response.status_code}): {response.text}"
        )
    logger.info("Hugging Face image generation prompt: %s", prompt)
    return response.content
