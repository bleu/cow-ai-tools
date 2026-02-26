# CoW Protocol Integration Documentation – PoC Plan

Plan for the **CoW Protocol Integration Documentation** PoC (RFP: [forum.cow.fi/t/cow-protocol-integration-documentation/3360](https://forum.cow.fi/t/cow-protocol-integration-documentation/3360)), using the forked **op-ai-tools** (Optimism) repo and OP Chat, CoW Docs and RFP as references.

---

## 1. Alignment with the RFP

### 1.1 RFP objective

- Reduce friction for **integrators** (partners, developers).
- Focus on **parameter-level clarity**, not general concepts.
- Deliver value in: **Order creation** (slippage, amount formats), **Approval setup** (ABI, relay), **Error responses**, **Endpoint selection** (fast vs optimal quoting).

### 1.2 Chosen track: **Track A (Systematic/AI-Based)**

- **RAG** solution that uses existing documentation and spec.
- Layer that improves as the underlying documentation improves.
- PoC demonstrates: deployed system + accurate responses in priority areas.

### 1.3 In and out of scope (per RFP)

| In scope | Out of scope |
|----------|--------------|
| Order Book API, quoting, order creation, approvals, errors, integration quickstart | Solver docs, CoW AMM, MEV Blocker, platform migration, conceptual guides for end-users |

---

## 2. References used

| Resource | Use |
|----------|-----|
| **OP Chat** ([op-chat.bleu.builders/chat](https://op-chat.bleu.builders/chat)) | UX and chat flow reference. |
| **op-ai-tools** ([github.com/bleu/op-ai-tools](https://github.com/bleu/op-ai-tools)) | Technical base: RAG, ingestion, API, frontend. |
| **CoW Docs** ([docs.cow.fi](https://docs.cow.fi/)) | Public content to be indexed. |
| **cowprotocol/docs** ([github.com/cowprotocol/docs](https://github.com/cowprotocol/docs)) | Primary source: markdown (Docusaurus, `docs/` folder). |
| **Order Book API** | [docs.cow.fi – Order book API](https://docs.cow.fi/cow-protocol/reference/apis/orderbook); OpenAPI at [api.cow.fi/docs](https://api.cow.fi/docs) when available. |

---

## 3. Base architecture (inherited from OP)

### 3.1 Backend simplified for PoC

For the PoC the backend was reduced to the minimum:

- **Kept:** Quart, CORS, `GET /up` (health), `POST /predict` (question + memory → RAG).
- **Removed:** Tortoise/DB, PostHog, Honeybadger, Quart-Tasks (cron), rate limiter, forum/snapshot sync, analytics events in predict.

The app (`pkg/cow-app`) depends only on what is needed to serve the chat: `cow-brains`, `rag-brains`, `cow-core`. No database; CoW docs + local FAISS only.

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js) – www/                                        │
│  Chat UI, memory, env: NEXT_PUBLIC_CHAT_API_URL → backend /predict│
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend (Quart/uvicorn) – pkg/cow-app                            │
│  GET /up | POST /predict { question, memory } → RAG → { data, error }│
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  RAG (pkg/cow-brains + pkg/rag-brains)                            │
│  • Retriever: FAISS + indices (keywords/questions)               │
│  • Expander: query → questions/keywords                          │
│  • LLM: response with retrieved context                           │
└─────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐         ┌─────────────────┐         ┌─────────────────┐
│ Docs (MD)     │         │ OpenAPI Order   │         │ (Optional)       │
│ cowprotocol/  │         │ Book – endpoints │         │ Errors / extra   │
│ docs          │         │ schemas, params │         │ ref               │
└───────────────┘         └─────────────────┘         └─────────────────┘
```

- **Source 1 – Documentation:** Markdown from the `cowprotocol/docs` repo (Docusaurus structure, `docs/` folder), chunked by section (headers), with `metadata.url` pointing to `https://docs.cow.fi/...`.
- **Source 2 – API:** Order Book OpenAPI (endpoints, parameters, schemas, errors) parsed and chunked by endpoint/schema/error for parameter-level retrieval (as in the Mig application example on the forum).
- **PoC:** We can start with markdown docs only; OpenAPI in phase 2 for maximum accuracy on “slippage”, “buyAmount”, “approval”, etc.

---

## 4. Phased implementation plan

### Phase 1: Foundation (repo + CoW docs)

**Objective:** RAG chat that answers based only on public CoW documentation (Concepts, Tutorials, Technical Reference), without forum/snapshot.

| # | Task | Details |
|---|------|---------|
| 1.1 | Rename / duplicate packages | `op-brains` → `cow-brains` (or keep name and only change sources and config). `op-app` → `cow-app`, `op-artifacts` → `cow-artifacts`. Adjust imports and pyproject. |
| 1.2 | CoW config | New `config.py`: `SCOPE = "CoW Protocol / Order Book API / Integration"`, `DOCS_PATH` or remote source for `cowprotocol/docs`. Remove or disable `RAW_FORUM_DB`, `FORUM_SUMMARY_DB`, `SNAPSHOT_DB` for PoC. |
| 1.3 | Docs ingestion script | New script (e.g. `scripts/cow-1-create-docs-dataset`) that clones or downloads `cowprotocol/docs` and produces an artifact in the format expected by the pipeline (e.g. `==> path <==` format as in `governance_docs.txt`, or CSV with `fullpath`, `content`). Filter: only `docs/` relevant for integration (Technical Reference, API/order creation Tutorials; optionally useful Concepts). |
| 1.4 | CoW document strategy | New class in `documents/` (e.g. `cow.py`): `CowDocsProcessingStrategy` inspired by `FragmentsProcessingStrategy`. Read artifact (txt or CSV), split by Markdown headers, `metadata.url` = `https://docs.cow.fi/...` (map repo path → doc URL). |
| 1.5 | Chat sources | In `documents/__init__.py`, use only the CoW docs strategy (no forum/summary). Keep `DataExporter` and `chat_sources` interface for the retriever. |
| 1.6 | Setup & indices | `setup.py`: generate FAISS and indices (keywords/questions) from CoW docs chunks. Adjust question-generation prompts for scope “CoW Protocol integration / Order Book API”. |
| 1.7 | API and frontend | Backend: keep `/predict`; point to `cow-brains` (or config “cow”). Frontend: change branding (Optimism → CoW), `NEXT_PUBLIC_CHAT_API_URL` to CoW backend. |
| 1.8 | README and env | Repo README describing CoW PoC, prerequisites, how to run ingestion, setup and chat. `.envrc.example` with required variables (embedding, LLM, API URL). |

**Phase 1 deliverable:** Working chat that answers about CoW Protocol based only on indexed documentation (docs.cow.fi via repo).

---

### Phase 2: Order Book API (OpenAPI) and parameter accuracy

**Objective:** Parameter-level accuracy (slippage, buyAmount, approvals, errors), aligned with RFP priorities.

| # | Task | Details |
|---|------|---------|
| 2.1 | Get Order Book OpenAPI | Locate spec (api.cow.fi/docs or cowprotocol/services repo) and save locally (YAML/JSON). |
| 2.2 | OpenAPI parser | Module that reads the spec, resolves `$ref`/`allOf`, extracts endpoints, request/response schemas, enums, descriptions and errors. Produces “chunks” per endpoint, per schema and per error (as in Mig example: api-endpoint, api-schema, api-error). |
| 2.3 | OpenAPI ingestion | Include these chunks in the embedding pipeline and in indices (keywords/questions). Metadata: type (endpoint/schema/error), path, method, parameter name, etc. |
| 2.4 | Integrate in DataExporter | Second source in `chat_sources`: strategy that returns documents generated from the OpenAPI. Retriever then considers docs + API. |
| 2.5 | Prompt/system | ~~Adjust chat system prompt to prioritize “parameter-level” responses (Order creation, Approvals, Errors, Fast vs Optimal), citing endpoint and parameter when applicable.~~ **Done:** `model_utils.py` – CoW instructions in responder and Answer; preprocessor with CoW terms; `ContextHandling.format` for docs_fragment/api-endpoint. |
| 2.6 | Quick prompts (optional) | On the frontend, suggest quick questions: “How do I set buyAmount with slippage?”, “How do I set token approval for gasless swap?”, “When to use fast vs optimal quote?”, “What does error X mean?”. |

**Phase 2 deliverable:** Assistant that answers accurately about API fields (slippage, amounts, approvals) and errors, with citations to doc and spec.

---

### Phase 3: Quickstart and validation (RFP)

**Objective:** Demonstrate “quickstart that leads to a first order in <10 min” and validation in priority areas.

| # | Task | Details |
|---|------|---------|
| 3.1 | “Golden questions” set | 20–30 questions covering: order creation (slippage, formats), approvals (ABI, relay), common errors, fast vs optimal. Reference answers (or success criteria) for evaluation. |
| 3.2 | PoC evaluation | Run golden questions in the chat; measure relevance and accuracy (manual or with checklist). Document results and gaps. **Done:** `docs/cow_poc_evaluation.md` with instructions and results/gaps template. |
| 3.3 | Quickstart in text/code | Minimal guide (markdown or repo page): “First order in <10 min” using the API (and/or SDK), with links to the chat for parameter questions. **Done:** `docs/cow_quickstart_first_order.md`. Optional: example script (e.g. Sepolia) as future extension. |
| 3.4 | PoC documentation | Updated README, optional `docs/COW_POC_PLAN.md` (this doc), and if applicable a summary for RFP submission (what was done, how to test, limitations). |

**Phase 3 deliverable:** Evidence that the assistant covers RFP priorities + documented quickstart.

---

## 5. Technical decisions summary

| Aspect | Decision |
|--------|----------|
| **Data sources** | 1) Markdown from cowprotocol/docs (filtered for integration). 2) Order Book OpenAPI (endpoints, schemas, errors). |
| **Vector store** | Keep FAISS in PoC (as in OP); migrate to pgvector/Neon only if required for deploy. |
| **Embedding** | Keep model configurable (e.g. OpenAI ada-002 or text-embedding-3-small). |
| **LLM** | Keep configurable (e.g. GPT-4o-mini / Claude). |
| **Forum / Snapshot** | Not used in PoC (out of RFP integration scope). |
| **Naming** | Rename to `cow-*` where it adds clarity; or keep `op-*` and identify by config. |

---

## 6. Risks and dependencies

- **OpenAPI:** If the Order Book spec is not public or stable, Phase 2 may depend on access or manual export from api.cow.fi/docs.
- **Maintenance:** RFP mentions “Swagger/OpenAPI sync as a prerequisite”; the PoC can assume a spec snapshot and document that updates require re-ingestion.
- **Doc scope:** Focus only on `docs/` paths related to CoW Protocol (API reference, integration tutorials); exclude CoW AMM, MEV Blocker, etc., per RFP.

---

## 7. Immediate next steps

1. **Confirm** with the team: Track A only (RAG) or hybrid with manual content (Track B) later.
2. **Implement Phase 1:** config, clone/processing script for cowprotocol/docs, `CowDocsProcessingStrategy`, source swap in DataExporter, setup + API + frontend with CoW branding.
3. **Locate** Order Book OpenAPI (URL or file) to prepare Phase 2.
4. **Define** 20–30 golden questions and acceptance criteria for RFP validation.

---

## 8. Concrete technical steps (checklist)

### 8.1 Repo and config

- [x] Keep `op-brains`; use `USE_COW` flag and CoW config in the same package.
- [x] In `op-brains`: `config.py` with `USE_COW`, `SCOPE`, `DOCS_PATH`/`COW_DOCS_PATH`, `COW_FAISS_PATH`; no DB for CoW.
- [x] `documents/cow.py`: `CowDocsProcessingStrategy` (read artifact, split by headers, `metadata.url` = `https://docs.cow.fi/...`).
- [x] `documents/__init__.py`: when `USE_COW`, `chat_sources = [[CowDocsProcessingStrategy]]`.
- [x] Adjust `setup.py` for CoW scope (TYPE_GUIDELINES, conditional import of op_data).

### 8.2 CoW docs ingestion

- [x] Script `scripts/cow-1-create-docs-dataset/main.py`: clone cowprotocol/docs, walk `docs/cow-protocol/**/*.md` and `docs/README.md`, produce `==> path <==\n{content}` in `data/cow-docs/cow_docs.txt` (option `--no-pull`).
- [x] In `cow.py`: map path to URL `https://docs.cow.fi/...` (without `.md`).
- [x] Config: `USE_COW` + `COW_DOCS_PATH`; `CowDocsProcessingStrategy` uses `DOCS_PATH`.

### 8.3 OpenAPI (Phase 2)

- [x] **OpenAPI URL:** `https://raw.githubusercontent.com/cowprotocol/services/main/crates/orderbook/openapi.yml` (referenced in docs/reference/apis/orderbook.mdx).
- [x] Script `scripts/cow-2-fetch-openapi/main.py` to download the spec to `data/cow-docs/openapi.yml`.
- [x] Module `op_brains/documents/openapi_orderbook.py`: parse spec (YAML), generate chunks per endpoint and per schema; metadata `api-endpoint` / `api-schema`, URL to docs.cow.fi.
- [x] When `USE_COW` and `COW_OPENAPI_PATH` points to an existing file, `OpenApiOrderbookStrategy` is the second source in `chat_sources`. Rebuild FAISS to include OpenAPI chunks.

### 8.4 Backend and frontend

- [x] **PoC backend:** API simplified: Quart/uvicorn + CORS + `/up` + `/predict` only (no DB, analytics, cron). See `pkg/cow-app/cow_app/api.py`.
- [x] CoW backend: cow-app calls `process_question` from cow-brains and uses CoW FAISS/indices (docs + OpenAPI) via rag-brains.
- [x] **System prompt (2.5):** In `model_utils.py`, CoW instructions in responder (parameter-level, cite endpoint/URL) and in Answer; preprocessor with CoW terms; `ContextHandling.format` includes `docs_fragment` and `api-endpoint`/`api-schema` in context.
- [x] Frontend: CoW branding via `NEXT_PUBLIC_BRAND=cow` (header “CoW Protocol”, empty state, quick prompts: buyAmount/slippage, gasless approval, fast vs optimal, errors). `.envrc.example`: `NEXT_PUBLIC_CHAT_API_URL=http://localhost:8000/predict`.

### 8.5 Deploy and validation

- [x] README with instructions: ingestion → (optional) fetch OpenAPI → build FAISS → run API → run www; golden questions referenced.
- [x] Golden questions in `docs/cow_golden_questions.md` (24 questions in areas: order creation, approvals, quoting, errors, endpoints).
- [x] PoC evaluation (3.2): `docs/cow_poc_evaluation.md` with instructions to run golden questions and results/gaps template.
- [x] Quickstart (3.3): `docs/cow_quickstart_first_order.md` – “first order in <10 min” guide with links to API and chat.

### 8.6 Quickstart (“first order in <10 min”)

- [x] Flow documented in README (CoW PoC): create docs artifact → (optional) fetch OpenAPI → build FAISS → run API → run www with `NEXT_PUBLIC_BRAND=cow`. The chat serves as support for parameter questions; “first order” code guide remains as a future extension (e.g. Sepolia script).

---

## 9. Quick references

- RFP: https://forum.cow.fi/t/cow-protocol-integration-documentation/3360  
- CoW Docs: https://docs.cow.fi/  
- CoW Docs repo: https://github.com/cowprotocol/docs  
- Order Book API (doc): https://docs.cow.fi/cow-protocol/reference/apis/orderbook  
- OP Chat: https://op-chat.bleu.builders/chat  
- OP AI Tools repo: https://github.com/bleu/op-ai-tools  
