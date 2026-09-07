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


DEFAULT_CHANNEL_LINK = "[Kernel To Cloude](https://t.me/kernel2cloud)"


def _to_blockquote(text: str) -> str:
    """Prefix each non-empty line of text with markdown quote syntax '>'."""
    lines = text.splitlines()
    return "\n".join(f"> {line}" if line.strip() else ">" for line in lines)


def format_lesson(
    data: Dict[str, Any],
    channel_link: str = DEFAULT_CHANNEL_LINK,
    valid_reference_url: str | None = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Compile structured lesson components into plain text and Telegram MessageEntity dicts.

    Args:
        data: Dictionary with 'title', 'concept_summary', 'explanation', 'key_takeaway',
              optional 'hashtags', and optional 'valid_reference_url'.
        channel_link: Markdown formatted link to append at the bottom.
        valid_reference_url: Optional validated URL to render as '📖 [more: ](url)'.

    Returns:
        A tuple of (clean_plain_text, list_of_entity_dictionaries).
    """
    raw_title = data.get("title", "").strip()
    raw_summary = data.get("concept_summary", "").strip()
    raw_explanation = data.get("explanation", "").strip()
    raw_takeaway = data.get("key_takeaway", "").strip()
    raw_hashtags = data.get("hashtags")
    ref_url = valid_reference_url or data.get("valid_reference_url")

    parts: List[str] = [f"**{raw_title}**"]
    if raw_summary:
        parts.append(_to_blockquote(f"*{raw_summary}*"))
    if raw_explanation:
        parts.append(raw_explanation)
    if raw_takeaway:
        parts.append(_to_blockquote(raw_takeaway))

    # Format 2-3 categorized technical hashtags
    formatted_hashtags = ""
    if raw_hashtags:
        if isinstance(raw_hashtags, list):
            tags = [
                tag.strip() if tag.strip().startswith("#") else f"#{tag.strip()}"
                for tag in raw_hashtags
                if isinstance(tag, str) and tag.strip()
            ]
            formatted_hashtags = " ".join(tags)
        elif isinstance(raw_hashtags, str):
            tags = [
                tag.strip() if tag.strip().startswith("#") else f"#{tag.strip()}"
                for tag in raw_hashtags.split()
                if tag.strip()
            ]
            formatted_hashtags = " ".join(tags)

    footer_lines: List[str] = []
    if ref_url and isinstance(ref_url, str) and ref_url.strip():
        footer_lines.append(f"📖 [more: ]({ref_url.strip()})")
    if formatted_hashtags:
        footer_lines.append(formatted_hashtags)
    if channel_link:
        footer_lines.append(channel_link)

    if footer_lines:
        parts.append("\n\n".join(footer_lines))

    markdown_doc = "\n\n".join(parts)

    text, entities = convert(markdown_doc, config=_CONFIG)

    # If the payload exceeds Telegram's message boundary, take the primary chunk with aligned entities
    chunks = split_entities(text, entities, max_utf16_len=TELEGRAM_MAX_MESSAGE_LENGTH)
    if not chunks:
        return text, [e.to_dict() for e in entities]

    primary_text, primary_entities = chunks[0]
    return primary_text, [e.to_dict() for e in primary_entities]
