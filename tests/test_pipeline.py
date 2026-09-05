"""Automated test suite for Daily Telegram Software Engineering Micro-Lesson Bot.

Covers:
- Seed topics integrity (uniqueness, non-emptiness).
- Prompt schema contract and placeholder interpolation.
- Deterministic state cursor advancement, resilience, and wrap-around.
- AST Markdown-to-Entities compilation (bold, italic, code block, spoiler).
- Technical concept image generation via Hugging Face Router Inference.
- Telegram Bot API delivery payload contract (sendPhoto multipart & sendMessage entities).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.prompts import LESSON_FIELDS, LESSON_SCHEMA, PROMPT_TEMPLATE
from src.topics import SEED_TOPICS
from src.topic_scheduler import advance_state, get_current_topic
from src.telegram_formatter import TELEGRAM_MAX_MESSAGE_LENGTH, format_lesson


class TestSeedsIntegrity(unittest.TestCase):
    """Validate seeds.py topic definition invariants."""

    def test_seeds_not_empty(self) -> None:
        self.assertGreater(len(SEED_TOPICS), 0, "SEED_TOPICS list cannot be empty.")
        for topic in SEED_TOPICS:
            self.assertIsInstance(topic, str)
            self.assertTrue(topic.strip(), "Topic string cannot be blank.")

    def test_seeds_uniqueness(self) -> None:
        self.assertEqual(
            len(SEED_TOPICS),
            len(set(SEED_TOPICS)),
            "Duplicate topics found in SEED_TOPICS.",
        )


class TestPromptContract(unittest.TestCase):
    """Validate prompt engineering and schema synchronization."""

    def test_schema_requires_all_fields(self) -> None:
        self.assertEqual(
            set(LESSON_SCHEMA["required"]),
            set(LESSON_FIELDS),
            "LESSON_SCHEMA required properties must mirror LESSON_FIELDS.",
        )

    def test_prompt_template_interpolates_cleanly(self) -> None:
        rendered = PROMPT_TEMPLATE.format(title="Binary Search Invariants")
        self.assertIn("Binary Search Invariants", rendered)
        self.assertNotIn("{title}", rendered)


class TestStateProgression(unittest.TestCase):
    """Validate topic cursor progression, wrap-around, and atomic persistence."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp_dir.name) / "state.json"
        self.mock_seeds = ["Topic A", "Topic B", "Topic C"]

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_initial_state_without_file(self) -> None:
        index, topic = get_current_topic(self.mock_seeds, self.state_path)
        self.assertEqual(index, 0)
        self.assertEqual(topic, "Topic A")

    def test_sequential_advancement(self) -> None:
        idx1 = advance_state(0, self.mock_seeds, self.state_path)
        self.assertEqual(idx1, 1)

        index, topic = get_current_topic(self.mock_seeds, self.state_path)
        self.assertEqual(index, 1)
        self.assertEqual(topic, "Topic B")

    def test_circular_wrap_around(self) -> None:
        next_idx = advance_state(2, self.mock_seeds, self.state_path)
        self.assertEqual(next_idx, 0)

        index, topic = get_current_topic(self.mock_seeds, self.state_path)
        self.assertEqual(index, 0)
        self.assertEqual(topic, "Topic A")

    def test_resilience_to_list_shrinkage(self) -> None:
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump({"current_index": 5}, f)

        index, topic = get_current_topic(self.mock_seeds, self.state_path)
        self.assertEqual(index, 2)
        self.assertEqual(topic, "Topic C")


class TestTelegramFormatter(unittest.TestCase):
    """Validate AST Markdown-to-Entities compilation."""

    def test_entities_generation(self) -> None:
        data = {
            "title": "The GIL in CPython",
            "concept_summary": "Mutual exclusion lock protecting Python object memory.",
            "explanation": "Prevents race conditions in refcounting.\n\n### Mechanical Trade-offs\n\n1. **Cache Locality**\n\n```python\nimport sys\n```",
            "key_takeaway": "The GIL locks interpreter state.",
        }
        text, entities = format_lesson(data)

        self.assertIsInstance(text, str)
        self.assertIsInstance(entities, list)

        self.assertNotIn("###", text)
        self.assertNotIn("```", text)

        entity_types = {e["type"] for e in entities}
        self.assertIn("bold", entity_types)
        self.assertIn("italic", entity_types)
        self.assertIn("pre", entity_types)
        self.assertIn("blockquote", entity_types)
        self.assertNotIn("spoiler", entity_types)
        self.assertNotIn("💡", text)
        self.assertNotIn("Key Takeaway", text)

    def test_length_bounded(self) -> None:
        huge_explanation = "A" * 6000
        data = {
            "title": "Large Post",
            "concept_summary": "Summary",
            "explanation": huge_explanation,
            "key_takeaway": "Takeaway",
        }
        text, entities = format_lesson(data)
        self.assertLessEqual(len(text), TELEGRAM_MAX_MESSAGE_LENGTH)

    def test_internal_image_prompt_is_not_rendered(self) -> None:
        internal_prompt = "SECRET INTERNAL VISUAL METAPHOR"
        data = {
            "title": "Queues",
            "concept_summary": "FIFO ordering",
            "explanation": "Items leave in arrival order.",
            "key_takeaway": "First in, first out.",
            "image_prompt": internal_prompt,
        }

        text, _ = format_lesson(data)

        self.assertNotIn(internal_prompt, text)


