"""JSON-backed article deduplication and history persistence.

Maintains a canonical registry of processed article URLs to prevent duplicate
dispatches across editorial runs, with automated pruning of expired records.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Sequence

logger = logging.getLogger("news_curator.history")

DEFAULT_HISTORY_FILE = Path(__file__).parent / "seen_articles.json"
MAX_RETENTION_DAYS = 30


class HistoryManager:
    """Tracks seen article URLs across runs to guarantee zero duplicate pings."""

    def __init__(self, history_file: Path | str = DEFAULT_HISTORY_FILE):
        self.history_file = Path(history_file)
        self._seen_urls: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        """Load seen URLs and ISO timestamps from persistent storage."""
        if not self.history_file.exists():
            self._seen_urls = {}
            return

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Schema: {url: first_seen_iso_timestamp}
                    self._seen_urls = data.get("seen_urls", {})
                else:
                    self._seen_urls = {}
        except Exception as exc:
            logger.warning("Could not read history file %s: %s. Re-initializing empty.", self.history_file, exc)
            self._seen_urls = {}

    def is_seen(self, url: str) -> bool:
        """Check whether an article URL has already been processed."""
        if not url:
            return True
        normalized = url.strip().rstrip("/")
        return normalized in self._seen_urls

    def mark_seen(self, urls: Sequence[str]) -> None:
        """Add new URLs to the seen registry and persist to disk atomically."""
        if not urls:
            return

        now_iso = datetime.now(timezone.utc).isoformat()
        mutated = False
        for raw_url in urls:
            normalized = raw_url.strip().rstrip("/")
            if normalized and normalized not in self._seen_urls:
                self._seen_urls[normalized] = now_iso
                mutated = True

        if mutated:
            self._prune()
            self._save()

    def _prune(self) -> None:
        """Prune entries older than MAX_RETENTION_DAYS to keep file size bounded."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_RETENTION_DAYS)
        surviving = {}
        for url, ts_str in self._seen_urls.items():
            try:
                dt = datetime.fromisoformat(ts_str)
                if dt >= cutoff:
                    surviving[url] = ts_str
            except (ValueError, TypeError):
                # Retain entries with unparseable timestamps rather than prematurely re-alerting
                surviving[url] = ts_str
        self._seen_urls = surviving

    def _save(self) -> None:
        """Atomically persist seen URLs via write-and-rename."""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "seen_urls": self._seen_urls,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

        # Write to temporary file in same directory to ensure atomic os.replace across filesystems
        dir_name = self.history_file.parent
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
            json.dump(payload, tf, indent=2)
            temp_path = tf.name

        os.replace(temp_path, self.history_file)
        logger.info("Persisted %d seen URLs to %s.", len(self._seen_urls), self.history_file.name)
