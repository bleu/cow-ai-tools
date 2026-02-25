# Testing the CoW Backend (health + RAG/FAISS)

Use these steps to verify the backend is working: health check, then a real question (RAG + Gemini).

## 1. Health check (API up)

Confirms the API is responding (does not test FAISS or Gemini).

**Local (port 8000):**
```bash
curl -s http://localhost:8000/up
```

**Deployed (replace with your backend URL):**
```bash
curl -s https://your-backend.up.railway.app/up
```

**Expected response:** `{"status":"healthy","service":"chat-api"}` (and HTTP 200).

If you get 404 or 500, the deploy or route is wrong. If you get 200, go to step 2.

---

## 2. RAG test (real question)

Confirms FAISS (retrieval), context, and model response.

**Local:**
```bash
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I compute or pass appData / appDataHash when creating an order?", "memory": []}'
```

**Deployed:**
```bash
curl -s -X POST https://your-backend.up.railway.app/predict \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I compute or pass appData / appDataHash when creating an order?", "memory": []}'
```

**What to check in the response (JSON):**

- **`error: null`** and **`data`** present → success.
- **`data.answer`** → response text (should mention appData/endpoint/References).
- **`data.url_supporting`** → array of URLs used (e.g. docs.cow.fi). For in-docs questions, it should not be empty.
- If **`error`** says something like "CoW FAISS index not found" → FAISS is not at `OP_CHAT_BASE_PATH` (data not deployed or wrong path).
- If **`error`** mentions API key / Gemini → check `GOOGLE_API_KEY` in the project's env vars.

---

## 3. Other test questions

Use questions from [cow_test_questions.md](./cow_test_questions.md). In-docs examples (should answer with references):

- `"What is the GPv2VaultRelayer and where do I find its address per chain?"`
- `"How do I get a quote before creating an order?"`

Out-of-docs example (should decline or say it's not in context):

- `"How do I create an order on Uniswap?"`

Only change the `"question"` value in `-d '{"question": "...", "memory": []}'`.

---

## 4. Quick summary

| Test        | Endpoint        | What it validates                          |
|-------------|-----------------|--------------------------------------------|
| Health      | `GET /up`       | API is up                                  |
| RAG + model | `POST /predict` | FAISS, context, Gemini, normalization     |

Base URL: use your backend URL (e.g. `https://xxx.up.railway.app` or `https://xxx.onrender.com`).