class TestImageGenerator(unittest.TestCase):
    """Validate Hugging Face concept image generation mechanics."""

    @patch("requests.post")
    def test_generate_concept_image_success(self, mock_post: MagicMock) -> None:
        from src.image_generator import generate_concept_image

        mock_post.return_value.status_code = 200
        mock_post.return_value.content = b"fake_png_data"

        lesson = {
            "title": "Hash Tables",
            "concept_summary": "Maps keys to values",
            "image_prompt": "Key-value hashing pipeline with hash function block and bucket array",
        }
        result = generate_concept_image(lesson)
        self.assertEqual(result, b"fake_png_data")

        payload = mock_post.call_args.kwargs["json"]
        self.assertIn(lesson["image_prompt"], payload["inputs"])
        self.assertNotIn(lesson["title"], payload["inputs"])
        self.assertNotIn(lesson["concept_summary"], payload["inputs"])
        self.assertIn("minimalist", payload["inputs"])
        self.assertIn("negative_prompt", payload["parameters"])
        self.assertIn("photorealistic", payload["parameters"]["negative_prompt"])
        self.assertNotIn("diagram", payload["parameters"]["negative_prompt"])

    def test_build_image_prompt_fallback(self) -> None:
        from src.image_generator import build_image_prompt

        pos, neg = build_image_prompt({})
        self.assertIn("System architecture diagram", pos)
        self.assertIn("minimalist", pos)
        self.assertIn("photorealistic", neg)

    @patch("time.sleep")
    @patch("requests.post")
    def test_generate_concept_image_failure(self, mock_post: MagicMock, mock_sleep: MagicMock) -> None:
        from src.image_generator import generate_concept_image

        mock_post.return_value.status_code = 503
        mock_post.return_value.text = "Model warming up"
        mock_post.return_value.json.return_value = {"estimated_time": 10.0}

        with self.assertRaises(RuntimeError) as ctx:
            generate_concept_image(
                {"image_prompt": "System architecture diagram"},
                tokens=["mock_tok1"],
                max_retries=2,
                initial_backoff=0.01,
            )

        self.assertIn("Hugging Face image generation failed", str(ctx.exception))
        self.assertEqual(mock_post.call_count, 2)
        self.assertGreaterEqual(mock_sleep.call_count, 1)

    @patch("time.sleep")
    @patch("requests.post")
    def test_generate_concept_image_retry_then_succeed(self, mock_post: MagicMock, mock_sleep: MagicMock) -> None:
        from src.image_generator import generate_concept_image

        # First attempt returns 503 (model warming up), second attempt succeeds with 200
        fail_resp = MagicMock(status_code=503, text="Model warming up")
        fail_resp.json.return_value = {"estimated_time": 12.0}
        success_resp = MagicMock(status_code=200, content=b"recovered_png_bytes")
        mock_post.side_effect = [fail_resp, success_resp]

        result = generate_concept_image(
            {"image_prompt": "Pipeline retry test"},
            tokens=["mock_tok1"],
            max_retries=3,
            initial_backoff=0.01,
        )
        self.assertEqual(result, b"recovered_png_bytes")
        self.assertEqual(mock_post.call_count, 2)
        self.assertGreaterEqual(mock_sleep.call_count, 1)

    @patch("time.sleep")
    @patch("requests.post")
    def test_generate_concept_image_token_failover(self, mock_post: MagicMock, mock_sleep: MagicMock) -> None:
        from src.image_generator import generate_concept_image

        # Token 1 hits 429 Rate Limit, Token 2 succeeds immediately with 200 OK
        resp_tok1 = MagicMock(status_code=429, text="Rate limit exceeded")
        resp_tok2 = MagicMock(status_code=200, content=b"token2_image_bytes")
        mock_post.side_effect = [resp_tok1, resp_tok2]

        result = generate_concept_image(
            {"image_prompt": "Token failover test"},
            tokens=["tok_primary", "tok_secondary"],
            max_retries=1,
            initial_backoff=0.01,
        )

        self.assertEqual(result, b"token2_image_bytes")
        self.assertEqual(mock_post.call_count, 2)
        # Verify first call used tok_primary and second call used tok_secondary
        call1_auth = mock_post.call_args_list[0].kwargs["headers"]["Authorization"]
        call2_auth = mock_post.call_args_list[1].kwargs["headers"]["Authorization"]
        self.assertEqual(call1_auth, "Bearer tok_primary")
        self.assertEqual(call2_auth, "Bearer tok_secondary")


