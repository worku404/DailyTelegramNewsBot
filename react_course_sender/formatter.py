"""Transforms structured day JSON objects into chunked Telegram messages.

Builds a full Markdown document from every field in a day entry, then compiles
it into plain text + UTF-16 MessageEntity dicts via telegramify-markdown.
Content exceeding Telegram's 4,096-character limit is split into ordered chunks
using split_entities so nothing is truncated.

Design Decisions:
- Entity-Based Delivery (no parse_mode): Avoids all MarkdownV2/HTML escaping
  issues by delivering formatting as explicit MessageEntity dictionaries.
- Clean Headings: telegramify-markdown's default emoji prefixes on headings
  are stripped so the source text hierarchy is respected exactly.
- Multi-Chunk Output: The formatter always returns a list of (text, entities)
  tuples. Callers iterate and send each sequentially.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from telegramify_markdown import convert, split_entities
from telegramify_markdown.config import get_runtime_config

TELEGRAM_MAX_MESSAGE_LENGTH = 4096

# Neutralize default heading emoji prefixes so our source text is rendered as-is.
_CONFIG = get_runtime_config()
_CONFIG._markdown_symbol.heading_level_1 = ""
_CONFIG._markdown_symbol.heading_level_2 = ""
_CONFIG._markdown_symbol.heading_level_3 = ""
_CONFIG._markdown_symbol.heading_level_4 = ""


def _bullet_list(items: list, ordered: bool = False) -> str:
    """Render a list of strings as a Markdown bullet or numbered list."""
    lines: List[str] = []
    for i, item in enumerate(items, 1):
        prefix = f"{i}." if ordered else "•"
        lines.append(f"{prefix} {item}")
    return "\n".join(lines)


def _to_blockquote(text: str) -> str:
    """Prefix each non-empty line with Markdown quote syntax '>'."""
    return "\n".join(
        f"> {line}" if line.strip() else ">" for line in text.splitlines()
    )


def _format_hashtags(raw_hashtags: Any) -> str:
    """Normalize hashtags into a space-separated string."""
    if not raw_hashtags:
        return ""
    if isinstance(raw_hashtags, list):
        tags = [
            tag.strip() if tag.strip().startswith("#") else f"#{tag.strip()}"
            for tag in raw_hashtags
            if isinstance(tag, str) and tag.strip()
        ]
        return " ".join(tags)
    if isinstance(raw_hashtags, str):
        tags = [
            tag.strip() if tag.strip().startswith("#") else f"#{tag.strip()}"
            for tag in raw_hashtags.split()
            if tag.strip()
        ]
        return " ".join(tags)
    return ""


def _build_markdown(day: Dict[str, Any]) -> str:
    """Assemble a complete Markdown document from a single day's JSON fields."""
    parts: List[str] = []

    # ── Header: Chapter + Title ──
    chapter = day.get("chapter", "")
    title = day.get("title", "")
    day_num = day.get("day", "")
    header = f"# Day {day_num} — {title}"
    if chapter:
        header += f"\n*{chapter}*"
    parts.append(header)

    # ── Prerequisites ──
    prereqs = day.get("prerequisites", [])
    if prereqs:
        parts.append("**📋 Prerequisites**\n" + _bullet_list(prereqs))

    # ── Learning Objectives ──
    objectives = day.get("learning_objectives", [])
    if objectives:
        parts.append("**🎯 Learning Objectives**\n" + _bullet_list(objectives, ordered=True))

    # ── Concept Summary (blockquoted) ──
    summary = day.get("concept_summary", "").strip()
    if summary:
        parts.append("**💡 Concept Summary**\n" + _to_blockquote(summary))

    # ── Explanation (main body — already contains Markdown with code blocks) ──
    explanation = (day.get("explanation") or day.get("text") or "").strip()
    if explanation:
        parts.append(explanation)

    # ── Hands-On Task ──
    hands_on = day.get("hands_on", "").strip()
    if hands_on:
        parts.append("**🛠 Hands-On**\n" + hands_on)

    # ── Reference Links ──
    ref_links = day.get("reference_links", [])
    if ref_links:
        link_lines = [f"👉 [Link {i}]({url})" for i, url in enumerate(ref_links, 1)]
        parts.append("**📖 References**\n" + "\n".join(link_lines))

    # ── Hashtags ──
    hashtags = _format_hashtags(day.get("hashtags"))
    if hashtags:
        parts.append(hashtags)

    return "\n\n".join(parts)


def format_day(day: Dict[str, Any]) -> List[Tuple[str, List[Dict[str, Any]]]]:
    """Compile a single day's JSON into a list of Telegram-ready (text, entities) chunks.

    Args:
        day: One element from the ``days`` array in react_in_11_days.json.

    Returns:
        Ordered list of (plain_text, entity_dicts) tuples, each fitting within
        Telegram's 4,096 UTF-16 code-unit message limit.
    """
    markdown_doc = _build_markdown(day)

    text, entities = convert(markdown_doc, config=_CONFIG)

    chunks = split_entities(
        text, entities, max_utf16_len=TELEGRAM_MAX_MESSAGE_LENGTH
    )

    if not chunks:
        # Content fits in a single message — return as a one-element list.
        return [(text, [e.to_dict() for e in entities])]

    return [
        (chunk_text, [e.to_dict() for e in chunk_entities])
        for chunk_text, chunk_entities in chunks
    ]
