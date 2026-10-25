#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

if [[ -x .venv/bin/streamlit ]]; then
  exec .venv/bin/streamlit run app.py
fi

exec streamlit run app.py
