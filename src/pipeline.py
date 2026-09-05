"""Daily Telegram Software Engineering Micro-Lesson Bot.

Main orchestration module that:
1. Loads the sequential topic for today from seeds.py via state.py.
2. Invokes Google Gemini to generate a structured engineering micro-lesson.
3. Invokes Hugging Face to synthesize an architecture concept diagram.
4. Delivers the concept diagram (sendPhoto) .
5. Delivers the full lesson post (sendMessage) with AST MessageEntity structures.
6. Advances the topic cursor to the next sequential topic for tomorrow.

Design Decisions & Invariants:
- Fail-Fast Pipeline: No silent error masking or fake status codes. If any step
  (text generation, image synthesis, or Telegram delivery) fails, the program halts
  with a non-zero exit code so scheduled jobs (GitHub Actions) register the failure.
- Two-Stage Telegram Delivery: Dispatches the image via sendPhoto first, followed
  by the full lesson text via sendMessage. This avoids Telegram's 1,024-character
  caption limit on photos while allowing rich 4,096-character lessons.
- State Persistence: The topic cursor is only advanced after Telegram confirms
  successful delivery of both media and text, guaranteeing no topics are skipped on failure.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, List
import requests

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.image_generator import generate_concept_image
from src.lesson_generator import generate_lesson
from src.prompts import PROMPT_TEMPLATE
from src.topic_scheduler import advance_state, get_current_topic
from src.telegram_formatter import format_lesson

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("telegram_micro_lesson_bot")


def send_telegram_photo(
    bot_token: str,
    chat_id: str,
    photo_bytes: bytes,
) -> None:
    """Deliver an image to Telegram via the Bot API sendPhoto multipart endpoint.

    Args:
        bot_token: Secret bot authentication token.
        chat_id: Target channel or group identifier.
        photo_bytes: Raw binary image content.

    Raises:
        RuntimeError: If Telegram API returns an HTTP error or body indicates ok: false.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    data = {
        "chat_id": chat_id,
    }
    files = {
        "photo": ("diagram.png", photo_bytes, "image/png"),
    }

    response = requests.post(url, data=data, files=files, timeout=30)

    if not response.ok or not response.json().get("ok", False):
        raise RuntimeError(
            f"Telegram API photo delivery failed ({response.status_code}): {response.text}"
        )


def send_telegram_message(
    bot_token: str,
    chat_id: str,
    text: str,
    entities: List[dict[str, Any]],
) -> None:
    """Deliver a message to Telegram via the Bot API sendMessage endpoint using native entities.

    Args:
        bot_token: Secret bot authentication token.
        chat_id: Target channel or group identifier.
        text: Plain-text string with markup markers stripped.
        entities: List of serialized Telegram MessageEntity dictionaries.

    Raises:
        RuntimeError: If Telegram API returns an HTTP error or body indicates ok: false.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "entities": entities,
        "disable_web_page_preview": True,
    }

    response = requests.post(url, json=payload, timeout=15)

    if not response.ok or not response.json().get("ok", False):
        raise RuntimeError(
            f"Telegram API delivery failed ({response.status_code}): {response.text}"
        )


def main() -> int:
    """Execute the daily lesson publishing pipeline."""
    current_index, topic = get_current_topic()
    logger.info("Executing daily run for topic [%d]: %s", current_index, topic)

    prompt = PROMPT_TEMPLATE.format(title=topic)
    logger.info("Requesting structured lesson from Gemini...")
    lesson_data = generate_lesson(prompt)

    logger.info("Generating technical concept diagram via Hugging Face...")
    # image_prompt is internal-only: the generator consumes it, while the Telegram
    # formatter deliberately ignores it and publishes only the lesson fields.
    image_bytes = generate_concept_image(lesson_data)

    logger.info("Compiling lesson into Telegram plain text and entities...")
    formatted_text, entities = format_lesson(lesson_data)

    logger.info("Dispatching diagram to Telegram chat %s...", TELEGRAM_CHAT_ID)
    send_telegram_photo(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, image_bytes)

    logger.info("Dispatching full lesson text to Telegram chat %s...", TELEGRAM_CHAT_ID)
    send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, formatted_text, entities)
    logger.info("Successfully delivered diagram and lesson to Telegram.")

    # State advances strictly after network delivery succeeds so failed runs retry the same topic
    next_index = advance_state(current_index)
    logger.info("Advanced topic cursor to index [%d] for next run.", next_index)
    return 0


if __name__ == "__main__":
    sys.exit(main())
