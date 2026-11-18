"""Teaching-first prompt and structured JSON schema for Gemini.

Each generated note is a short (3-5 minute) lesson that:
1. Defines the concept from zero, as if the reader has never heard the word.
2. Explains why the concept exists and what goes wrong without it.
3. Explains how it works in small steps.
4. Shows how MedFinder applies it, using trimmed snippets from the PR diff
   where every snippet exists only to teach one idea.
5. Ends with common mistakes and a short plain-words summary.
"""

from __future__ import annotations

from typing import Any

from medfinder_notes.github_client import PullRequestInfo

NOTES_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "notes": {
            "type": "ARRAY",
            "description": (
                "Zero or more distinct Markdown lessons extracted from the PR. "
                "Return an empty array [] if the PR introduces no meaningful Java/OOP concept "
                "from the syllabus."
            ),
            "items": {
                "type": "OBJECT",
                "properties": {
                    "slug": {
                        "type": "STRING",
                        "description": (
                            "Short lowercase kebab-case filename slug WITHOUT numeric prefix "
                            "or .md extension (e.g. 'abstract-classes-and-template-method')."
                        ),
                    },
                    "title": {
                        "type": "STRING",
                        "description": (
                            "Plain, concise title including the chapter reference "
                            "(e.g. 'Abstract Classes and the Template Method (Chapter 4)')."
                        ),
                    },
                    "chapter_refs": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"},
                        "description": (
                            "Exact matching chapter/subtopic names from topics.md "
                            "(e.g. ['4.5 Abstract Classes & Abstract Methods'])."
                        ),
                    },
                    "markdown_content": {
                        "type": "STRING",
                        "description": (
                            "Complete standalone Markdown lesson following the required "
                            "teaching structure. 500-800 words of prose plus short snippets."
                        ),
                    },
                },
                "required": ["slug", "title", "chapter_refs", "markdown_content"],
            },
        }
    },
    "required": ["notes"],
}


def build_pr_notes_prompt(
    pr: PullRequestInfo,
    diff_text: str,
    topics_text: str,
    existing_titles: list[str],
    max_notes: int,
) -> str:
    """Build the full Gemini prompt for analyzing a MedFinder Pull Request."""
    existing_block = (
        "\n".join(f"- {title}" for title in existing_titles)
        if existing_titles
        else "(None yet)"
    )

    return f"""You are a patient, experienced Java instructor. You are writing learning notes for third-year software engineering students who are building the **MedFinder** Java 17 Maven console application as a team. The students know basic programming, but they must be taught every concept from zero. The goal is LEARNING and understanding, nothing else.

### TASK
Study the production code (`src/main/` and build/config files only) from Pull Request #{pr.number} in `worku404/MedFinder-java`. Find the concepts in it that match topics in the course syllabus (`topics.md`) and write **0 to {max_notes}** lessons that teach those concepts using our own code.

### PULL REQUEST CONTEXT
- **PR Number:** #{pr.number}
- **Title:** {pr.title}
- **Author:** @{pr.author}
- **URL:** {pr.html_url}

### COURSE SYLLABUS (`topics.md`)
```text
{topics_text.strip()}
```

### ALREADY-EXISTING NOTES (DO NOT DUPLICATE)
{existing_block}

### HOW MANY LESSONS
1. Return `{{"notes": []}}` if the PR only has trivial edits (formatting, comments, typos, renames) or only repeats concepts the existing notes already teach well, with no new angle.
2. Write 1 lesson if the PR centers on one concept (or two tightly linked ones).
3. Write 2 to {max_notes} lessons ONLY when the PR clearly applies distinct syllabus concepts. Never split a topic into thin lessons.
4. Do NOT skip a concept just because it seems basic. If it is in `topics.md` and the PR uses it, it is worth teaching.

### REQUIRED STRUCTURE FOR EVERY `markdown_content`
Use exactly these sections, in this order. Plain headings, no emoji.

1. **Title and one-line metadata**
   ```markdown
   # <Plain concept title> (Chapter X)

   > **Chapter:** <exact section(s) from topics.md> | **In MedFinder:** `<exact class / method / file from this PR>` | **PR:** #{pr.number} by @{pr.author}
   ```

2. **`## What is it?`**
   - Define the concept in 2 to 4 clear sentences, as if the reader is hearing the word for the first time.
   - Do not use a technical word without explaining it right there in plain language.
   - Be precise and unambiguous. No vague phrases.
   - Add one short real-life analogy ONLY if it makes the idea clearer. Never open it with "Think of X as...".

3. **`## Why do we need it?`**
   - Describe the problem in a short, realistic MedFinder scenario (this part may be hypothetical).
   - Then state what goes wrong without it: a short paragraph or at most 3 bullets, each with its concrete consequence (bug, duplicated code, compile error, hard-to-change code, etc.).

4. **`## How it works`**
   - Explain the mechanism in small, numbered or clearly ordered steps (rules, order of execution, what the compiler or JVM does).
   - Use a tiny generic example ONLY if the concept cannot be understood without one.

5. **`## How MedFinder uses it`**
   - This is the most important section. Use 1 to 3 parts, each with a short `###` sub-heading naming the idea it shows.
   - Each part follows this pattern:
     a. **Situation:** 1 to 2 sentences on what MedFinder needed to do.
     b. **Code:** a trimmed snippet (about 5 to 15 lines) copied exactly from the diff. Cut unrelated lines; add `// ...` where lines are removed.
     c. **Walkthrough:** explain what the key lines do and exactly where the concept appears in them. Then say what would break or get worse here if we did not apply it.
   - A snippet is allowed ONLY if it teaches the concept. No decorative or "list of code" snippets.

6. **`## Common mistakes`**
   - 1 or 2 mistakes students often make with this concept, each with a short explanation and the fix. Skip this section completely if nothing meaningful applies.

7. **`## Summary`**
   - 3 to 4 plain sentences restating the idea and how we use it. No table, no questions.

### WRITING STYLE
- Write like a teacher talking to one student: use "we" for the MedFinder team and "you" for the reader.
- Short paragraphs (max 3 to 4 lines). Clear, direct sentences.
- Target a 3 to 5 minute read: about 500 to 800 words of prose, not counting code.
- Use **bold** only for the key term when you first define it. Use backticks for identifiers, keywords and file names.
- No emoji. No tables unless one small table is truly needed in "How it works".
- Avoid filler such as "Let's dive in", "It's important to note", "In conclusion", "In today's world", "Imagine a world".
- Do not include exam, oral defense, or checklist content. Do not add quiz or "think about it" questions.

### STRICT ACCURACY RULES
- Every code snippet must come from the PR diff below. Never invent classes, methods or fields. Hypotheticals are allowed only in prose in "Why do we need it?".
- Do not invent numbers or facts (class counts, team size, versions) that are not in the diff or the syllabus.
- Keep to Java 17 plain console style. Do not use or recommend streams, lambdas, `var`, `record` or `Optional` unless they literally appear in the diff.
- Never mention or analyze test files (`src/test/`).
- Use valid GitHub-Flavored Markdown with real newlines (never emit a literal backslash-n outside code).
- Keep `slug` short, lowercase kebab-case, no numbers, no `.md` (e.g., `try-with-resources-and-ioexception`).

### PR CODE DIFF (`src/main/` & Config Only)
```diff
{diff_text.strip()}
```
"""
