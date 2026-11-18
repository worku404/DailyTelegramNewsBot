"""Hybrid OOP teaching prompt and structured JSON schema for Gemini.

Combines two proven learning styles from the user's MedFinder notes:
1. Problem-First Walkthrough (02-what-is-pom-xml.md):
   - Plain-English explanation & analogy
   - "Why it matters / What happens WITHOUT it?" pain points
   - Guided walkthrough of the real MedFinder PR code
   - Quick Reference summary table
2. Exam & Oral Defense Study Guide (01-class-with-static-method.md):
   - Structured metadata blockquote (Course, Chapters, Topic, Where in MedFinder, Source PR)
   - 30-second Concept Overview
   - Question & Answer Study Guide (compiler/runtime rules, good use vs. anti-patterns)
   - Quick Review Checklist table for Oral Presentation / Defense
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
                "Zero or more distinct Markdown study notes extracted from the PR. "
                "Return an empty array [] if the PR introduces no meaningful new OOP/Java concepts."
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
                            "Concise human-readable note title including chapter reference "
                            "(e.g. 'Abstract Classes & Template Method Pattern (Chapter 4)')."
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
                            "Complete standalone Markdown study note following the hybrid "
                            "teaching structure."
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

    return f"""You are an expert Java & Object-Oriented Programming (OOP) university instructor writing personal study notes for a student team building the **MedFinder** Java 17 Maven console application.

### TASK
Analyze the newly added/changed production code (`src/main/` and build/config files only) from Pull Request #{pr.number} in `worku404/MedFinder-java`, map every substantive Java/OOP concept to the exact matching chapters & subtopics in the course syllabus (`topics.md`), and generate **0 to {max_notes}** clear, high-depth Markdown study notes.

### PULL REQUEST CONTEXT
- **PR Number:** #{pr.number}
- **Title:** {pr.title}
- **Author:** @{pr.author}
- **URL:** {pr.html_url}

### COURSE SYLLABUS (`topics.md` — Chapters 1 to 6)
```text
{topics_text.strip()}
```

### ALREADY-EXISTING STUDY NOTES (DO NOT DUPLICATE!)
The student already has notes covering these topics:
{existing_block}

### DECIDING HOW MANY NOTES TO GENERATE
1. **Return `{{"notes": []}}` (0 notes)** if the PR contains only trivial edits (formatting, comments, typos, renames) or ONLY repeats concepts already thoroughly covered in the existing notes above without introducing a meaningful new angle or chapter subtopic.
2. **Generate 1 note** if the PR centers on one cohesive OOP/Java concept (or a tight pair of concepts).
3. **Generate 2 to {max_notes} separate notes** ONLY when the PR introduces genuinely distinct OOP concepts from different sections of `topics.md` (for example, one note on `Try-with-Resources & Checked IOException` from Chapter 6, and a second note on `Generic Interfaces & Default Methods` from Chapter 4). Never split artificially into thin notes.

### REQUIRED HYBRID TEACHING STRUCTURE FOR EVERY NOTE
Each `markdown_content` must blend **Problem-First Walkthrough** teaching with **Exam & Oral Defense Q&A** rigor, using these exact sections:

1. **Title (`# ...`) and Metadata Blockquote:**
   ```markdown
   # Course Concept: <Concept Title> (Chapter X)

   > **Course:** Object-Oriented Programming (Java)
   > **Syllabus Mapping:** <Exact section(s) from topics.md>
   > **Where in MedFinder:** `<exact package.ClassName / method(s) from this PR>`
   > **Source PR:** PR #{pr.number} by @{pr.author}
   ```
2. **`## 📖 Concept Overview in 30 Seconds`**
   - Plain-English explanation + intuitive real-world analogy so the student grasps the core idea immediately.
3. **`## ❌ What Happens WITHOUT This? (Why It Exists)`**
   - Concrete, relatable MedFinder pain points showing what breaks, gets messy, or fails to compile/scale if you didn't use this OOP/Java feature.
4. **`## 🔍 Guided Tour of Our MedFinder Code (PR #{pr.number})`**
   - Quote exact, accurate Java code snippets from the PR diff below (never invent classes or methods that aren't in the diff or MedFinder).
   - Walk through the key lines, keywords, memory/JVM mechanics, and design choices step by step.
5. **`## 🎯 Question & Answer Study Guide (for Defense & Exams)`**
   - 4 to 6 sharp, instructor-style questions and thorough answers covering:
     - Core mechanism & JVM/compiler rules (mention exact compiler errors or runtime exceptions where relevant)
     - Why MedFinder chose this design here
     - Good usage vs. anti-patterns / common traps
6. **`## 📋 Quick Review Checklist for Oral Presentation / Defense`**
   - Clean Markdown table (`| Question / Concept | Key Point to Say to Instructor |`) summarizing the essential takeaways in crisp defense-ready bullets.

### STRICT QUALITY RULES
- Ground every code snippet strictly in the PR diff below (Java 17 plain console OOP style — no streams, lambdas, `var`, `record`, or `Optional` unless literally present in the diff).
- Never mention or analyze unit test files (`src/test/`).
- Use valid GitHub-Flavored Markdown with real newlines (never emit literal `\\n` outside code).
- Keep `slug` short, descriptive, lowercase kebab-case without numbers or `.md` (e.g., `try-with-resources-and-ioexception`).

### PR CODE DIFF (`src/main/` & Config Only)
```diff
{diff_text.strip()}
```
"""
