# How CoW AI Works – From Doc Setup to Chat Response

End-to-end flow: data preparation → vector index → API → RAG → frontend.

---

## 1. Documentation setup (once)

### 1.1 Docs artifact (Markdown)

- **Script:** `scripts/cow-1-create-docs-dataset/main.py`
- **What it does:** Clones the [cowprotocol/docs](https://github.com/cowprotocol/docs) repo, walks the `docs/cow-protocol/` folder (and `docs/README.md`) and produces a single text file in the format:
  ```
  ==> docs/cow-protocol/concepts/order-types/market-orders.md <==
  (file content)
  ```
- **Output:** `data/cow-docs/cow_docs.txt` (or path given in `--output`).
- **Command:** `python scripts/cow-1-create-docs-dataset/main.py --output data/cow-docs/cow_docs.txt`

### 1.2 Order Book OpenAPI (optional)

- **Script:** `scripts/cow-2-fetch-openapi/main.py`
- **What it does:** Fetches the Order Book API OpenAPI spec and saves it as YAML.
- **Output:** `data/cow-docs/openapi.yml`.
- **Use:** Included as a source in RAG for parameter-level answers (endpoints, fields, errors).

### 1.3 Environment variables

- **Base:** `OP_CHAT_BASE_PATH` points to the folder containing `cow-docs/` (e.g. `../../data` or an absolute path).
- **Files:** Inside `cow-docs/` we expect:
  - `cow_docs.txt` (artifact from step 1.1)
  - `openapi.yml` (optional, step 1.2)
  - `faiss/` (created in step 2).

---

## 2. Building the FAISS index (once, or when updating docs)

- **Module:** `cow_brains.build_faiss`  
- **Command:** `cd pkg/cow-app && OP_CHAT_BASE_PATH=... GOOGLE_API_KEY=... poetry run python -m cow_brains.build_faiss`

**Internal steps:**

1. **Load documents**
   - `DataExporter.get_dataframe()` calls document strategies:
     - **CowDocsProcessingStrategy** (`documents_cow.py`): reads `cow_docs.txt`, splits by `==> path <==`, splits each doc by Markdown headers (##, ###, …) and produces fragments with metadata (URL in `https://docs.cow.fi/...`).
     - **OpenApiOrderbookStrategy** (`openapi_orderbook.py`): reads `openapi.yml`, produces one fragment per endpoint and per schema, with fixed Order Book API URL.
   - The resulting DataFrame has columns: `url`, `last_date`, `content` (LangChain `Document` objects), `type_db_info`.

2. **Embeddings**
   - Uses the configured embedding model (e.g. `gemini-embedding-001`) via `access_APIs.get_embedding(EMBEDDING_MODEL)` (Gemini, with `GOOGLE_API_KEY`).

3. **FAISS**
   - `FAISS.from_documents(documents, embeddings)` builds the vector index.
   - `db.save_local(COW_FAISS_PATH)` writes to `data/cow-docs/faiss/` (files `index.faiss` and `index.pkl`).

So the “docs” the chat uses are: fragments from CoW Markdown + OpenAPI chunks, all indexed by vector in FAISS.

---

## 3. API startup (backend)

- **App:** `pkg/cow-app/cow_app/api.py` (Quart/uvicorn).
- **Startup:** Loads `.env` from `pkg/cow-app` (e.g. `GOOGLE_API_KEY`, `OP_CHAT_BASE_PATH`), then imports `cow_brains.process_question`.
- **Routes:**
  - `GET /up` → health check.
  - `POST /predict` → body `{ "question": "...", "memory": [ { "name": "user"|"chat", "message": "..." } ] }` → response `{ "data": { "answer": "...", "url_supporting": ["..."] }, "error": null }`.

---

## 4. When the user sends a question in the chat

### 4.1 Frontend

- The user types in the field and submits.
- The frontend (Next.js) calls `POST NEXT_PUBLIC_CHAT_API_URL` (e.g. `http://localhost:8000/predict`) with `{ question, memory }`.
- On response, it fills the assistant bubble with `data.answer` and references `data.url_supporting`.

### 4.2 Backend: `process_question` (cow_brains)

1. **Index check**
   - If `COW_FAISS_PATH` is not an existing directory, returns a message asking to run `python -m cow_brains.build_faiss`.

2. **Context DataFrame**
   - `DataExporter.get_dataframe()` returns the same type of DataFrame used in the build (docs + OpenAPI), cached. Used to filter/map context by URL.

3. **Retriever**
   - `RetrieverBuilder.build_faiss_retriever(faiss_path=COW_FAISS_PATH, embedding_model=EMBEDDING_MODEL, k=5)` loads the saved FAISS and exposes a function that, given a string (question or expansion), returns the `k` most similar documents.

4. **RAG (rag_brains pipeline)**
   - **Preprocessor (LLM 1 – Gemini):** Receives the question and history. Decides whether it can answer from history alone (`needs_info=False`) or needs more context (`needs_info=True`). In the second case, returns questions and keywords for retrieval.
   - **Retrieval:** The retriever is called with those questions/keywords; FAISS returns the closest fragments in embedding space.
   - **Context filter:** Fragments are formatted as text (with URLs in context) and passed to the responder.
   - **Responder (LLM 2 – Gemini):** Receives the question, formatted context, and CoW instructions (answer at parameter level, cite URLs, do not invent endpoints). Returns `answer` (text) and `url_supporting` (list of cited URLs).
   - The system may do multiple rounds of “expand question → retrieve → respond” until it has a sufficient answer or hits the limit.

5. **Final response**
   - `process_question` returns `{ "data": { "answer": "...", "url_supporting": ["https://docs.cow.fi/...", ...] }, "error": null }`. On error, fills `data.answer` with the error message and optionally `error`.

### 4.3 Frontend again

- Receives the JSON and updates chat state with `data.answer` and `data.url_supporting`.
- `formatAnswerWithReferences` builds the response text and links [1], [2], … from `url_supporting`, normalizing `docs.cow.fi` URLs (lowercase, etc.) to avoid 404s.
- The message component renders the text and clickable references (Markdown + links).

---

## 5. One-sentence summary

**Setup:** Scripts produce `cow_docs.txt` and (optional) `openapi.yml` → **Build:** `cow_brains.build_faiss` builds the FAISS from these sources with Gemini embeddings → **API:** `/predict` uses that FAISS and the rag_brains RAG pipeline (preprocessor + retriever + Gemini responder) to produce `answer` and `url_supporting` → **Frontend:** Displays the answer and references as links to docs.cow.fi and Order Book API.

---

## File reference

| Step              | Location |
|-------------------|----------|
| Create docs artifact | `scripts/cow-1-create-docs-dataset/main.py` |
| Fetch OpenAPI      | `scripts/cow-2-fetch-openapi/main.py` |
| Docs strategy     | `pkg/cow-brains/cow_brains/documents_cow.py` |
| OpenAPI strategy  | `pkg/cow-brains/cow_brains/openapi_orderbook.py` |
| DataExporter       | `pkg/cow-brains/cow_brains/data_exporter.py` |
| Build FAISS        | `pkg/cow-brains/cow_brains/build_faiss.py` |
| CoW config         | `pkg/cow-brains/cow_brains/config.py` |
| process_question   | `pkg/cow-brains/cow_brains/process_question.py` |
| HTTP API           | `pkg/cow-app/cow_app/api.py` |
| RAG (preprocessor + responder) | `pkg/rag-brains/rag_brains/chat/system_structure.py`, `model_utils.py` |
| References in UI   | `www/src/lib/chat-utils.ts` (`formatAnswerWithReferences`) |
