# CoW Protocol project

This repo is **CoW-only**: RAG chat for CoW integration docs (Order Book API, order creation, approvals, errors).

## Package layout

- **`pkg/cow-app`** – API (Quart/uvicorn): `/up`, `/predict`; uses `cow_brains.process_question` and `rag_brains`.
- **`pkg/cow-brains`** – CoW RAG: config, documents (docs + OpenAPI), `build_faiss`, `process_question` (uses `rag_brains` pipeline with CoW config/prompts).
- **`pkg/rag-brains`** – Shared RAG: chat, retriever (FAISS), Gemini; no project-specific data.
- **`pkg/cow-core`** – Shared utilities (e.g. logging).

## Data and scripts

- **Data dir:** `data/cow-docs/` (docs artifact, OpenAPI YAML, FAISS index).
- **Scripts:**
  - `scripts/cow-1-create-docs-dataset/main.py` – build docs artifact
  - `scripts/cow-2-fetch-openapi/main.py` – fetch Order Book OpenAPI
  - `scripts/test_cow_poc.sh` – validate artifact
  - `scripts/test_cow_api.sh` – test API health + `/predict`

## Build index

From repo root (with PYTHONPATH set) or from `pkg/cow-app`:

```bash
OP_CHAT_BASE_PATH=../../data GOOGLE_API_KEY=... poetry run python -m cow_brains.build_faiss
```

## Run API

From repo root:

```bash
bash scripts/run-backend.sh
```

Or from `pkg/cow-app` (with PYTHONPATH including `pkg/rag-brains:pkg/cow-brains:pkg/cow-core`):

```bash
poetry run uvicorn cow_app.api:app --host 0.0.0.0 --port 8000
```

## Env reference

- **Required:** `GOOGLE_API_KEY`, `OP_CHAT_BASE_PATH` (e.g. `../../data` or `/app/data` in Docker).
- **Optional:** `COW_DOCS_PATH`, `COW_FAISS_PATH`, `COW_OPENAPI_PATH`, `CHAT_MODEL`, `COW_OPENAPI_PATH`.

Copy `pkg/cow-app/.envrc.example` to `.envrc` (or `.env`) and set `GOOGLE_API_KEY`.

## Frontend

In `www`, set `NEXT_PUBLIC_CHAT_API_URL` to your backend URL (e.g. `http://localhost:8000/predict`).

Docs: [COW_POC_PLAN.md](COW_POC_PLAN.md), [cow_golden_questions.md](cow_golden_questions.md), [cow_quickstart_first_order.md](cow_quickstart_first_order.md).
