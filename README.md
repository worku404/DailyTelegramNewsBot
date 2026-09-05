# Daily Telegram Software Engineering Micro-Lesson Bot (Gemini + Hugging Face)

An automated bot that generates and publishes a daily intermediate-to-advanced software engineering micro-lesson to a configured Telegram channel or group. 

Powered by the **Google GenAI SDK** (`google-genai`), **Hugging Face Router Inference** (`Stable Diffusion 3 Medium`), **`telegramify-markdown`**, and the Telegram Bot API. It runs on a daily schedule via GitHub Actions with zero dedicated server hosting costs.

---

## 1. System Architecture

```
  src/topics.py (SE topic list)
     │
     ▼
  state.json (tracks topic cursor)
     │
     ▼
  bot.py -> src/pipeline.py (orchestration)
     │
     ├──► src/lesson_generator.py ───────────────► Google Gemini API (structured lesson JSON)
     │
     ├──► src/image_generator.py ───► Hugging Face Inference (architecture diagram PNG)
     │
     ├──► src/telegram_formatter.py ─► telegramify-markdown (AST Markdown to MessageEntity objects)
     │
     └──► Telegram Bot API ─────► 1. sendPhoto (diagram + short title caption)
                                  2. sendMessage (full lesson + native entities)
```

### Execution Flow & Invariants
1. **Deterministic Sequential Traversal:** Topics are defined in [seeds.py](file:///c:/Users/hi/Downloads/python/DailyTelegramNewsBot/seeds.py). Each run processes **exactly one topic** per day.
2. **Two-Stage Telegram Delivery:** 
   * **Stage 1 (Media):** Concept diagram is sent via `sendPhoto` with a short title caption.
   * **Stage 2 (Text):** Full lesson body is sent via `sendMessage` using native AST entities.
   * *Rationale:* Bypasses Telegram's 1,024-character caption limit on photos while allowing rich 4,096-character lessons with syntax-highlighted code blocks.
3. **Fail-Fast Semantics:** The cursor in `state.json` only advances **after** successful delivery of both media and text. If any step fails, the script halts with a non-zero exit code and the topic is retried on the next execution.
4. **AST Entity Formatting (Zero-Escaping):** Uses `telegramify-markdown` to convert Markdown directly into Telegram `MessageEntity` objects with pre-calculated UTF-16 byte offsets. This eliminates escaping traps on special characters (`.`, `!`, `<`, `>`, `&`).

---

## 2. File Structure

```
telegram-news-bot/
├── bot.py                          # Thin entry-point shim → src.pipeline.main()
├── state.json                      # Persisted topic cursor (committed by CI)
├── requirements.txt                # Python dependencies
├── src/                            # Application package
│   ├── __init__.py
│   ├── config.py                   # Single Source of Truth (SSOT) configuration
│   ├── prompts.py                  # ALL model-facing prompts: lesson prompt+schema & image style/negative prompts
│   ├── lesson_generator.py         # Google GenAI client + decode/repair (was llm.py)
│   ├── image_generator.py          # Hugging Face image transport (imports prompts)
│   ├── telegram_formatter.py       # AST Markdown → Telegram MessageEntity compiler
│   ├── topics.py                   # Curated software engineering topic list (was seeds.py)
│   ├── topic_scheduler.py          # Topic cursor management & state persistence (was state.py)
│   └── pipeline.py                 # Orchestration + Telegram send helpers (was bot.py)
├── tests/
│   ├── __init__.py
│   └── test_pipeline.py            # Automated unit test suite
├── get_chat_id.py                  # One-time helper to discover chat_id
├── .env.example                    # Template for local environment secrets
├── .gitignore                      # Keeps .env, .tmp, and virtualenvs out of git
└── .github/workflows/daily-news.yml# GitHub Actions daily cron schedule (06:00 UTC)
```

---

## 3. Step-by-Step Setup

### Step 1 — Create your Telegram Bot
1. Open Telegram and start a chat with **@BotFather**.
2. Send `/newbot` and follow the prompts to choose a display name and username.
3. BotFather issues a token formatted like `123456789:AAExampleTokenText`. This is your `TELEGRAM_BOT_TOKEN`.

### Step 2 — Add the Bot to your Channel or Group
* **Channel:** Open Channel Settings → Administrators → Add Admin → Search for your bot username → Grant "Post Messages" permission.
* **Group:** Add the bot as a group member (or administrator if member messages are restricted).

### Step 3 — Discover your `chat_id`
1. Send a message into the channel or group where the bot was added.
2. Run `get_chat_id.py` (or check via the Telegram web client).
3. The resulting numeric ID (e.g. `-1001234567890` for channels/supergroups) is your `TELEGRAM_CHAT_ID`.

### Step 4 — API Keys
1. **Google Gemini:** Visit [Google AI Studio](https://aistudio.google.com/) and generate a `GEMINI_API_KEY`.
2. **Hugging Face:** Visit [Hugging Face Settings Tokens](https://huggingface.co/settings/tokens) and generate a read token for `HF_IMAGE_TOKEN`.

### Step 5 — Configure Secrets

#### Local Testing
Copy `.env.example` to `.env` and fill in real values:
```bash
cp .env.example .env
```
Fill in the required variables:
```env
GEMINI_API_KEY=your_real_gemini_api_key
GEMINI_MODEL_NAME=gemini-3.5-flash
HF_IMAGE_TOKEN=your_real_hf_token
TELEGRAM_BOT_TOKEN=your_real_telegram_token
TELEGRAM_CHAT_ID=-1001234567890
```

#### Production (GitHub Actions)
Go to your GitHub repository → **Settings → Secrets and variables → Actions → New repository secret**, and create:
* `GEMINI_API_KEY`
* `GEMINI_MODEL_NAME` (e.g., `gemini-3.5-flash`)
* `HF_IMAGE_TOKEN`
* `TELEGRAM_BOT_TOKEN`
* `TELEGRAM_CHAT_ID`

---

## 4. Telegram Formatting & Media Hierarchy

1. **Concept Diagram Card:** Synthesized via Stable Diffusion 3 Medium and delivered as a high-contrast visual preview.
2. **Native Message Entities:** Formatted with typography primitives:
   * **Title:** Bold header
   * **Summary:** Italic hook
   * **Subheadings:** Bold section titles
   * **Lists:** Numbered list items with bold labels
   * **Code Blocks:** Syntax-highlighted `<pre><code>` blocks with copy buttons
   * **Key Takeaway:** Tap-to-reveal spoiler

---

## 5. Topic Progression & State Management

All topics are maintained in [seeds.py](file:///c:/Users/hi/Downloads/python/DailyTelegramNewsBot/seeds.py) as a clean Python list:

```python
SEED_TOPICS = [
    "Hash tables: collision resolution (chaining vs. open addressing)",
    "The GIL: what it actually locks and what it doesn't",
    "Deadlock: the four Coffman conditions",
    ...
]
```

* **Persistence:** State is tracked in `state.json`.
* **Automated CI/CD Commit:** In GitHub Actions, the workflow has `contents: write` permissions. Upon completing the daily run, it automatically commits the updated `state.json` back to your repository with `[skip ci]`.
* **Wrap-Around:** After publishing the 31st topic, the next execution seamlessly restarts at topic index `0`.

---

## 6. Testing & Local Run

Run the automated test suite:
```bash
python -m unittest discover -s tests
```

Execute a live test locally:
```bash
python bot.py
```
