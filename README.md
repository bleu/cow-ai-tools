# cow-ai-tools

This repository is a fork of [op-ai-tools](https://github.com/bleu/op-ai-tools), adapted for **CoW Protocol Integration Documentation** (PoC aligned with the [CoW Grants RFP](https://forum.cow.fi/t/cow-protocol-integration-documentation/3360)).

**Planning:** See **[docs/COW_POC_PLAN.md](docs/COW_POC_PLAN.md)** for scope, phases, data sources, and implementation checklist. **Forum proposal (next phase):** [docs/COW_PROPOSAL_NEXT_PHASE.md](docs/COW_PROPOSAL_NEXT_PHASE.md).

---

## Two projects in this repo

The codebase supports **two projects**; you run one at a time with different config and data:

| Project | Purpose | Activation |
|--------|---------|------------|
| **CoW Protocol** | RAG chat for integration docs (Order Book API, orders, approvals) | `PROJECT=cow` or `USE_COW=true` |
| **Optimism** | Governance chat, forum summarization, reporting | `PROJECT=optimism` (default) or unset |

**→ Full comparison, env examples, and setup:** **[docs/PROJECTS.md](docs/PROJECTS.md)**

- **CoW:** File-based docs + FAISS, Gemini-only, no DB. Scripts: `cow-1-create-docs-dataset`, `cow-2-fetch-openapi`, `test_cow_api.sh`.
- **Optimism:** op_artifacts + DB, OpenAI/Anthropic (or Gemini). Scripts: `op-2-*`, `op-9-*`, setup.py.

---

## Project overview

Op Chat Brains is an advanced question-answering system designed to provide intelligent responses about Optimism using RAG. The **CoW** adaptation reuses this stack to answer integration-focused questions about CoW Protocol (Order Book API, order creation, approvals, errors) using [CoW docs](https://docs.cow.fi/) and the Order Book OpenAPI spec.

## Key Features

Chatbot Web Application: Users can interact with the trained model and ask questions.
Automated Summary Reports: Summarizes forum discussions within the Optimism ecosystem.
Reporting Tool: Tracks user engagement and evaluates the model's effectiveness.

## Key Directories and Files

- `data/`: Contains raw and processed datasets.
- `notebooks/`: Jupyter notebooks for experimentation and analysis.
- `pkg/`: Core package containing the main application logic and modules.
- `scripts/`: Scripts for creating and improving datasets and conducting tests.
- `www/`: Frontend-related files, configurations, and dependencies.

## Getting Started

### Prerequisites

- Python 3.12+
- Poetry
- Node.js 20+
- Yarn

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/bleu/op-ai-tools.git
   cd op-ai-tools
   ```

2. Set up the Python environment:

   ```bash
   cd pkg/op-brains
   poetry install
   ```

3. Set up the web application:

   ```bash
   cd www
   yarn install
   ```

### Usage

#### CoW PoC (documentation-only chat)

**Quick test** (no API key, no full install): from repo root run `bash scripts/test_cow_poc.sh` to validate ingestion and artifact format. Full flow (FAISS + API) requires Python 3.12 and a working `poetry install` in `pkg/op-brains` and `pkg/op-app`.

**Golden questions** for validation: see [docs/cow_golden_questions.md](docs/cow_golden_questions.md). **Evaluation:** [docs/cow_poc_evaluation.md](docs/cow_poc_evaluation.md). **Quickstart (first order):** [docs/cow_quickstart_first_order.md](docs/cow_quickstart_first_order.md).

1. **Create the CoW docs artifact** (clone cowprotocol/docs, output `==> path <==` format):

   ```bash
   python scripts/cow-1-create-docs-dataset/main.py --output data/cow-docs/cow_docs.txt
   ```

2. **(Optional) Fetch Order Book OpenAPI spec** for parameter-level answers (slippage, buyAmount, errors):

   ```bash
   python scripts/cow-2-fetch-openapi/main.py --output data/cow-docs/openapi.yml
   ```

3. **Build the FAISS index** (CoW; set `GOOGLE_API_KEY`):

   ```bash
   cd pkg/op-app && PROJECT=cow OP_CHAT_BASE_PATH=../../data GOOGLE_API_KEY=... poetry run python -m cow_brains.build_faiss
   ```

4. **Run the API** (CoW project):

   ```bash
   cd pkg/op-app && cp .envrc.example.cow .envrc   # then edit GOOGLE_API_KEY
   direnv allow   # or source .envrc
   poetry run python op_app/api.py
   ```
   Or one-shot: `PROJECT=cow OP_CHAT_BASE_PATH=../../data GOOGLE_API_KEY=... poetry run python op_app/api.py`

5. **Run the frontend** with CoW branding and API URL:

   ```bash
   cd www && cp .envrc.example .envrc
   # Edit .envrc: NEXT_PUBLIC_CHAT_API_URL=http://localhost:8000/predict, NEXT_PUBLIC_BRAND=cow
   yarn dev
   ```

See **[docs/PROJECTS.md](docs/PROJECTS.md)** and `pkg/op-app/.envrc.example.cow` for all CoW env options. To deploy frontend and backend on **Vercel**, see **[docs/deploy-vercel.md](docs/deploy-vercel.md)**.

#### Optimism project – data preparation

Run the data collection scripts:

```bash
python scripts/op-2-create-initial-documentation-dataset/main.py
python scripts/op-9-create-optimism-forum-dataset/main.py
```

Process the collected data:

```bash
cd pkg/op-brains && python op_brains/setup.py
```

#### Running the API

Start the chat API (from `pkg/op-app`):

```bash
cd pkg/op-app && poetry run python op_app/api.py
```
(For CoW use `PROJECT=cow` and run after building the FAISS index; see [docs/PROJECTS.md](docs/PROJECTS.md).)

#### Running the Web Application

Start the Next.js development server:

```bash
cd www
yarn dev
```

Visit [http://localhost:3000](http://localhost:3000) in your browser to interact with the chat interface.

## Contact

For any questions or issues, please open an issue on GitHub or contact the project maintainers.
