"""Streamlit entry point, also runnable directly from the repository root."""

import sys
from pathlib import Path

# Streamlit adds the script's directory (``src``) to sys.path, but the app
# imports modules through the ``src`` package. Add the repository root so that
# ``streamlit run src/main.py`` works the same way as ``python -m``.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.app import main

if __name__ == "__main__":
    main()
