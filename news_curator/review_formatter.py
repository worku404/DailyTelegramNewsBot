"""Compiles curated stories into Telegram review cards for the editorial chat.

Employs telegramify-markdown to produce sanitized plain text and exact UTF-16
MessageEntity offsets for the private review bot.
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


def format_review_card(
    story: Dict[str, Any],
    stream_id: int,
    stream_name: str,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Compile an evaluated story into a review card for the editor's private chat.

    Args:
        story: Curated story dictionary containing title, author, source_name, url,
               why_it_matters, key_takeaway, and ready_to_ship_draft.
        stream_id: The stream identifier (1 or 2).
        stream_name: Name of the stream category.

    Returns:
        Tuple of (clean_plain_text, list_of_entity_dictionaries).
    """
    title = story.get("title", "").strip()
    author = story.get("author", "").strip()
    source_name = story.get("source_name", "").strip()
    url = story.get("url", "").strip()
    why_it_matters = story.get("why_it_matters", "").strip()
    key_takeaway = story.get("key_takeaway", "").strip()
    draft = story.get("ready_to_ship_draft", "").strip()

    parts = [
        f"⭐ **[STREAM {stream_id}: {stream_name.upper()}]**",
        f"📰 **{title}**",
        f"👤 **Source:** {author} ({source_name})",
        f"🔗 **Original:** [Read Source Article]({url})",
        "🧠 **Why This Matters:**",
        _to_blockquote(why_it_matters),
        "💡 **Key Takeaway / Mental Model:**",
        _to_blockquote(key_takeaway),
        "---\n📋 **READY-TO-SHIP DRAFT (Copy or Forward below):**",
        draft,
    ]

    markdown_doc = "\n\n".join(parts)
    text, entities = convert(markdown_doc, config=_CONFIG)

    chunks = split_entities(text, entities, max_utf16_len=TELEGRAM_MAX_MESSAGE_LENGTH)
    if not chunks:
        return text, [e.to_dict() for e in entities]

    primary_text, primary_entities = chunks[0]
    return primary_text, [e.to_dict() for e in primary_entities]
