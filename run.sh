#!/usr/bin/env bash
# Launch the Primer.
set -e
cd "$(dirname "$0")"

PRIMER_PYTHON="${PRIMER_PYTHON:-python3}"
require_supported_python() {
  if ! "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "Python 3.10+ is required for the patched dependencies. Use PRIMER_PYTHON=/path/to/python3.12 for a first run, or recreate an older .venv with that interpreter and install requirements.lock.txt. Reader records in content/ are separate." >&2
    exit 1
  fi
}

if [ ! -d ".venv" ]; then
  require_supported_python "$PRIMER_PYTHON"
  echo "Setting up (first run)…"
  "$PRIMER_PYTHON" -m venv .venv
  .venv/bin/pip install --quiet --upgrade pip
  # Pinned versions — see requirements.txt
  .venv/bin/pip install --quiet -r requirements.txt
fi

require_supported_python .venv/bin/python

PORT="${PORT:-8747}"
echo "✦ The Primer is opening at http://localhost:${PORT}"
exec .venv/bin/uvicorn primer.server:app --host 127.0.0.1 --port "${PORT}" "$@"
