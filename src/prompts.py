"""Structured prompt engineering and schema definitions for Gemini micro-lessons.

Defines the system prompt template and the strict JSON schema passed to Gemini
for structured outputs.

Design Decisions & Invariants:
- Dual Contract Alignment: The fields specified in PROMPT_TEMPLATE must mirror
  LESSON_SCHEMA exactly. If a field exists in the JSON schema but is omitted
  from the prompt text, the model may under-populate or hallucinate that field.
"""

from __future__ import annotations

from typing import Any

PROMPT_TEMPLATE = """You are teaching ONE software engineering concept to an experienced software engineer.
Teach only this topic:

TOPIC: {title}

Rules:
- Audience: Experienced software engineer. Use precise technical terminology, avoid introductory hand-holding, and teach at an intermediate-to-advanced register.
- Formatting & Layout:
  * Structure: Break the explanation into 2–3 concise, focused paragraphs separated by blank lines.
  * Subheadings & Lists: Every numbered item, paradigm, or trade-off MUST start on its own separate line, preceded by a blank line.
  * Bold Labels: ALWAYS bold the subtitle or label of each list item or paradigm (e.g., "1. **Closed Interval [L, R]:** ...").
  * No Run-On Lists: NEVER pack multiple numbered items (do NOT write "1. ... 2. ...") into a single continuous paragraph.
- Code: If code clarifies the invariant or pitfall, include a concise, focused snippet in a fenced Markdown block (e.g. ```python ... ```). Omit code if not needed.
- Anti-hallucination: If you are not confident in a specific detail, omit it rather than speculate.
- Tone: Crisp, practical, and punchy. No generic fluff or boilerplate conversational intros.

Output MUST satisfy these exact fields:
- title: A short, precise name for the concept.
- concept_summary: ONE sentence answering what it is, why it exists, or what problem it solves.
- explanation: The technical core of the lesson. Explain the underlying mechanism, trade-offs, invariants, and common footguns. Format with blank lines between paragraphs and bold subtitles for all list items.
- key_takeaway: One memorable line or mental model the reader should retain.
- hashtags: An array of 2 to 3 categorized technical hashtags relevant to this specific topic, each starting with # (e.g., ["#SystemDesign", "#Concurrency", "#Databases"]).
- reference_links: An array of exactly 3 candidate reference URLs for further reading from high-authority, canonical technical documentation, official language/library specs, RFCs, or Wikipedia (e.g. ["https://docs.python.org/...", "https://en.wikipedia.org/wiki/...", "https://datatracker.ietf.org/doc/html/..."]). Prefer stable, canonical URLs that are unlikely to 404.
"""

LESSON_FIELDS = (
    "title",
    "concept_summary",
    "explanation",
    "key_takeaway",
    "hashtags",
    "reference_links",
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
        "hashtags": {
            "type": "ARRAY",
            "items": {
                "type": "STRING",
            },
            "description": "2 to 3 categorized technical hashtags relevant to this topic, each starting with #.",
        },
        "reference_links": {
            "type": "ARRAY",
            "items": {
                "type": "STRING",
            },
            "description": "Exactly 3 candidate reference URLs for further reading from high-authority canonical sources (e.g. Wikipedia, official documentation, RFCs).",
        },
    },
    "required": list(LESSON_FIELDS),
}
