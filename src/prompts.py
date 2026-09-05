"""Structured prompt engineering and schema definitions for Gemini micro-lessons.

Defines the system prompt template and the strict JSON schema passed to Gemini
for structured outputs.

Design Decisions & Invariants:
- Dual Contract Alignment: The fields specified in PROMPT_TEMPLATE must mirror
  LESSON_SCHEMA exactly. If a field exists in the JSON schema but is omitted
  from the prompt text, the model may under-populate or hallucinate that field.
- Minimal-Legible-Text Visuals: image_prompt directs Gemini to describe ONE
  clean, abstract technical illustration whose meaning is carried by layout,
  arrows, and color contrast. Diffusion models garble dense text, so the field
  instruction caps in-image text at a couple of short quoted words and forbids
  code, symbols, and identifiers. The instruction is intentionally topic-agnostic:
  it states rules, not per-topic examples, so it works for every seed topic.
- Internal-Only Invariant: image_prompt is consumed strictly by image_generator.py
  and is deliberately filtered out from user-facing Telegram message bodies.
"""

from __future__ import annotations

from typing import Any

PROMPT_TEMPLATE = """You are teaching ONE software engineering concept to an experienced software engineer.
Teach only this topic:

TOPIC: {title}

Rules:
- Audience: Experienced software engineer. Use precise technical terminology, avoid introductory hand-holding, and teach at an intermediate-to-advanced register.
- Code: If code clarifies the invariant or pitfall, include a concise, focused snippet in a fenced Markdown block (e.g. ```python ... ```). Omit code if not needed.
- Anti-hallucination: If you are not confident in a specific detail, omit it rather than speculate.
- Tone: Crisp, practical, and punchy. No generic fluff or boilerplate conversational intros.

Output MUST satisfy these exact fields:
- title: A short, precise name for the concept.
- concept_summary: ONE sentence answering what it is, why it exists, or what problem it solves.
- explanation: The technical core of the lesson. Explain the underlying mechanism, trade-offs, invariants, and common footguns.
- key_takeaway: One memorable line or mental model the reader should retain.
- image_prompt: A visual description for an AI image generator (a diffusion model that cannot render text reliably). Describe ONE clean, abstract technical illustration for THIS concept whose meaning is carried by composition, shapes, directional arrows, and color contrast — not by written words. Text budget: the image may contain at most two short text elements of 1–2 plain words each; write those exact words in double quotes so they render literally, and prefer short, generic words that suit the concept. If the concept has no natural one- or two-word cue, request zero text. Do NOT put code, code syntax, identifiers, function or variable names, memory addresses, hex values, numbers, multi-word callouts, sentences, paragraphs, or more than two text elements in the image. Choose the visual structure that best fits this specific concept (for example a single focal object, a one-vs-many comparison, a flow, or a state change), expressed purely through geometry, arrows, and color.
"""

# image_prompt is an INTERNAL-ONLY field: it is authored by Gemini and consumed
# by image_generator.py to steer the diffusion model. It is deliberately NOT
# rendered into the Telegram message (telegram_formatter.format_lesson reads only
# title/concept_summary/explanation/key_takeaway and ignores extra keys).
LESSON_FIELDS = (
    "title",
    "concept_summary",
    "explanation",
    "key_takeaway",
    "image_prompt",
)

LESSON_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "title": {
            "type": "STRING",
            "description": "Short, specific name for the concept.",
        },
        "concept_summary": {
            "type": "STRING",
            "description": "One sentence answering what it is, why it exists, or what problem it solves.",
        },
        "explanation": {
            "type": "STRING",
            "description": "Technical lesson body with mechanical trade-offs and code examples.",
        },
        "key_takeaway": {
            "type": "STRING",
            "description": "One memorable rule of thumb or invariant to retain.",
        },
        "image_prompt": {
            "type": "STRING",
            "description": "An abstract technical illustration described via composition, shapes, arrows, and color contrast, with at most two short quoted text labels and no code, symbols, or identifiers.",
        },
    },
    "required": list(LESSON_FIELDS),
}


# --- Image generation prompts (consumed by src/image_generator.py) ---
# Kept here so ALL model-facing prompt text lives in a single module.
IMAGE_STYLE_CONSTRAINTS = (
    "Clean minimalist 2D flat vector technical illustration, modern software concept art, "
    "dark theme, high contrast, clean lines and geometric shapes, directional arrows, "
    "sharp focus, crisp perfectly legible typography for the one or two short labels only, "
    "minimalist developer editorial style."
)

IMAGE_NEGATIVE_PROMPT = (
    "paragraphs, sentences, dense text, too much text, tiny text, code, syntax, "
    "pseudo-code, memory address, gibberish text, distorted letters, unreadable "
    "typography, misspelled text, handwriting, scribbles, "
    "photorealistic, real-life photography, messy, cluttered, blurry, "
    "low quality, distorted, watermark, signature, noisy background"
)