class TestBotDelivery(unittest.TestCase):
    """Validate Telegram API delivery mechanics using sendPhoto and sendMessage."""

    @patch("requests.post")
    def test_successful_delivery_with_entities(self, mock_post: MagicMock) -> None:
        from src.pipeline import send_telegram_message

        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {"ok": True, "result": {"message_id": 42}}

        mock_entities = [{"type": "bold", "offset": 0, "length": 10}]
        send_telegram_message("dummy_token", "-100123456", "Plain Text", mock_entities)

        mock_post.assert_called_once_with(
            "https://api.telegram.org/botdummy_token/sendMessage",
            json={
                "chat_id": "-100123456",
                "text": "Plain Text",
                "entities": mock_entities,
                "disable_web_page_preview": True,
            },
            timeout=15,
        )
        self.assertNotIn("parse_mode", mock_post.call_args.kwargs["json"])

    @patch("requests.post")
    def test_successful_photo_delivery(self, mock_post: MagicMock) -> None:
        from src.pipeline import send_telegram_photo

        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {"ok": True, "result": {"message_id": 43}}

        fake_photo = b"binary_image_stream"
        send_telegram_photo("dummy_token", "-100123456", fake_photo)

        mock_post.assert_called_once()
        url = mock_post.call_args.args[0]
        self.assertEqual(url, "https://api.telegram.org/botdummy_token/sendPhoto")
        self.assertEqual(mock_post.call_args.kwargs["data"]["chat_id"], "-100123456")
        self.assertNotIn("caption", mock_post.call_args.kwargs["data"])
        self.assertIn("photo", mock_post.call_args.kwargs["files"])

    @patch("requests.post")
    def test_fail_fast_on_api_error(self, mock_post: MagicMock) -> None:
        from src.pipeline import send_telegram_message

        mock_post.return_value.ok = False
        mock_post.return_value.status_code = 400
        mock_post.return_value.text = '{"ok":false,"description":"Bad Request: chat not found"}'
        mock_post.return_value.json.return_value = {"ok": False}

        with self.assertRaises(RuntimeError) as ctx:
            send_telegram_message("dummy_token", "-100123456", "Plain Text", [])

        self.assertIn("Telegram API delivery failed", str(ctx.exception))


class TestDoubleEscapeRepair(unittest.TestCase):
    """Validate the guarded decode-layer repair of double-escaped model output.

    These tests exercise the FULL decode path (generate_lesson -> json.loads ->
    _repair_lesson_fields) rather than a pre-cleaned dict, because the defect
    lives in decoding, not formatting. A prior formatter-only test could not have
    caught it.
    """

    def _mock_gemini(self, raw_text: str):
        """Patch the Gemini client so generate_content returns raw_text verbatim."""
        fake_response = MagicMock()
        fake_response.text = raw_text
        fake_client = MagicMock()
        fake_client.models.generate_content.return_value = fake_response
        return patch("src.lesson_generator.genai.Client", return_value=fake_client)

    def test_double_escaped_newlines_repaired_into_pre_block(self) -> None:
        # Regression: Gemini double-escapes newlines, so the JSON string carries
        # the two literal characters backslash+n. json.loads would otherwise yield
        # literal "\n" text that breaks the CommonMark fence into an inline span.
        from src.lesson_generator import generate_lesson

        # Build the exact byte sequence a double-escaping model emits: within the
        # JSON payload the newline is written as "\\n", i.e. backslash + backslash
        # + n at the Python source level.
        b = chr(96) * 3  # ```
        raw_json = (
            '{'
            '"title": "The GIL", '
            '"concept_summary": "Interpreter lock.", '
            '"explanation": "Non-atomic ops race.\\\\n\\\\n'
            + b + 'python\\\\nimport threading\\\\nx = 0\\\\n' + b + '", '
            '"key_takeaway": "Use explicit locks.", '
            '"image_prompt": "A single lane gate."'
            '}'
        )

        with self._mock_gemini(raw_json):
            lesson = generate_lesson("prompt")

        # The decoded explanation must contain REAL newlines, not literal backslash-n.
        self.assertNotIn("\\n", lesson["explanation"])
        self.assertIn("\n", lesson["explanation"])

        # And it must now compile into a proper Telegram 'pre' code block.
        _text, entities = format_lesson(lesson)
        pre = [e for e in entities if e["type"] == "pre"]
        self.assertTrue(pre, "Expected a 'pre' code block entity after repair.")
        self.assertEqual(pre[0].get("language"), "python")

    def test_legitimate_backslash_n_content_is_not_corrupted(self) -> None:
        # Negative test: a lesson whose content legitimately mentions the literal
        # two-character sequence backslash+n (e.g. a regex lesson) already has REAL
        # newlines, so the guard must leave the literal text untouched.
        from src.lesson_generator import generate_lesson

        # Real newlines are present (written as \\n in this Python source -> one
        # real newline in the JSON string), plus a legitimate literal "\n" token
        # inside the prose (written as \\\\n -> backslash+n after json.loads).
        raw_json = (
            '{'
            '"title": "Regex newlines", '
            '"concept_summary": "Matching line breaks.", '
            '"explanation": "Line one.\\nUse the token \\\\n to match a newline.\\nLine three.", '
            '"key_takeaway": "Escape carefully.", '
            '"image_prompt": "Two stacked ribbons."'
            '}'
        )

        with self._mock_gemini(raw_json):
            lesson = generate_lesson("prompt")

        # The legitimate literal backslash-n token must survive verbatim.
        self.assertIn("\\n", lesson["explanation"])
        # Real newlines from the content are preserved too.
        self.assertIn("Line one.\nUse", lesson["explanation"])


