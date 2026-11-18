"""Comprehensive unit & integration tests for the medfinder_notes package.

Run with:
    python -m unittest discover -s medfinder_notes/tests -v
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import requests

from medfinder_notes.github_client import (
    PrFileChange,
    PullRequestInfo,
    _get_with_retry,
    format_diff_for_prompt,
    is_eligible_pr,
    is_relevant_file,
)
from medfinder_notes.main import deliver_queued_notes, sync_prs
from medfinder_notes.note_generator import (
    GeneratedNote,
    _repair_double_escaping,
    generate_notes_for_pr,
    sanitize_slug,
)
from medfinder_notes.sender import format_caption, send_telegram_document
from medfinder_notes.state import (
    default_state,
    extract_note_number,
    load_state,
    mark_file_sent,
    save_generated_notes,
    save_state,
    select_files_to_send,
)


def _make_pr(
    number: int = 6,
    title: str = "feat(console): add abstract Menu base class",
    author: str = "wubettamrat525-prog",
    state: str = "closed",
    merged_at: str | None = "2026-11-18T12:00:00Z",
) -> PullRequestInfo:
    return PullRequestInfo(
        number=number,
        title=title,
        author=author,
        state=state,
        merged_at=merged_at,
        html_url=f"https://github.com/worku404/MedFinder-java/pull/{number}",
        head_sha=f"sha-{number}",
    )


class TestGithubClient(unittest.TestCase):
    def test_is_relevant_file_strictly_includes_src_main_and_excludes_tests(self) -> None:
        # Included production Java & key build/config files
        self.assertTrue(is_relevant_file("src/main/java/medfinder/console/Menu.java"))
        self.assertTrue(is_relevant_file("src/main/java/medfinder/Main.java"))
        self.assertTrue(is_relevant_file("pom.xml"))
        self.assertTrue(is_relevant_file("config/config.properties.example"))
        self.assertTrue(is_relevant_file("src/main/resources/ai/system-prompt.txt"))

        # Completely excluded: src/test/, docs/, README, seed CSVs, gitignore
        self.assertFalse(is_relevant_file("src/test/java/medfinder/logic/TextSimilarityTest.java"))
        self.assertFalse(is_relevant_file("src/test/java/medfinder/support/FakeLlmClient.java"))
        self.assertFalse(is_relevant_file("src/test/resources/sample.txt"))
        self.assertFalse(is_relevant_file("docs/02-high-level-design.md"))
        self.assertFalse(is_relevant_file("README.md"))
        self.assertFalse(is_relevant_file(".gitignore"))
        self.assertFalse(is_relevant_file("src/main/resources/seed/users.csv"))
        self.assertFalse(is_relevant_file("OtherFile.java"))

    def test_is_eligible_pr_merged_vs_all(self) -> None:
        merged_pr = _make_pr(number=6, state="closed", merged_at="2026-11-18T10:00:00Z")
        open_pr = _make_pr(number=7, state="open", merged_at=None)
        closed_unmerged_pr = _make_pr(number=8, state="closed", merged_at=None)

        self.assertTrue(is_eligible_pr(merged_pr, "merged"))
        self.assertFalse(is_eligible_pr(open_pr, "merged"))
        self.assertFalse(is_eligible_pr(closed_unmerged_pr, "merged"))

        self.assertTrue(is_eligible_pr(open_pr, "all"))
        self.assertTrue(is_eligible_pr(merged_pr, "all"))

        with self.assertRaises(ValueError):
            is_eligible_pr(merged_pr, "invalid")

    def test_format_diff_for_prompt_truncates_large_diffs(self) -> None:
        big_patch = "+String x = \"a\";\n" * 500
        files = [
            PrFileChange(
                filename="src/main/java/medfinder/console/Menu.java",
                status="added",
                additions=500,
                deletions=0,
                patch=big_patch,
            )
        ]
        rendered = format_diff_for_prompt(files, max_chars=400)
        self.assertLessEqual(len(rendered), 450)
        self.assertIn("diff truncated", rendered)

    @patch("medfinder_notes.github_client.time.sleep")
    @patch("medfinder_notes.github_client.requests.get")
    def test_get_with_retry_recovers_from_ssl_and_timeout_errors(
        self, mock_get: MagicMock, _mock_sleep: MagicMock
    ) -> None:
        ok_resp = MagicMock(ok=True, status_code=200)
        mock_get.side_effect = [
            requests.exceptions.SSLError("EOF occurred in violation of protocol"),
            requests.exceptions.ReadTimeout("Read timed out"),
            ok_resp,
        ]
        result = _get_with_retry("https://api.github.com/test", headers={}, max_retries=4, initial_backoff=0.0)
        self.assertIs(result, ok_resp)
        self.assertEqual(mock_get.call_count, 3)


class TestPriorityQueueAndState(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.notes_dir = self.root / "notes"
        self.notes_dir.mkdir()
        self.state_file = self.root / "state.json"

        # Seed backlog notes 01..14
        for idx in range(1, 15):
            (self.notes_dir / f"{idx:02d}-topic-{idx}.md").write_text(
                f"# Topic {idx}\n\nBody for topic {idx}.\n",
                encoding="utf-8",
            )

        state = default_state()
        state["next_index"] = 15
        save_state(state, self.state_file)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_fresh_pr_notes_jump_ahead_of_backlog_then_resume(self) -> None:
        state = load_state(self.state_file)
        # Simulate notes 01..03 already sent (user's exact example!)
        for idx in (1, 2, 3):
            mark_file_sent(f"{idx:02d}-topic-{idx}.md", state, self.state_file)

        # A new merged PR generates notes 15 and 16
        pr = _make_pr(number=6)
        generated = [
            GeneratedNote(
                slug="abstract-menu-template-method",
                title="Abstract Classes & Template Method (Chapter 4)",
                chapter_refs=["4.5 Abstract Classes & Abstract Methods"],
                markdown_content="# Abstract Classes\n",
            ),
            GeneratedNote(
                slug="ordered-catch-blocks",
                title="Ordered Catch Blocks (Chapter 6)",
                chapter_refs=["6.4 Exception Control Flow Mechanics"],
                markdown_content="# Ordered Catch Blocks\n",
            ),
        ]
        created = save_generated_notes(generated, pr, self.notes_dir, state, self.state_file)
        self.assertEqual(
            created,
            ["15-abstract-menu-template-method.md", "16-ordered-catch-blocks.md"],
        )
        self.assertEqual(state["next_index"], 17)

        # Run 1 (max_files=2): MUST send 15 and 16 immediately!
        batch1 = select_files_to_send(self.notes_dir, state, max_files=2)
        self.assertEqual(
            batch1,
            ["15-abstract-menu-template-method.md", "16-ordered-catch-blocks.md"],
        )
        for fname in batch1:
            mark_file_sent(fname, state, self.state_file)

        # Run 2 (no new PR notes left): MUST resume backlog at 04 and 05!
        batch2 = select_files_to_send(self.notes_dir, state, max_files=2)
        self.assertEqual(batch2, ["04-topic-4.md", "05-topic-5.md"])

    def test_single_pr_note_fills_remaining_slot_with_backlog(self) -> None:
        state = load_state(self.state_file)
        for idx in (1, 2, 3):
            mark_file_sent(f"{idx:02d}-topic-{idx}.md", state, self.state_file)

        save_generated_notes(
            [
                GeneratedNote(
                    slug="try-with-resources",
                    title="Try-with-Resources (Chapter 6)",
                    chapter_refs=["6.5 Resource Management"],
                    markdown_content="# Try-with-Resources\n",
                )
            ],
            _make_pr(number=7),
            self.notes_dir,
            state,
            self.state_file,
        )

        # 1 PR note + 1 backlog note = 2 files total
        batch = select_files_to_send(self.notes_dir, state, max_files=2)
        self.assertEqual(batch, ["15-try-with-resources.md", "04-topic-4.md"])

    def test_three_pr_notes_span_two_runs_before_backlog(self) -> None:
        state = load_state(self.state_file)
        for idx in (1, 2, 3):
            mark_file_sent(f"{idx:02d}-topic-{idx}.md", state, self.state_file)

        save_generated_notes(
            [
                GeneratedNote("concept-a", "Concept A", ["4.1"], "# A\n"),
                GeneratedNote("concept-b", "Concept B", ["4.2"], "# B\n"),
                GeneratedNote("concept-c", "Concept C", ["4.3"], "# C\n"),
            ],
            _make_pr(number=8),
            self.notes_dir,
            state,
            self.state_file,
        )

        batch1 = select_files_to_send(self.notes_dir, state, max_files=2)
        self.assertEqual(batch1, ["15-concept-a.md", "16-concept-b.md"])
        for fname in batch1:
            mark_file_sent(fname, state, self.state_file)

        batch2 = select_files_to_send(self.notes_dir, state, max_files=2)
        self.assertEqual(batch2, ["17-concept-c.md", "04-topic-4.md"])

    def test_extract_note_number(self) -> None:
        self.assertEqual(extract_note_number("01-what-is-maven.md"), 1)
        self.assertEqual(extract_note_number("15-try-with-resources.md"), 15)
        self.assertEqual(extract_note_number("100-advanced.md"), 100)
        self.assertIsNone(extract_note_number("README.md"))


class TestSenderAndCaptions(unittest.TestCase):
    def test_format_caption_pr_and_backlog(self) -> None:
        pr_caption = format_caption(
            "15-abstract-menu.md",
            {
                "title": "Abstract Classes & Template Method",
                "pr_number": 7,
                "pr_author": "worku404",
            },
        )
        self.assertEqual(
            pr_caption,
            "Note #15 — Abstract Classes & Template Method (PR #7 by @worku404)",
        )

        backlog_caption = format_caption(
            "04-class-with-static-method.md",
            {"title": "Course Concept: Class with Static Methods (Chapters 2 & 3)"},
        )
        self.assertEqual(
            backlog_caption,
            "Note #04 — Course Concept: Class with Static Methods (Chapters 2 & 3)",
        )

    @patch("medfinder_notes.sender.requests.post")
    def test_send_telegram_document_success_and_error(self, mock_post: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc_path = Path(tmp) / "15-demo.md"
            doc_path.write_text("# Demo\n", encoding="utf-8")

            ok_resp = MagicMock(ok=True, status_code=200)
            ok_resp.json.return_value = {"ok": True, "result": {"message_id": 42}}
            mock_post.return_value = ok_resp

            send_telegram_document("TOKEN", "12345", doc_path, caption="Note #15 — Demo")
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            self.assertEqual(args[0], "https://api.telegram.org/botTOKEN/sendDocument")
            self.assertEqual(kwargs["data"], {"chat_id": "12345", "caption": "Note #15 — Demo"})

            mock_post.reset_mock()
            send_telegram_document(
                "TOKEN", "-1004379841591", doc_path, caption="Note #15 — Demo", thread_id=404
            )
            args, kwargs = mock_post.call_args
            self.assertEqual(
                kwargs["data"],
                {
                    "chat_id": "-1004379841591",
                    "caption": "Note #15 — Demo",
                    "message_thread_id": "404",
                },
            )

            bad_resp = MagicMock(ok=False, status_code=400, text="Bad Request")
            bad_resp.json.return_value = {"ok": False}
            mock_post.return_value = bad_resp
            with self.assertRaises(RuntimeError):
                send_telegram_document("TOKEN", "12345", doc_path)

    @patch("medfinder_notes.sender.time.sleep")
    @patch("medfinder_notes.sender.requests.post")
    def test_send_telegram_document_retries_on_timeout_and_429(
        self, mock_post: MagicMock, mock_sleep: MagicMock
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc_path = Path(tmp) / "16-demo.md"
            doc_path.write_text("# Demo\n", encoding="utf-8")

            rate_limited = MagicMock(ok=False, status_code=429, text="Too Many Requests")
            rate_limited.json.return_value = {"ok": False, "parameters": {"retry_after": 3}}
            ok_resp = MagicMock(ok=True, status_code=200)
            ok_resp.json.return_value = {"ok": True, "result": {"message_id": 99}}

            mock_post.side_effect = [
                requests.exceptions.ConnectTimeout("Connection to api.telegram.org timed out"),
                rate_limited,
                ok_resp,
            ]

            send_telegram_document(
                "TOKEN",
                "-1004379841591",
                doc_path,
                caption="Note #16 — Demo",
                thread_id=404,
                max_retries=4,
                initial_backoff=1.0,
            )
            self.assertEqual(mock_post.call_count, 3)
            self.assertEqual(mock_sleep.call_args_list[0].args, (1.0,))
            self.assertEqual(mock_sleep.call_args_list[1].args, (3.0,))


class TestNoteGenerator(unittest.TestCase):
    def test_sanitize_slug_and_double_escape_repair(self) -> None:
        self.assertEqual(sanitize_slug("15-Try_With_Resources.md"), "try-with-resources")
        self.assertEqual(sanitize_slug("   ", fallback_title="Chapter 4: Inheritance!"), "chapter-4-inheritance")
        self.assertEqual(_repair_double_escaping("# Title\\n\\nBody"), "# Title\n\nBody")
        self.assertEqual(
            _repair_double_escaping("# Title\nPrint literal \\n here"),
            "# Title\nPrint literal \\n here",
        )

    @patch("medfinder_notes.note_generator.genai.Client")
    def test_generate_notes_failover_and_cap(self, mock_client_cls: MagicMock) -> None:
        failing_client = MagicMock()
        failing_client.models.generate_content.side_effect = RuntimeError("429 Quota exceeded")

        good_payload = {
            "notes": [
                {
                    "slug": "abstract-menu",
                    "title": "Abstract Classes (Chapter 4)",
                    "chapter_refs": ["4.5 Abstract Classes"],
                    "markdown_content": "# Abstract Classes\\n\\nExplanation.",
                },
                {
                    "slug": "template-method",
                    "title": "Template Method (Chapter 4)",
                    "chapter_refs": ["4.5 Abstract Classes"],
                    "markdown_content": "# Template Method\n\nExplanation.",
                },
                {
                    "slug": "extra-third",
                    "title": "Should Be Capped",
                    "chapter_refs": ["4.6"],
                    "markdown_content": "# Third\n",
                },
            ]
        }
        ok_response = MagicMock(text=json.dumps(good_payload))
        good_client = MagicMock()
        good_client.models.generate_content.return_value = ok_response

        mock_client_cls.side_effect = [failing_client, good_client]

        notes = generate_notes_for_pr(
            pr=_make_pr(number=6),
            diff_text="+public abstract class Menu {}",
            topics_text="Chapter 4: Inheritance & Abstract Classes",
            existing_titles=[],
            max_notes=2,
            api_keys=["bad-key", "good-key"],
            model_name="gemini-2.5-flash",
            max_retries=1,
            initial_backoff=0.0,
        )

        self.assertEqual(len(notes), 2)
        self.assertEqual(notes[0].slug, "abstract-menu")
        self.assertIn("\n\n", notes[0].markdown_content)
        self.assertEqual(notes[1].slug, "template-method")


class TestEndToEndPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.notes_dir = self.root / "notes"
        self.notes_dir.mkdir()
        self.topics_file = self.root / "topics.md"
        self.topics_file.write_text("Chapter 4: Abstract Classes\n", encoding="utf-8")
        self.state_file = self.root / "state.json"

        (self.notes_dir / "01-what-is-maven.md").write_text("# What is Maven?\n", encoding="utf-8")
        (self.notes_dir / "02-what-is-pom-xml.md").write_text("# What is pom.xml?\n", encoding="utf-8")

        state = default_state()
        state["next_index"] = 3
        state["processed_prs"]["5"] = {"baseline": True, "notes": []}
        state["note_metadata"] = {
            "01-what-is-maven.md": {"title": "What is Maven?", "source": "backlog"},
            "02-what-is-pom-xml.md": {"title": "What is pom.xml?", "source": "backlog"},
        }
        save_state(state, self.state_file)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    @patch("medfinder_notes.main.get_telegram_credentials", return_value=("BOT_TOKEN", "CHAT_ID", 404))
    @patch("medfinder_notes.main.send_telegram_document")
    @patch("medfinder_notes.main.generate_notes_for_pr")
    @patch("medfinder_notes.main.fetch_pr_relevant_files")
    @patch("medfinder_notes.main.fetch_pull_requests")
    @patch("medfinder_notes.main.get_github_token", return_value=None)
    def test_sync_merged_only_and_priority_delivery_with_crash_recovery(
        self,
        _mock_gh_token: MagicMock,
        mock_fetch_prs: MagicMock,
        mock_fetch_files: MagicMock,
        mock_generate: MagicMock,
        mock_send: MagicMock,
        _mock_tg_creds: MagicMock,
    ) -> None:
        mock_fetch_prs.return_value = [
            _make_pr(number=5, merged_at="2026-11-17T00:00:00Z"),  # already baseline
            _make_pr(number=6, author="wubettamrat525-prog", merged_at="2026-11-18T11:00:00Z"),  # new merged
            _make_pr(number=7, state="open", merged_at=None),  # open -> must skip!
        ]
        mock_fetch_files.return_value = [
            PrFileChange("src/main/java/medfinder/console/Menu.java", "added", 50, 0, "+abstract class Menu {}")
        ]
        mock_generate.return_value = [
            GeneratedNote("abstract-menu", "Abstract Classes", ["4.5"], "# Abstract Classes\n"),
        ]

        # Stage 1: Sync PRs -> only PR #6 analyzed; creates 03-abstract-menu.md
        created = sync_prs(
            notes_dir=self.notes_dir,
            topics_file=self.topics_file,
            state_file=self.state_file,
            trigger_mode="merged",
        )
        self.assertEqual(created, ["03-abstract-menu.md"])
        mock_fetch_files.assert_called_once_with("worku404", "MedFinder-java", 6, None)
        self.assertTrue((self.notes_dir / "03-abstract-menu.md").is_file())

        # Stage 2 (simulate Telegram failure on the 2nd file in the batch):
        # Expected order: 03-abstract-menu.md (PR priority), then 01-what-is-maven.md (backlog)
        mock_send.side_effect = [None, RuntimeError("Telegram temporary timeout")]

        with self.assertRaises(RuntimeError):
            deliver_queued_notes(
                notes_dir=self.notes_dir,
                state_file=self.state_file,
                max_files=2,
                pause_seconds=0,
            )

        # Verify crash safety: file #1 was persisted as sent; file #2 stays unsent for retry!
        state_after_crash = load_state(self.state_file)
        self.assertEqual(state_after_crash["sent_files"], ["03-abstract-menu.md"])
        self.assertEqual(state_after_crash["pr_note_queue"], [])

        # Verify caption of file #1
        first_call = mock_send.call_args_list[0]
        self.assertEqual(
            first_call.kwargs["caption"],
            "Note #03 — Abstract Classes (PR #6 by @wubettamrat525-prog)",
        )

        # Next run retries cleanly: delivers 01-what-is-maven.md and 02-what-is-pom-xml.md
        mock_send.side_effect = None
        mock_send.reset_mock()
        delivered = deliver_queued_notes(
            notes_dir=self.notes_dir,
            state_file=self.state_file,
            max_files=2,
            pause_seconds=0,
        )
        self.assertEqual(delivered, ["01-what-is-maven.md", "02-what-is-pom-xml.md"])

    @patch("medfinder_notes.main.send_telegram_document")
    @patch("medfinder_notes.main.fetch_pull_requests", return_value=[])
    @patch("medfinder_notes.main.get_github_token", return_value=None)
    def test_dry_run_makes_no_mutations(
        self,
        _mock_gh_token: MagicMock,
        _mock_fetch_prs: MagicMock,
        mock_send: MagicMock,
    ) -> None:
        before = self.state_file.read_text(encoding="utf-8")
        sync_prs(
            notes_dir=self.notes_dir,
            topics_file=self.topics_file,
            state_file=self.state_file,
            dry_run=True,
        )
        chosen = deliver_queued_notes(
            notes_dir=self.notes_dir,
            state_file=self.state_file,
            max_files=2,
            dry_run=True,
        )
        self.assertEqual(chosen, ["01-what-is-maven.md", "02-what-is-pom-xml.md"])
        mock_send.assert_not_called()
        self.assertEqual(self.state_file.read_text(encoding="utf-8"), before)


if __name__ == "__main__":
    unittest.main()
