#!/usr/bin/env bash
# Test CoW PoC pipeline (parts that don't require full poetry install).
# Full E2E (build_cow_faiss + API) requires: Python 3.12, poetry install, OPENAI_API_KEY.
set -e
cd "$(dirname "$0")/.."
echo "=== 1. Ingestion script (--no-pull) ==="
python scripts/cow-1-create-docs-dataset/main.py --output data/cow-docs/cow_docs.txt --no-pull
echo ""
echo "=== 2. Artifact format & parsing ==="
python scripts/cow-1-create-docs-dataset/test_artifact_format.py
echo ""
echo "=== Done. For full test: USE_COW=true, build FAISS, then run API (see README). ==="
