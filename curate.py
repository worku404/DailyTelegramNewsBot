"""Root execution shim for the Editorial News Scout.

Delegates execution to news_curator.main.main().
Usage:
    python curate.py
"""

from __future__ import annotations

import sys
from news_curator.main import main

if __name__ == "__main__":
    sys.exit(main())
