# cow-brains

CoW Protocol RAG: docs + Order Book OpenAPI. **No Optimism/OP code.** Use when `PROJECT=cow`.

- **config** — CoW paths, SCOPE, CHAT_MODEL, EMBEDDING_MODEL
- **documents_cow** — CowDocsProcessingStrategy (==> path <== artifact)
- **openapi_orderbook** — OpenApiOrderbookStrategy
- **data_exporter** — DataExporter over CoW sources
- **build_faiss** — build FAISS index: `python -m cow_brains.build_faiss`
- **process_question** — RAG prediction (uses op_brains for pipeline; injects CoW config and prompts)

The `op` prefix is for Optimism; CoW lives in this package only.
