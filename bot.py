"""Entry point shim.

Kept at the repository root so the scheduled CI command (`python bot.py`) and
the on-disk data file (state.json) remain unchanged. All orchestration lives
in src/pipeline.py.
"""

from __future__ import annotations

import sys

from src.pipeline import main

if __name__ == "__main__":
    sys.exit(main())
