"""State management, monotonic note numbering, and Fresh-PR-First priority queue.

Queue semantics (Option 2 — Fresh PR Notes First):
- Unsent PR-generated notes (in ``pr_note_queue``) are ALWAYS sent first,
  ordered ascending by their numeric prefix (e.g. ``15-``, ``16-``).
- Any remaining slots up to ``MAX_FILES_PER_RUN`` are filled from unsent
  backlog notes in ``notes/`` (e.g. ``01-``, ``02-``, ..., ``14-``).
- Each file is marked sent in ``state.json`` strictly AFTER Telegram confirms
  delivery, guaranteeing zero skipped notes on transient network failures.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Optional

from medfinder_notes.github_client import PullRequestInfo
from medfinder_notes.note_generator import GeneratedNote

_NUMBER_PREFIX_RE = re.compile(r"^(\d+)-")


def extract_note_number(filename: str) -> Optional[int]:
    """Extract the leading integer index from a numbered note filename (e.g. '04-foo.md' -> 4)."""
    match = _NUMBER_PREFIX_RE.match(filename)
    return int(match.group(1)) if match else None


def _note_sort_key(filename: str) -> tuple[int, str]:
    num = extract_note_number(filename)
    return (num if num is not None else 10**9, filename)


def default_state() -> dict[str, Any]:
    return {
        "next_index": 1,
        "processed_prs": {},
        "pr_note_queue": [],
        "sent_files": [],
        "note_metadata": {},
    }


def load_state(state_file: Path) -> dict[str, Any]:
    """Load persistent pipeline state from JSON, returning defaults if missing."""
    if not state_file.is_file():
        return default_state()

    data = json.loads(state_file.read_text(encoding="utf-8"))
    state = default_state()
    state.update(data)
    return state


def save_state(state: dict[str, Any], state_file: Path) -> None:
    """Persist pipeline state atomically with stable formatting."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = state_file.with_suffix(".json.tmp")
    tmp_path.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(state_file)


def extract_markdown_title(file_path: Path) -> str:
    """Read the first H1 heading ('# ...') from a Markdown file, or fall back to filename."""
    if file_path.is_file():
        for line in file_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
    stem = re.sub(r"^\d+-", "", file_path.stem)
    return stem.replace("-", " ").title()


def list_existing_note_titles(notes_dir: Path, state: dict[str, Any]) -> list[str]:
    """Return ordered titles of all notes currently stored in notes_dir."""
    if not notes_dir.is_dir():
        return []

    metadata = state.get("note_metadata", {})
    titles: list[str] = []
    for path in sorted(notes_dir.glob("*.md"), key=lambda p: _note_sort_key(p.name)):
        meta = metadata.get(path.name) or {}
        title = meta.get("title") or extract_markdown_title(path)
        titles.append(f"{path.name}: {title}")
    return titles


def _compute_next_index(notes_dir: Path, state: dict[str, Any]) -> int:
    highest = int(state.get("next_index", 1)) - 1
    if notes_dir.is_dir():
        for path in notes_dir.glob("*.md"):
            num = extract_note_number(path.name)
            if num is not None and num > highest:
                highest = num
    return highest + 1


def save_generated_notes(
    notes: list[GeneratedNote],
    pr: PullRequestInfo,
    notes_dir: Path,
    state: dict[str, Any],
    state_file: Path,
) -> list[str]:
    """Write generated notes to disk with sequential numbering and persist state."""
    notes_dir.mkdir(parents=True, exist_ok=True)
    next_idx = _compute_next_index(notes_dir, state)
    created_filenames: list[str] = []

    pr_queue: list[str] = state.setdefault("pr_note_queue", [])
    note_metadata: dict[str, Any] = state.setdefault("note_metadata", {})

    for note in notes:
        filename = f"{next_idx:02d}-{note.slug}.md"
        file_path = notes_dir / filename
        file_path.write_text(note.markdown_content, encoding="utf-8")

        created_filenames.append(filename)
        if filename not in pr_queue:
            pr_queue.append(filename)

        note_metadata[filename] = {
            "title": note.title,
            "source": "pr",
            "pr_number": pr.number,
            "pr_author": pr.author,
            "chapter_refs": note.chapter_refs,
        }
        next_idx += 1

    state["next_index"] = next_idx
    pr_queue.sort(key=_note_sort_key)

    record_pr_processed(
        pr=pr,
        generated_filenames=created_filenames,
        state=state,
        state_file=state_file,
    )
    return created_filenames


def record_pr_processed(
    pr: PullRequestInfo,
    generated_filenames: list[str],
    state: dict[str, Any],
    state_file: Path,
    baseline: bool = False,
) -> None:
    """Record a PR as processed in state.json and save immediately."""
    processed = state.setdefault("processed_prs", {})
    processed[str(pr.number)] = {
        "title": pr.title,
        "author": pr.author,
        "merged_at": pr.merged_at,
        "head_sha": pr.head_sha,
        "baseline": baseline,
        "notes": generated_filenames,
    }
    save_state(state, state_file)


def select_files_to_send(
    notes_dir: Path,
    state: dict[str, Any],
    max_files: int,
) -> list[str]:
    """Select up to max_files unsent notes using Fresh-PR-First priority ordering.

    1. Unsent files in ``state['pr_note_queue']`` (ascending numeric order).
    2. Remaining slots filled from unsent backlog ``*.md`` files in ``notes_dir``
       (ascending numeric order).
    """
    if max_files <= 0 or not notes_dir.is_dir():
        return []

    sent_set = set(state.get("sent_files", []))
    available_files = {p.name for p in notes_dir.glob("*.md")}

    selected: list[str] = []
    selected_set: set[str] = set()

    # Priority 1: Fresh PR-generated notes first
    pr_candidates = sorted(
        (
            fname
            for fname in state.get("pr_note_queue", [])
            if fname in available_files and fname not in sent_set
        ),
        key=_note_sort_key,
    )
    for fname in pr_candidates:
        if len(selected) >= max_files:
            return selected
        if fname not in selected_set:
            selected.append(fname)
            selected_set.add(fname)

    # Priority 2: Fill remaining slots from numbered backlog (01-, 02-, ..., 14-)
    backlog_candidates = sorted(
        (
            fname
            for fname in available_files
            if fname not in sent_set and fname not in selected_set
        ),
        key=_note_sort_key,
    )
    for fname in backlog_candidates:
        if len(selected) >= max_files:
            break
        selected.append(fname)
        selected_set.add(fname)

    return selected


def mark_file_sent(filename: str, state: dict[str, Any], state_file: Path) -> None:
    """Record a single file as delivered to Telegram and persist immediately."""
    pr_queue: list[str] = state.setdefault("pr_note_queue", [])
    if filename in pr_queue:
        pr_queue.remove(filename)

    sent_files: list[str] = state.setdefault("sent_files", [])
    if filename not in sent_files:
        sent_files.append(filename)

    save_state(state, state_file)
