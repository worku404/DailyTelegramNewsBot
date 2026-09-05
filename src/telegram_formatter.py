"""Transforms structured micro-lessons into Telegram plain text and MessageEntity objects.

Employs telegramify-markdown to compile GitHub-Flavored Markdown into an Abstract
Syntax Tree (AST), producing sanitized plain text and exact UTF-16 entity offsets.

Design Decisions & Invariants:
- Zero-Escaping Entity Delivery: Rather than embedding parse_mode strings (HTML or MarkdownV2),
  formatting is expressed via explicit MessageEntity dictionaries. This guarantees zero
  character-escaping crashes on symbols like '.', '!', '<', '>', or '&'.
- UTF-16 Code Unit Measurement: Telegram measures entity offsets in UTF-16 code units.
  telegramify-markdown internally calculates these byte offsets, avoiding alignment
  drift when emojis or multibyte unicode characters appear in the text.
- Clean Headings: Default symbol prefixes on headers (e.g. 📚, 📌) are neutralized
  so the model's exact text hierarchy is respected.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
from telegramify_markdown import convert, split_entities
from telegramify_markdown.config import get_runtime_config

TELEGRAM_MAX_MESSAGE_LENGTH = 4096

_CONFIG = get_runtime_config()
_CONFIG._markdown_symbol.heading_level_1 = ""
_CONFIG._markdown_symbol.heading_level_2 = ""
_CONFIG._markdown_symbol.heading_level_3 = ""
_CONFIG._markdown_symbol.heading_level_4 = ""


def _to_blockquote(text: str) -> str:
    """Prefix each non-empty line of text with markdown quote syntax '>'."""
    lines = text.splitlines()
    return "\n".join(f"> {line}" if line.strip() else ">" for line in lines)


def format_lesson(data: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
    """Compile structured lesson components into plain text and Telegram MessageEntity dicts.

    Args:
        data: Dictionary with 'title', 'concept_summary', 'explanation', and 'key_takeaway'.

    Returns:
        A tuple of (clean_plain_text, list_of_entity_dictionaries).
    """
    raw_title = data.get("title", "").strip()
    raw_summary = data.get("concept_summary", "").strip()
    raw_explanation = data.get("explanation", "").strip()
    raw_takeaway = data.get("key_takeaway", "").strip()

    parts: List[str] = [f"**{raw_title}**"]
    if raw_summary:
        parts.append(_to_blockquote(f"*{raw_summary}*"))
    if raw_explanation:
        parts.append(raw_explanation)
    if raw_takeaway:
        parts.append(_to_blockquote(raw_takeaway))

    markdown_doc = "\n\n".join(parts)

    text, entities = convert(markdown_doc, config=_CONFIG)

    # If the payload exceeds Telegram's message boundary, take the primary chunk with aligned entities
    chunks = split_entities(text, entities, max_utf16_len=TELEGRAM_MAX_MESSAGE_LENGTH)
    if not chunks:
        return text, [e.to_dict() for e in entities]

    primary_text, primary_entities = chunks[0]
    return primary_text, [e.to_dict() for e in primary_entities]
