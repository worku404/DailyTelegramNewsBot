"""Test script to send a Markdown file to Telegram via the sendDocument API."""

from __future__ import annotations

from pathlib import Path
import sys

from decouple import config
import requests

FILE_PATH = Path(
    r"c:\class\OOP\groupProject\MedFinder-java\notes\course-concepts\01-class-with-static-method.md"
)


def send_telegram_document(bot_token: str, chat_id: str, file_path: Path) -> None:
    """Send a file as a document to Telegram using the Bot API sendDocument endpoint."""
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"

    with file_path.open("rb") as doc:
        response = requests.post(
            url,
            data={"chat_id": chat_id},
            files={"document": (file_path.name, doc, "text/markdown")},
            timeout=30,
        )

    if not response.ok or not response.json().get("ok", False):
        raise RuntimeError(
            f"Telegram API delivery failed ({response.status_code}): {response.text}"
        )


def main() -> int:
    bot_token: str = config("TEMP_11_DAY_REACT_BOT")
    chat_id: str = config("USER_CHAT_ID")

    send_telegram_document(bot_token, chat_id, FILE_PATH)
    print(f"Successfully sent '{FILE_PATH.name}' to chat {chat_id}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
