#!/usr/bin/env bash
# Run the CoW/Optimism chat API (Quart) for Railway, Render, Fly.io, etc.
# Usage: from repo root, after pip install -r requirements.txt
#   PORT=8000 ./scripts/run-backend.sh

set -e
cd "$(dirname "$0")/.."
export PYTHONPATH="pkg/op-app:pkg/op-brains:pkg/cow-brains:pkg/op-core:pkg/op-data:pkg/op-artifacts:$PYTHONPATH"
PORT="${PORT:-8000}"
exec python -m uvicorn op_app.api:app --host 0.0.0.0 --port "$PORT"
