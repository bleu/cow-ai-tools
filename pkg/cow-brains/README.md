# cow-brains

CoW Protocol RAG: docs + Order Book OpenAPI + CoW Swap (cowswap repo) + CoW SDK (cow-sdk repo). **No Optimism/OP code.** Use when `PROJECT=cow`.

- **config** — CoW paths (DOCS_PATH, COW_SWAP_DOCS_PATH, COW_SDK_DOCS_PATH, COW_OPENAPI_PATH), SCOPE, CHAT_MODEL, EMBEDDING_MODEL
- **documents_cow** — CowDocsProcessingStrategy (==> path <== artifact from cowprotocol/docs)
- **documents_cowswap** — CowSwapDocsProcessingStrategy (README + docs/ from cowprotocol/cowswap)
- **documents_cowsdk** — CowSdkDocsProcessingStrategy (README + docs/ from cowprotocol/cow-sdk)
- **openapi_orderbook** — OpenApiOrderbookStrategy
- **data_exporter** — DataExporter over CoW sources (docs, OpenAPI, CoW Swap, CoW SDK)
- **build_faiss** — build FAISS index: `python -m cow_brains.build_faiss` (after creating artifacts)
- **process_question** — RAG prediction (uses op_brains for pipeline; injects CoW config and dev-focused prompts)

To add CoW Swap content: run `python scripts/cow-3-create-cowswap-dataset/main.py` from repo root; then rebuild FAISS.
To add CoW SDK content: run `python scripts/cow-4-create-cowsdk-dataset/main.py` from repo root; then rebuild FAISS.

The `op` prefix is for Optimism; CoW lives in this package only.
