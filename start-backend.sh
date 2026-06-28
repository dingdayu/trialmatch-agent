#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_DIR="$BACKEND_DIR/.venv"

cd "$BACKEND_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
  uv venv "$VENV_DIR"
fi

if ! "$VENV_DIR/bin/python" -c "import fastapi, uvicorn" >/dev/null 2>&1; then
  uv pip install -r requirements.txt
fi

exec "$VENV_DIR/bin/python" -m uvicorn app.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}" --reload