"""
Helper script: find your Telegram chat_id.

You only need to run this ONCE, to discover the chat_id of the group or
channel you want the bot to post to. Once you have it, put it in your
secrets (see README.md) and you never need this script again.

HOW TO USE
----------
1. Add your bot to the target group/channel (as admin — see README).
2. Send ANY message in that group/channel (e.g. type "hello" and send it).
   - Telegram only keeps a short recent history of "updates" for the bot
     to fetch, so the message must be recent (within the last day or so,
     and not already "consumed" by a previous getUpdates call).
3. Run this script:
       TELEGRAM_BOT_TOKEN=your_token_here python get_chat_id.py
4. It prints every chat_id Telegram currently has on record for your bot.
"""

import os
import requests
from src.config import TELEGRAM_BOT_TOKEN


def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Set TELEGRAM_BOT_TOKEN in config.py first.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    updates = data.get("result", [])
    if not updates:
        print(
            "No updates found.\n"
            "-> Send a fresh message in your target group/channel, then re-run this script."
        )
        return

    seen_chat_ids = set()
    for update in updates:
        # A normal group message arrives under "message"; a channel post
        # arrives under "channel_post" instead — we check both.
        chat = (update.get("message") or update.get("channel_post") or {}).get("chat")
        if chat and chat["id"] not in seen_chat_ids:
            seen_chat_ids.add(chat["id"])
            name = chat.get("title") or chat.get("username") or "(no title)"
            print(f"chat_id: {chat['id']:<18}  type: {chat.get('type'):<12}  name: {name}")


if __name__ == "__main__":
    main()
