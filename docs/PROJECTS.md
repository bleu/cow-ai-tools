# Projects in this repo

This repository supports **two distinct projects** that share the same codebase (op-brains, op-app, www) but use different data, config, and scripts. Choose one project per environment; do not mix.

**Package layout:** The **op** prefix is for Optimism only; CoW has no code inside op-brains.
- **`pkg/op-brains`** — Optimism only: config, documents (governance, forum), chat, retriever, setup
- **`pkg/cow-brains`** — CoW only: config, documents (docs + OpenAPI), build_faiss, process_question (uses op-brains pipeline with CoW config/prompts)
- **`pkg/op-app`** — API: when `PROJECT=cow` uses `cow_brains.process_question`, else `op_brains.chat.utils.process_question`

| | **CoW Protocol** | **Optimism** |
|---|-----------------|--------------|
| **Purpose** | RAG chat for CoW integration docs (Order Book API, order creation, approvals) | Governance chat + forum summarization, reporting |
| **Data** | CoW docs artifact + OpenAPI spec; local FAISS index | Governance docs (op_artifacts) + forum/snapshot DB |
| **LLM/Embeddings** | Gemini (one API key) | OpenAI/Anthropic + optional Gemini |
| **Activation** | `PROJECT=cow` or `USE_COW=true` | `PROJECT=optimism` (default) or unset |

---

## CoW Protocol project

- **Config:** `PROJECT=cow` or `USE_COW=true`. Use `pkg/op-app/.envrc.example.cow` as reference.
- **Data dir:** `data/cow-docs/` (docs artifact, OpenAPI YAML, FAISS index).
- **Scripts:**  
  - `scripts/cow-1-create-docs-dataset/main.py` – build docs artifact  
  - `scripts/cow-2-fetch-openapi/main.py` – fetch Order Book OpenAPI  
  - `scripts/test_cow_poc.sh` – validate artifact  
  - `scripts/test_cow_api.sh` – test API health + `/predict`
- **Build index:** From `pkg/op-app`:  
  `PROJECT=cow OP_CHAT_BASE_PATH=../../data GOOGLE_API_KEY=... poetry run python -m cow_brains.build_faiss`
- **Run API:** From `pkg/op-app`:  
  `PROJECT=cow OP_CHAT_BASE_PATH=../../data GOOGLE_API_KEY=... poetry run python op_app/api.py`
- **Frontend:** In `www`, set `NEXT_PUBLIC_BRAND=cow` and `NEXT_PUBLIC_CHAT_API_URL=http://localhost:8000/predict`.
- **Docs:** [COW_POC_PLAN.md](COW_POC_PLAN.md), [cow_golden_questions.md](cow_golden_questions.md), [cow_quickstart_first_order.md](cow_quickstart_first_order.md).

---

## Optimism project

- **Config:** `PROJECT=optimism` or leave `PROJECT` and `USE_COW` unset. Use `pkg/op-app/.envrc.example.optimism` as reference.
- **Data:** Run op-* scripts for documentation and forum datasets; use `pkg/op-brains` setup and DB.
- **Scripts:**  
  - `scripts/op-2-create-initial-documentation-dataset/main.py`  
  - `scripts/op-9-create-optimism-forum-dataset/main.py`  
  - etc.
- **Setup:** `cd pkg/op-brains && python op_brains/setup.py`
- **Run API:** From `pkg/op-app`:  
  `poetry run python op_app/api.py` (with DB and env for Optimism).
- **Frontend:** Default branding; point to your API URL.

---

## Env reference

- **CoW:** `PROJECT=cow`, `GOOGLE_API_KEY`, `OP_CHAT_BASE_PATH` (e.g. `../../data`). Optional: `COW_DOCS_PATH`, `COW_FAISS_PATH`, `COW_OPENAPI_PATH`.
- **Optimism:** `DATABASE_URL`, `SECRET`, optional `OPENAI_API_KEY` / `CHAT_MODEL`, etc. Do not set `USE_COW` or `PROJECT=cow` when running Optimism.

Copy the right example before running:

- CoW: `cp pkg/op-app/.envrc.example.cow pkg/op-app/.envrc` then set `GOOGLE_API_KEY` in `.envrc`, or `cp pkg/op-app/.env.example pkg/op-app/.env` and set `GOOGLE_API_KEY` in `.env` (loaded by python-dotenv when running the API).
- Optimism: `cp pkg/op-app/.envrc.example.optimism pkg/op-app/.envrc`