class TestGeminiRetries(unittest.TestCase):
    """Validate application-level retry mechanics for Gemini lesson generation."""

    @patch("time.sleep")
    @patch("src.lesson_generator.genai.Client")
    def test_gemini_retry_then_succeed(self, mock_client_cls: MagicMock, mock_sleep: MagicMock) -> None:
        from src.lesson_generator import generate_lesson

        fake_client = MagicMock()
        mock_client_cls.return_value = fake_client

        # First call fails with a transient exception, second call succeeds with valid JSON
        valid_response = MagicMock()
        valid_response.text = '{"title": "T", "concept_summary": "S", "explanation": "E", "key_takeaway": "K", "image_prompt": "I"}'

        fake_client.models.generate_content.side_effect = [
            RuntimeError("Transient network drop"),
            valid_response,
        ]

        lesson = generate_lesson("test prompt", api_keys=["mock_key"], max_retries=3, initial_backoff=0.01)
        self.assertEqual(lesson["title"], "T")
        self.assertEqual(fake_client.models.generate_content.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("time.sleep")
    @patch("src.lesson_generator.genai.Client")
    def test_gemini_exhausts_retries_and_raises(self, mock_client_cls: MagicMock, mock_sleep: MagicMock) -> None:
        from src.lesson_generator import generate_lesson

        fake_client = MagicMock()
        mock_client_cls.return_value = fake_client
        fake_client.models.generate_content.side_effect = RuntimeError("Google API unavailable")

        with self.assertRaises(RuntimeError) as ctx:
            generate_lesson("test prompt", api_keys=["mock_key"], max_retries=2, initial_backoff=0.01)

        self.assertIn("Gemini lesson generation failed after 2 rounds", str(ctx.exception))
        self.assertEqual(fake_client.models.generate_content.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("time.sleep")
    @patch("src.lesson_generator.genai.Client")
    def test_gemini_key_failover(self, mock_client_cls: MagicMock, mock_sleep: MagicMock) -> None:
        from src.lesson_generator import generate_lesson

        fake_client = MagicMock()
        mock_client_cls.return_value = fake_client

        # Key 1 fails, Key 2 succeeds immediately on attempt 2
        valid_response = MagicMock()
        valid_response.text = '{"title": "T", "concept_summary": "S", "explanation": "E", "key_takeaway": "K", "image_prompt": "I"}'
        fake_client.models.generate_content.side_effect = [
            RuntimeError("Key 1 quota exceeded"),
            valid_response,
        ]

        lesson = generate_lesson("test prompt", api_keys=["key1", "key2"], max_retries=1, initial_backoff=0.01)
        self.assertEqual(lesson["title"], "T")
        self.assertEqual(fake_client.models.generate_content.call_count, 2)
        # Verify first call used key1 and second call used key2
        self.assertEqual(mock_client_cls.call_args_list[0].kwargs["api_key"], "key1")
        self.assertEqual(mock_client_cls.call_args_list[1].kwargs["api_key"], "key2")
        mock_sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
