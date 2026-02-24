# Como funciona o CoW AI – do setup das docs até a resposta no chat

Fluxo completo: preparação dos dados → índice vetorial → API → RAG → frontend.

---

## 1. Setup das documentações (uma vez)

### 1.1 Artefato de docs (Markdown)

- **Script:** `scripts/cow-1-create-docs-dataset/main.py`
- **O que faz:** Clona o repositório [cowprotocol/docs](https://github.com/cowprotocol/docs), percorre a pasta `docs/cow-protocol/` (e `docs/README.md`) e gera um único arquivo de texto no formato:
  ```
  ==> docs/cow-protocol/concepts/order-types/market-orders.md <==
  (conteúdo do arquivo)
  ```
- **Saída:** `data/cow-docs/cow_docs.txt` (ou caminho passado em `--output`).
- **Comando:** `python scripts/cow-1-create-docs-dataset/main.py --output data/cow-docs/cow_docs.txt`

### 1.2 OpenAPI do Order Book (opcional)

- **Script:** `scripts/cow-2-fetch-openapi/main.py`
- **O que faz:** Baixa o spec OpenAPI da Order Book API e salva em YAML.
- **Saída:** `data/cow-docs/openapi.yml`.
- **Uso:** Incluído como fonte no RAG para respostas em nível de parâmetro (endpoints, campos, erros).

### 1.3 Variáveis de ambiente

- **Base:** `OP_CHAT_BASE_PATH` aponta para a pasta onde estão `cow-docs/` (ex.: `../../data` ou caminho absoluto).
- **Arquivos:** Dentro de `cow-docs/` esperamos:
  - `cow_docs.txt` (artefato do passo 1.1)
  - `openapi.yml` (opcional, passo 1.2)
  - `faiss/` (criada no passo 2).

---

## 2. Construção do índice FAISS (uma vez, ou ao atualizar docs)

- **Módulo:** `cow_brains.build_faiss`  
- **Comando:** `cd pkg/op-app && PROJECT=cow OP_CHAT_BASE_PATH=... GOOGLE_API_KEY=... poetry run python -m cow_brains.build_faiss`

**Passo a passo interno:**

1. **Carregar documentos**
   - `DataExporter.get_dataframe()` chama as estratégias de documento:
     - **CowDocsProcessingStrategy** (`documents_cow.py`): lê `cow_docs.txt`, quebra por `==> path <==`, divide cada doc por headers Markdown (##, ###, …) e gera fragmentos com metadados (URL em `https://docs.cow.fi/...`).
     - **OpenApiOrderbookStrategy** (`openapi_orderbook.py`): lê `openapi.yml`, gera um fragmento por endpoint e por schema, com URL fixa da Order Book API.
   - O DataFrame resultante tem colunas: `url`, `last_date`, `content` (objetos `Document` do LangChain), `type_db_info`.

2. **Embeddings**
   - Usa o modelo de embeddings configurado (ex.: `gemini-embedding-001`) via `access_APIs.get_embedding(EMBEDDING_MODEL)` (Gemini, com `GOOGLE_API_KEY`).

3. **FAISS**
   - `FAISS.from_documents(documents, embeddings)` monta o índice vetorial.
   - `db.save_local(COW_FAISS_PATH)` grava em `data/cow-docs/faiss/` (arquivos `index.faiss` e `index.pkl`).

Assim, as “docs” que o chat usa são: fragmentos dos Markdown do CoW + chunks do OpenAPI, todos indexados por vetor no FAISS.

---

## 3. Subida da API (backend)

- **App:** `pkg/op-app/op_app/api.py` (Quart).
- **Ativação CoW:** `PROJECT=cow` (ou `USE_COW=true`) e, se quiser, `OP_CHAT_BASE_PATH` no `.env` ou no ambiente.
- **Início:** Carrega `.env` de `pkg/op-app` (ex.: `GOOGLE_API_KEY`), depois importa `cow_brains.process_question` quando o projeto é CoW.
- **Rotas:**
  - `GET /up` → health check.
  - `POST /predict` → corpo `{ "question": "...", "memory": [ { "name": "user"|"chat", "message": "..." } ] }` → resposta `{ "data": { "answer": "...", "url_supporting": ["..."] }, "error": null }`.

---

## 4. Quando o usuário envia uma pergunta no chat

### 4.1 Frontend

- O usuário digita no campo e envia.
- O frontend (Next.js) chama `POST NEXT_PUBLIC_CHAT_API_URL` (ex.: `http://localhost:8000/predict`) com `{ question, memory }`.
- Ao receber a resposta, preenche a bolha da assistente com `data.answer` e as referências `data.url_supporting`.

### 4.2 Backend: `process_question` (cow_brains)

1. **Checagem do índice**
   - Se `COW_FAISS_PATH` não for um diretório existente, devolve mensagem pedindo para rodar `python -m cow_brains.build_faiss`.

2. **DataFrame de contexto**
   - `DataExporter.get_dataframe()` devolve o mesmo tipo de DataFrame usado no build (docs + OpenAPI), em cache. Será usado para filtrar/mapear contexto por URL.

3. **Retriever**
   - `RetrieverBuilder.build_faiss_retriever(faiss_path=COW_FAISS_PATH, embedding_model=EMBEDDING_MODEL, k=5)` carrega o FAISS salvo e expõe uma função que, dada uma string (pergunta ou expansão), retorna os `k` documentos mais similares.

4. **RAG (op_brains.RAGSystem)**
   - **Preprocessador (LLM 1 – Gemini):** Recebe a pergunta e o histórico. Decide se já dá para responder só com o histórico (`needs_info=False`) ou se precisa buscar mais contexto (`needs_info=True`). No segundo caso, devolve perguntas e palavras-chave para busca.
   - **Busca:** O retriever é chamado com essas perguntas/palavras-chave; o FAISS devolve os fragmentos mais próximos no espaço de embeddings.
   - **Filtro de contexto:** Os fragmentos são formatados em texto (com URLs no contexto) e passados ao respondente.
   - **Respondente (LLM 2 – Gemini):** Recebe a pergunta, o contexto formatado e as instruções CoW (responder em nível de parâmetro, citar URLs, não inventar endpoints). Devolve `answer` (texto) e `url_supporting` (lista de URLs citadas).
   - O sistema pode fazer mais de uma rodada de “expandir pergunta → buscar → responder” até achar resposta suficiente ou atingir o limite.

5. **Resposta final**
   - `process_question` devolve `{ "data": { "answer": "...", "url_supporting": ["https://docs.cow.fi/...", ...] }, "error": null }`. Em erro, preenche `data.answer` com a mensagem de erro e opcionalmente `error`.

### 4.3 Frontend de novo

- Recebe o JSON e atualiza o estado do chat com `data.answer` e `data.url_supporting`.
- `formatAnswerWithReferences` monta o texto da resposta e os links [1], [2], … a partir de `url_supporting`, normalizando URLs `docs.cow.fi` (lowercase, etc.) para evitar 404.
- O componente de mensagem renderiza o texto e as referências clicáveis (Markdown + links).

---

## 5. Resumo em uma frase

**Setup:** Scripts geram `cow_docs.txt` e (opcional) `openapi.yml` → **Build:** `cow_brains.build_faiss` gera o FAISS a partir dessas fontes com embeddings Gemini → **API:** Com `PROJECT=cow`, o `/predict` usa esse FAISS e o pipeline RAG do op_brains (preprocessador + retriever + respondente Gemini) para produzir `answer` e `url_supporting` → **Frontend:** Exibe a resposta e as referências como links para docs.cow.fi e Order Book API.

---

## Referência rápida de arquivos

| Etapa              | Onde está |
|--------------------|-----------|
| Criar artefato docs | `scripts/cow-1-create-docs-dataset/main.py` |
| Fetch OpenAPI      | `scripts/cow-2-fetch-openapi/main.py` |
| Estratégia docs    | `pkg/cow-brains/cow_brains/documents_cow.py` |
| Estratégia OpenAPI | `pkg/cow-brains/cow_brains/openapi_orderbook.py` |
| DataExporter       | `pkg/cow-brains/cow_brains/data_exporter.py` |
| Build FAISS        | `pkg/cow-brains/cow_brains/build_faiss.py` |
| Config CoW         | `pkg/cow-brains/cow_brains/config.py` |
| process_question   | `pkg/cow-brains/cow_brains/process_question.py` |
| API HTTP           | `pkg/op-app/op_app/api.py` |
| RAG (preprocessador + respondente) | `pkg/op-brains/op_brains/chat/system_structure.py`, `model_utils.py` |
| Referências no UI  | `www/src/lib/chat-utils.ts` (`formatAnswerWithReferences`) |
