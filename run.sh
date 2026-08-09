#!/usr/bin/env bash
# Launch the Primer.
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Setting up (first run)…"
  python3 -m venv .venv
  .venv/bin/pip install --quiet --upgrade pip
  # Pinned versions — see requirements.txt
  .venv/bin/pip install --quiet -r requirements.txt
fi

PORT="${PORT:-8747}"
echo "✦ The Primer is opening at http://localhost:${PORT}"
exec .venv/bin/uvicorn primer.server:app --host 127.0.0.1 --port "${PORT}" "$@"
