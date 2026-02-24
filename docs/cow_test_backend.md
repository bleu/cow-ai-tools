# Testar o backend CoW (health + RAG/FAISS)

Use estes passos para validar se o backend está funcionando: health check, depois uma pergunta real (RAG + Gemini).

## 1. Health check (API no ar)

Confirma que a API está respondendo (não testa FAISS nem Gemini).

**Local (porta 8000):**
```bash
curl -s http://localhost:8000/up
```

**Vercel (troque pela URL do seu projeto):**
```bash
curl -s https://cow-ai-backend.vercel.app/api/up
```

**Resposta esperada:** `{"status":"healthy","service":"chat-api"}` (e status HTTP 200).

Se der 404 ou 500, o deploy ou a rota estão errados. Se der 200, siga para o passo 2.

---

## 2. Teste RAG (pergunta real)

Confirma FAISS (retrieval), contexto e resposta do modelo.

**Local:**
```bash
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I compute or pass appData / appDataHash when creating an order?", "memory": []}'
```

**Vercel:**
```bash
curl -s -X POST https://cow-ai-backend.vercel.app/api/predict \
  -H "Content-Type: application/json" \
  -d '{"question": "How do I compute or pass appData / appDataHash when creating an order?", "memory": []}'
```

**O que verificar na resposta (JSON):**

- **`error: null`** e **`data`** presente → sucesso.
- **`data.answer`** → texto da resposta (deve falar de appData/endpoint/References).
- **`data.url_supporting`** → array de URLs usadas (ex.: docs.cow.fi). Se for pergunta in-docs, não deve ser vazio.
- Se **`error`** tiver mensagem tipo "CoW FAISS index not found" → FAISS não está em `OP_CHAT_BASE_PATH` (dados não subiram ou path errado).
- Se **`error`** falar de API key / Gemini → conferir `GOOGLE_API_KEY` nas env vars do projeto Vercel.

---

## 3. Outras perguntas de teste

Use perguntas do [cow_test_questions.md](./cow_test_questions.md). Exemplos in-docs (devem responder com referências):

- `"What is the GPv2VaultRelayer and where do I find its address per chain?"`
- `"How do I get a quote before creating an order?"`

Exemplo out-of-docs (deve recusar ou dizer que não tem no contexto):

- `"How do I create an order on Uniswap?"`

Troque apenas o valor de `"question"` no `-d '{"question": "...", "memory": []}'`.

---

## 4. Resumo rápido

| Teste        | Endpoint        | O que valida                          |
|-------------|-----------------|----------------------------------------|
| Health      | `GET /api/up`   | API no ar                              |
| RAG + modelo| `POST /api/predict` | FAISS, contexto, Gemini, normalização |

Base URL no Vercel: `https://cow-ai-backend.vercel.app` (troque pelo seu projeto se for outro).
