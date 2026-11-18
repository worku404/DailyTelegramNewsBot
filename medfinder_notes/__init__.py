"""MedFinder OOP Study Notes automation package.

Monitors merged Pull Requests on worku404/MedFinder-java, maps newly added
src/main/ Java code to the OOP course syllabus (topics.md), generates
hybrid study notes with Gemini, persists numbered Markdown files under
medfinder_notes/notes/, and delivers them to Telegram via a priority queue.
"""
