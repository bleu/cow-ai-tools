#!/usr/bin/env bash
# Run the CoW Protocol chat API (Quart) for Railway, Render, Fly.io, etc.
# Usage: from repo root, after poetry install in pkg/cow-app
#   PORT=8000 ./scripts/run-backend.sh

set -e
cd "$(dirname "$0")/.."
export PYTHONPATH="pkg/cow-app:pkg/rag-brains:pkg/cow-brains:pkg/cow-core:$PYTHONPATH"
PORT="${PORT:-8000}"
exec python -m uvicorn cow_app.api:app --host 0.0.0.0 --port "$PORT"
