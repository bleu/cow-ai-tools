# cow-ai-tools

This repository provides **CoW Protocol Integration Documentation** chat: a RAG-based Q&A for Order Book API, order creation, approvals, and errors (aligned with the [CoW Grants RFP](https://forum.cow.fi/t/cow-protocol-integration-documentation/3360)).

**Planning:** [docs/COW_POC_PLAN.md](docs/COW_POC_PLAN.md), [docs/COW_PROPOSAL_NEXT_PHASE.md](docs/COW_PROPOSAL_NEXT_PHASE.md).

---

## Overview

CoW AI is a RAG chatbot that answers integration-focused questions about CoW Protocol using [CoW docs](https://docs.cow.fi/) and the Order Book OpenAPI spec. Stack: file-based docs + FAISS index, Gemini for embeddings and chat, no database.

## Key directories

- `data/` – Raw and processed datasets (e.g. `data/cow-docs/`).
- `pkg/` – Backend and RAG: `cow-app` (API), `cow-brains` (CoW RAG), `rag-brains` (shared RAG pipeline), `cow-core` (logging).
- `scripts/` – Dataset and OpenAPI scripts, tests.
- `www/` – Next.js frontend.

## Prerequisites

- Python 3.12+
- Poetry
- Node.js 20+
- Yarn

## Installation

1. Clone and enter the repo:

   ```bash
   git clone https://github.com/bleu/cow-ai-tools.git
   cd cow-ai-tools
   ```

2. Install backend (from repo root, with Poetry in each package or use a venv and install from `pkg/cow-app`):

   ```bash
   cd pkg/cow-app && poetry install
   cd ../cow-brains && poetry install
   cd ../rag-brains && poetry install
   cd ../cow-core && poetry install
   ```

3. Install frontend:

   ```bash
   cd www && yarn install
   ```

## Usage

### Quick test (no API key)

From repo root:

```bash
bash scripts/test_cow_poc.sh
```

### Full flow (FAISS + API)

1. **Create CoW docs artifact**

   ```bash
   python scripts/cow-1-create-docs-dataset/main.py --output data/cow-docs/cow_docs.txt
   ```

2. **(Optional) Fetch Order Book OpenAPI**

   ```bash
   python scripts/cow-2-fetch-openapi/main.py --output data/cow-docs/openapi.yml
   ```

3. **Build FAISS index** (set `GOOGLE_API_KEY`)

   ```bash
   cd pkg/cow-app && OP_CHAT_BASE_PATH=../../data GOOGLE_API_KEY=... poetry run python -m cow_brains.build_faiss
   ```

4. **Run the API**

   ```bash
   cd pkg/cow-app && cp .envrc.example .envrc   # edit GOOGLE_API_KEY
   direnv allow   # or source .envrc
   poetry run uvicorn cow_app.api:app --host 0.0.0.0 --port 8000
   ```
   Or use the helper script from repo root: `bash scripts/run-backend.sh` (ensure PYTHONPATH includes `pkg/cow-app:pkg/rag-brains:pkg/cow-brains:pkg/cow-core`).

5. **Run the frontend**

   ```bash
   cd www && cp .envrc.example .envrc
   # Set NEXT_PUBLIC_CHAT_API_URL=http://localhost:8000/predict
   yarn dev
   ```

**Golden questions:** [docs/cow_golden_questions.md](docs/cow_golden_questions.md). **Evaluation:** [docs/cow_poc_evaluation.md](docs/cow_poc_evaluation.md). **Quickstart:** [docs/cow_quickstart_first_order.md](docs/cow_quickstart_first_order.md).

## Deploy

- **Backend (Railway/Render):** [docs/deploy-backend-railway.md](docs/deploy-backend-railway.md).
- **Frontend + serverless API (Vercel):** [docs/deploy-vercel.md](docs/deploy-vercel.md).

## Contact

Open an issue on GitHub or contact the maintainers.
