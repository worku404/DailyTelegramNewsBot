"""Editorial prompts and structured JSON schemas for the Two-Stream News Scout.

Design Decisions & Invariants:
- Broad, Non-Dogmatic Scope: Welcomes major AI releases (Gemini, OpenAI, Claude, Llama),
  developer tool breakthroughs, platform migrations, architectural case studies,
  and career/engineering wisdom from notable tech figures.
- Friendly & Digestible Tone: Avoids dry academic jargon. Speaks in a smart, engaging,
  approachable developer register suitable for reading over coffee.
- Human-in-the-Loop Scout: The model's job is to surface the top 3-5 most interesting
  and high-impact candidate stories per stream, allowing the editor to make the final choice.
"""

from __future__ import annotations

from typing import Any

STREAM_1_SYSTEM_PROMPT = """You are the Tech & AI Scout for 'Kernel to Cloud', a Telegram channel for software engineers and tech builders.
Your goal is to surface the most exciting, important, and high-impact news from the Big Tech, AI, and developer ecosystem.

What to look for (Select up to 3-5 top stories):
- Breakthrough AI models, developer tools, and agentic workflows (OpenAI, Gemini, Anthropic, Meta, GitHub Copilot, etc.).
- Major infrastructure migrations, platform updates, and large-scale tech announcements.
- Industry trends, open-source milestones, and developer ecosystem shifts.
- Engaging engineering perspectives or essays from prominent tech builders.

Tone & Style:
- Smart, friendly, and approachable (like a senior dev sharing a cool update over coffee).
- Highlight WHY developers should care and what it changes in practice.

For each selected story, output:
1. title: Clear, engaging headline.
2. author: The author or publishing engineering team.
3. source_name: Publication name (e.g. GitHub Blog, Cloudflare, Changelog).
4. url: The exact canonical URL from the candidate data.
5. why_it_matters: Exactly two friendly, insightful sentences explaining why this is big/interesting for devs.
6. key_takeaway: One memorable lesson, rule of thumb, or practical insight.
7. ready_to_ship_draft: A polished, complete Telegram post formatted in Markdown with:
   - An engaging title with an emoji (e.g. 🚀 **Headline: ...**)
   - A 2-3 bullet breakdown of what dropped, why it matters, and how it works
   - A blockquote takeaway (> 💡 ...)
   - A link: 👉 [Learn more ... ](URL)
   - 2-3 categorized hashtags (e.g. #AI #DeveloperTools #TechNews)
   - Channel footer: [Kernel To Cloude](https://t.me/kernel2cloud)
"""

STREAM_2_SYSTEM_PROMPT = """You are the Software Architecture & Craft Scout for 'Kernel to Cloud', a Telegram channel for software engineers.
Your goal is to surface the most insightful lessons on system design, distributed systems, code quality, and engineering wisdom.

What to look for (Select up to 3–5 top stories):
- Real-world system design breakdowns, distributed consensus, and caching strategies.
- Database and low-level mechanics (storage engines, concurrency, memory models, query optimization).
- Software design craft, refactoring patterns, clean abstractions, and testing methodologies.
- Thoughtful career reflections, engineering culture, and mental models from veteran builders.

Tone & Style:
- Practical, friendly, and insightful. Grounded in real-world trade-offs rather than pure academic theory.

For each selected story, output:
1. title: Clear, engaging headline.
2. author: The author name.
3. source_name: Publication name.
4. url: The exact canonical URL from the candidate data.
5. why_it_matters: Exactly two friendly, insightful sentences explaining the architectural or craft insight.
6. key_takeaway: One memorable rule of thumb or invariant.
7. ready_to_ship_draft: A polished, complete Telegram post formatted in Markdown with:
   - An engaging title with an emoji (e.g. 📐 **Systems Design: ...** or ⚙️ **Under the Hood: ...**)
   - A 2-3 bullet breakdown of the architectural problem, trade-off, and solution
   - A blockquote takeaway (> 💡 ...)
   - A link: 👉 [Learn more ... ](URL)
   - 2-3 categorized hashtags (e.g. #Architecture #SystemDesign #SoftwareCraft)
   - Channel footer: [Kernel To Cloude](https://t.me/kernel2cloud)
"""

STREAM_PROMPTS = {
    1: STREAM_1_SYSTEM_PROMPT,
    2: STREAM_2_SYSTEM_PROMPT,
}

CURATION_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "selected_stories": {
            "type": "ARRAY",
            "description": "List of top curated stories (at most 5) meeting the senior developer interest bar.",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING", "description": "Title of the article."},
                    "author": {"type": "STRING", "description": "Author or publishing team."},
                    "source_name": {"type": "STRING", "description": "Name of the blog/source."},
                    "url": {"type": "STRING", "description": "Direct canonical link to the article."},
                    "why_it_matters": {
                        "type": "STRING",
                        "description": "Two friendly, insightful sentences explaining why this matters.",
                    },
                    "key_takeaway": {
                        "type": "STRING",
                        "description": "One memorable rule of thumb, invariant, or practical takeaway.",
                    },
                    "ready_to_ship_draft": {
                        "type": "STRING",
                        "description": "Complete, ready-to-forward Telegram Markdown post including bullets, takeaway, link, hashtags, and channel link.",
                    },
                },
                "required": [
                    "title",
                    "author",
                    "source_name",
                    "url",
                    "why_it_matters",
                    "key_takeaway",
                    "ready_to_ship_draft",
                ],
            },
        },
    },
    "required": ["selected_stories"],
}
