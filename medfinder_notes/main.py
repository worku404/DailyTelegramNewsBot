"""Entry-point for the MedFinder OOP Notes pipeline.

Two-stage decoupled orchestration:
1. Sync Stage: Fetches newly merged PRs from worku404/MedFinder-java, filters
   diffs strictly to src/main/ Java & key config files (excluding src/test/),
   maps concepts to topics.md via Gemini, and saves sequentially numbered .md
   files under medfinder_notes/notes/.
2. Delivery Stage: Selects up to MAX_FILES_PER_RUN unsent notes using the
   Fresh-PR-First priority queue, delivers them via Telegram sendDocument,
   and updates state.json strictly after each confirmed upload.

Usage:
    python -m medfinder_notes.main                 # Sync merged PRs + send up to MAX_FILES_PER_RUN
    python -m medfinder_notes.main --sync-only     # Only analyze new merged PRs & save notes
    python -m medfinder_notes.main --send-only     # Only send queued notes to Telegram
    python -m medfinder_notes.main --pr 3        # Force-analyze PR #6 (even if open/processed)
    python -m medfinder_notes.main --dry-run       # Preview actions without writing or sending
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
import time
from typing import Optional

from medfinder_notes.config import (
    GITHUB_OWNER,
    GITHUB_REPO,
    INTER_FILE_PAUSE_SECONDS,
    MAX_DIFF_CHARS,
    MAX_FILES_PER_RUN,
    MAX_NOTES_PER_PR,
    NOTES_DIR,
    PR_TRIGGER_MODE,
    STATE_FILE,
    TOPICS_FILE,
    get_github_token,
    get_telegram_credentials,
)
from medfinder_notes.github_client import (
    PullRequestInfo,
    fetch_pr_relevant_files,
    fetch_pull_request,
    fetch_pull_requests,
    format_diff_for_prompt,
    is_eligible_pr,
)
from medfinder_notes.note_generator import generate_notes_for_pr
from medfinder_notes.sender import format_caption, send_telegram_document
from medfinder_notes.state import (
    list_existing_note_titles,
    load_state,
    mark_file_sent,
    record_pr_processed,
    save_generated_notes,
    select_files_to_send,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("medfinder_notes.main")


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync MedFinder merged PRs into OOP study notes and deliver via Telegram."
    )
    parser.add_argument(
        "--sync-only",
        action="store_true",
        help="Only check GitHub PRs and generate/save notes; do not send to Telegram.",
    )
    parser.add_argument(
        "--send-only",
        action="store_true",
        help="Only send queued notes to Telegram; do not check GitHub or call Gemini.",
    )
    parser.add_argument(
        "--pr",
        type=int,
        default=None,
        help="Manually analyze a specific PR number (bypasses merged/processed filters).",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help=f"Override MAX_FILES_PER_RUN (default: {MAX_FILES_PER_RUN}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be generated/sent without writing files, state, or calling Telegram.",
    )
    return parser.parse_args(argv)


def sync_prs(
    notes_dir: Path = NOTES_DIR,
    topics_file: Path = TOPICS_FILE,
    state_file: Path = STATE_FILE,
    owner: str = GITHUB_OWNER,
    repo: str = GITHUB_REPO,
    trigger_mode: str = PR_TRIGGER_MODE,
    max_notes_per_pr: int = MAX_NOTES_PER_PR,
    max_diff_chars: int = MAX_DIFF_CHARS,
    forced_pr_number: Optional[int] = None,
    dry_run: bool = False,
) -> list[str]:
    """Stage 1: Discover new eligible PRs, generate notes with Gemini, and save to disk."""
    state = load_state(state_file)
    github_token = get_github_token()

    if not topics_file.is_file():
        raise FileNotFoundError(f"Course syllabus file not found: {topics_file}")
    topics_text = topics_file.read_text(encoding="utf-8")

    target_prs: list[PullRequestInfo]
    if forced_pr_number is not None:
        logger.info("Fetching forced PR #%d from %s/%s...", forced_pr_number, owner, repo)
        target_prs = [fetch_pull_request(owner, repo, forced_pr_number, github_token)]
    else:
        logger.info(
            "Checking %s/%s for new PRs (mode=%s)...",
            owner,
            repo,
            trigger_mode,
        )
        all_prs = fetch_pull_requests(owner, repo, github_token)
        processed = state.get("processed_prs", {})
        target_prs = [
            pr
            for pr in all_prs
            if is_eligible_pr(pr, trigger_mode) and str(pr.number) not in processed
        ]

    if not target_prs:
        logger.info("No new eligible PRs to analyze.")
        return []

    created_all: list[str] = []

    for pr in target_prs:
        logger.info(
            "Analyzing PR #%d (%s) by @%s...",
            pr.number,
            pr.title,
            pr.author,
        )
        relevant_files = fetch_pr_relevant_files(owner, repo, pr.number, github_token)
        if not relevant_files:
            logger.info(
                "PR #%d has no relevant src/main/ or config changes; skipping note generation.",
                pr.number,
            )
            if not dry_run:
                record_pr_processed(pr, [], state, state_file)
            continue

        diff_text = format_diff_for_prompt(relevant_files, max_chars=max_diff_chars)
        existing_titles = list_existing_note_titles(notes_dir, state)

        if dry_run:
            logger.info(
                "[DRY RUN] Would send %d relevant file(s) (%d diff chars) from PR #%d to Gemini.",
                len(relevant_files),
                len(diff_text),
                pr.number,
            )
            continue

        generated = generate_notes_for_pr(
            pr=pr,
            diff_text=diff_text,
            topics_text=topics_text,
            existing_titles=existing_titles,
            max_notes=max_notes_per_pr,
        )

        if not generated:
            logger.info("Gemini returned 0 notes for PR #%d (no new OOP concepts).", pr.number)
            record_pr_processed(pr, [], state, state_file)
            continue

        saved = save_generated_notes(
            notes=generated,
            pr=pr,
            notes_dir=notes_dir,
            state=state,
            state_file=state_file,
        )
        logger.info("Saved %d new note(s) for PR #%d: %s", len(saved), pr.number, saved)
        created_all.extend(saved)

    return created_all


def deliver_queued_notes(
    notes_dir: Path = NOTES_DIR,
    state_file: Path = STATE_FILE,
    max_files: int = MAX_FILES_PER_RUN,
    pause_seconds: float = INTER_FILE_PAUSE_SECONDS,
    dry_run: bool = False,
) -> list[str]:
    """Stage 2: Send up to max_files notes using Fresh-PR-First priority ordering."""
    state = load_state(state_file)
    chosen = select_files_to_send(notes_dir, state, max_files=max_files)

    if not chosen:
        logger.info("All notes have already been delivered — delivery queue is empty.")
        return []

    metadata_map = state.get("note_metadata", {})

    if dry_run:
        for fname in chosen:
            caption = format_caption(fname, metadata_map.get(fname), notes_dir / fname)
            logger.info("[DRY RUN] Would send %s | caption: %s", fname, caption)
        return chosen

    bot_token, chat_id, thread_id = get_telegram_credentials()
    delivered: list[str] = []

    for idx, fname in enumerate(chosen):
        file_path = notes_dir / fname
        caption = format_caption(fname, metadata_map.get(fname), file_path)
        logger.info("Sending %s to Telegram (%s)...", fname, caption)
        send_telegram_document(bot_token, chat_id, file_path, caption=caption, thread_id=thread_id)
        mark_file_sent(fname, state, state_file)
        delivered.append(fname)
        logger.info("Delivered %s and updated state.json.", fname)

        if idx < len(chosen) - 1 and pause_seconds > 0:
            time.sleep(pause_seconds)

    return delivered


def main(argv: Optional[list[str]] = None) -> int:
    """Run the MedFinder notes pipeline."""
    args = _parse_args(argv)

    if args.sync_only and args.send_only:
        logger.error("Cannot combine --sync-only and --send-only.")
        return 2

    max_files = args.max_files if args.max_files is not None else MAX_FILES_PER_RUN

    if not args.send_only:
        sync_prs(
            forced_pr_number=args.pr,
            dry_run=args.dry_run,
        )

    if not args.sync_only:
        deliver_queued_notes(
            max_files=max_files,
            dry_run=args.dry_run,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
