#!/usr/bin/env bash
# Test CoW PoC API: health + one /predict (RAG + Gemini).
# Prereqs: API running with PROJECT=cow and GOOGLE_API_KEY.
# Start API: bash scripts/run-backend.sh (or cd pkg/cow-app && OP_CHAT_BASE_PATH=../../data GOOGLE_API_KEY=... poetry run uvicorn cow_app.api:app --host 0.0.0.0 --port 8000)

set -e
BASE_URL="${COW_API_URL:-http://localhost:8000}"

echo "=== CoW PoC API test (base: $BASE_URL) ==="

echo -n "GET /up ... "
UP=$(curl -s "$BASE_URL/up")
if echo "$UP" | grep -q '"status":"healthy"'; then
  echo "OK"
else
  echo "FAIL"
  echo "$UP"
  exit 1
fi

echo -n "POST /predict (limit order) ... "
RESP=$(curl -s -X POST "$BASE_URL/predict" -H "Content-Type: application/json" \
  -d '{"question":"How do I place a limit order?","memory":[]}')
if echo "$RESP" | grep -q '"error":null' && echo "$RESP" | grep -q '"answer"'; then
  echo "OK"
  echo "$RESP" | head -c 400
  echo "..."
else
  echo "FAIL"
  echo "$RESP"
  exit 1
fi

echo "=== All checks passed ==="
