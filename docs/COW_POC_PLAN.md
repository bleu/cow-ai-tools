# CoW Protocol Integration Documentation – PoC Plan

Plano para a PoC do **CoW Protocol Integration Documentation** (RFP: [forum.cow.fi/t/cow-protocol-integration-documentation/3360](https://forum.cow.fi/t/cow-protocol-integration-documentation/3360)), usando como base o repositório forkado do **op-ai-tools** (Optimism) e as referências OP Chat, CoW Docs e RFP.

---

## 1. Alinhamento com a RFP

### 1.1 Objetivo da RFP

- Reduzir atrito para **integradores** (parceiros, devs).
- Foco em **clareza em nível de parâmetro**, não em conceitos gerais.
- Entregar valor em: **Order creation** (slippage, formatos de amount), **Approval setup** (ABI, relay), **Error responses**, **Endpoint selection** (fast vs optimal quoting).

### 1.2 Track escolhido: **Track A (Systematic/AI-Based)**

- Solução **RAG** que usa documentação e spec existentes.
- Camada que melhora conforme a documentação subjacente melhora.
- PoC demonstra: sistema implantado + respostas precisas nas áreas prioritárias.

### 1.3 Escopo In e Out (conforme RFP)

| Dentro do escopo | Fora do escopo |
|------------------|----------------|
| Order Book API, quoting, order creation, approvals, erros, quickstart integração | Solver docs, CoW AMM, MEV Blocker, migração de plataforma, guias conceituais para end-users |

---

## 2. Referências utilizadas

| Recurso | Uso |
|--------|-----|
| **OP Chat** ([op-chat.bleu.builders/chat](https://op-chat.bleu.builders/chat)) | Referência de UX e fluxo do chat. |
| **op-ai-tools** ([github.com/bleu/op-ai-tools](https://github.com/bleu/op-ai-tools)) | Base técnica: RAG, ingestão, API, frontend. |
| **CoW Docs** ([docs.cow.fi](https://docs.cow.fi/)) | Conteúdo público a ser indexado. |
| **cowprotocol/docs** ([github.com/cowprotocol/docs](https://github.com/cowprotocol/docs)) | Fonte primária: markdown (Docusaurus, pasta `docs/`). |
| **Order Book API** | [docs.cow.fi – Order book API](https://docs.cow.fi/cow-protocol/reference/apis/orderbook); OpenAPI em [api.cow.fi/docs](https://api.cow.fi/docs) quando disponível. |

---

## 3. Arquitetura base (herdada do OP)

### 3.1 Backend simplificado para PoC

Para a PoC o backend foi reduzido ao mínimo:

- **Mantido:** Quart, CORS, rota `GET /up` (health), rota `POST /predict` (question + memory → RAG).
- **Removido:** Tortoise/DB, PostHog, Honeybadger, Quart-Tasks (cron), rate limiter, sync de forum/snapshot, eventos de analytics no predict.

O app (`pkg/op-app`) passa a depender só do necessário para servir o chat; `op-core` e `op-data` continuam como dependências transitivas do `op-brains` até a migração para fontes só de arquivo (CoW docs + FAISS local). Quando houver `cow-brains` com docs + OpenAPI em arquivo e FAISS local, será possível remover também `op-data` e `op-core` do stack.

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js) – www/                                        │
│  Chat UI, memory, env: NEXT_PUBLIC_CHAT_API_URL → backend /predict│
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  Backend (Quart) – pkg/op-app (simplificado)                      │
│  GET /up | POST /predict { question, memory } → RAG → { data, error }│
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  RAG (pkg/op-brains → cow-brains)                                 │
│  • Retriever: FAISS + índices (keywords/questions)                │
│  • Expander: query → perguntas/keywords                            │
│  • LLM: resposta com contexto recuperado                           │
└─────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐         ┌─────────────────┐         ┌─────────────────┐
│ Docs (MD)     │         │ OpenAPI Order   │         │ (Opcional)       │
│ cowprotocol/  │         │ Book – endpoints│         │ Erros / ref     │
│ docs          │         │ schemas, params │         │ extra            │
└───────────────┘         └─────────────────┘         └─────────────────┘
```

- **Fonte 1 – Documentação:** Markdown do repositório `cowprotocol/docs` (estrutura Docusaurus, pasta `docs/`), chunked por seção (headers), com `metadata.url` apontando para `https://docs.cow.fi/...`.
- **Fonte 2 – API:** Order Book OpenAPI (endpoints, parâmetros, schemas, erros) parseado e chunked por endpoint/schema/erro para retrieval em nível de parâmetro (como no exemplo da aplicação do Mig no fórum).
- **PoC:** Podemos começar só com docs markdown; OpenAPI na fase 2 para máxima precisão em “slippage”, “buyAmount”, “approval”, etc.

---

## 4. Plano de implementação em fases

### Fase 1: Fundação (repo + docs CoW)

**Objetivo:** Chat RAG respondendo com base apenas na documentação pública do CoW (Concepts, Tutorials, Technical Reference), sem forum/snapshot.

| # | Tarefa | Detalhes |
|---|--------|----------|
| 1.1 | Renomear / duplicar pacotes | `op-brains` → `cow-brains` (ou manter nome e trocar apenas fontes e config). `op-app` → `cow-app`, `op-artifacts` → `cow-artifacts`. Ajustar imports e pyproject. |
| 1.2 | Config CoW | Novo `config.py`: `SCOPE = "CoW Protocol / Order Book API / Integration"`, `DOCS_PATH` ou fonte remota para `cowprotocol/docs`. Remover ou desabilitar `RAW_FORUM_DB`, `FORUM_SUMMARY_DB`, `SNAPSHOT_DB` para PoC. |
| 1.3 | Script de ingestão de docs | Novo script (ex.: `scripts/cow-1-create-docs-dataset`) que clona ou baixa `cowprotocol/docs` e gera um artefato no formato esperado pelo pipeline (ex.: formato `==> path <==` como em `governance_docs.txt`, ou CSV com `fullpath`, `content`). Filtro: apenas `docs/` relevantes para integração (Technical Reference, Tutorials de API/order creation; opcionalmente Concepts úteis). |
| 1.4 | Estratégia de documentos CoW | Nova classe em `documents/` (ex.: `cow.py`): `CowDocsProcessingStrategy` inspirada em `FragmentsProcessingStrategy`. Leitura do artefato (txt ou CSV), split por headers Markdown, `metadata.url` = `https://docs.cow.fi/...` (mapear path do repo → URL da doc). |
| 1.5 | Chat sources | Em `documents/__init__.py`, usar apenas a estratégia de docs CoW (sem forum/summary). Manter interface `DataExporter` e `chat_sources` para o retriever. |
| 1.6 | Setup & índices | `setup.py`: gerar FAISS e índices (keywords/questions) a partir dos chunks de docs CoW. Ajustar prompts de geração de perguntas para escopo “CoW Protocol integration / Order Book API”. |
| 1.7 | API e frontend | Backend: manter `/predict`; apontar para `cow-brains` (ou config “cow”). Frontend: trocar branding (Optimism → CoW), `NEXT_PUBLIC_CHAT_API_URL` para o backend do CoW. |
| 1.8 | README e env | README do repo descrevendo PoC CoW, pré-requisitos, como rodar ingestão, setup e chat. `.envrc.example` com variáveis necessárias (embedding, LLM, API URL). |

**Entregável Fase 1:** Chat funcionando que responde sobre CoW Protocol com base apenas na documentação indexada (docs.cow.fi via repo).

---

### Fase 2: Order Book API (OpenAPI) e precisão em parâmetros

**Objetivo:** Respostas com precisão em nível de parâmetro (slippage, buyAmount, approvals, erros), alinhado às prioridades da RFP.

| # | Tarefa | Detalhes |
|---|--------|----------|
| 2.1 | Obter OpenAPI Order Book | Localizar spec (api.cow.fi/docs ou repo cowprotocol/services) e salvar localmente (YAML/JSON). |
| 2.2 | Parser OpenAPI | Módulo que lê o spec, resolve `$ref`/`allOf`, extrai endpoints, request/response schemas, enums, descrições e erros. Gera “chunks” por endpoint, por schema e por erro (como no exemplo Mig: api-endpoint, api-schema, api-error). |
| 2.3 | Ingestão OpenAPI | Incluir esses chunks no pipeline de embedding e nos índices (keywords/questions). Metadata: tipo (endpoint/schema/error), path, method, nome do parâmetro, etc. |
| 2.4 | Integrar no DataExporter | Segunda fonte em `chat_sources`: estratégia que retorna documentos gerados a partir do OpenAPI. Retriever passa a considerar docs + API. |
| 2.5 | Prompt/system | ~~Ajustar system prompt do chat para priorizar respostas baseadas em “parameter-level” (Order creation, Approvals, Errors, Fast vs Optimal), citando endpoint e parâmetro quando aplicável.~~ **Feito:** `model_utils.py` – instruções CoW no responder e no Answer; preprocessor com termos CoW; `ContextHandling.format` para docs_fragment/api-endpoint. |
| 2.6 | Quick prompts (opcional) | No frontend, sugerir perguntas rápidas: “How do I set buyAmount with slippage?”, “How do I set token approval for gasless swap?”, “When to use fast vs optimal quote?”, “What does error X mean?”. |

**Entregável Fase 2:** Assistente que responde com precisão sobre campos da API (slippage, amounts, approvals) e erros, com citações à doc e ao spec.

---

### Fase 3: Quickstart e validação (RFP)

**Objetivo:** Demonstrar “quickstart que leva a um primeiro order em <10 min” e validação nas áreas prioritárias.

| # | Tarefa | Detalhes |
|---|--------|----------|
| 3.1 | Conjunto de “golden questions” | 20–30 perguntas cobrindo: order creation (slippage, formatos), approvals (ABI, relay), erros comuns, fast vs optimal. Respostas de referência (ou critérios de sucesso) para avaliação. |
| 3.2 | Avaliação PoC | Rodar golden questions no chat; medir relevância e precisão (manual ou com checklist). Documentar resultados e gaps. **Feito:** `docs/cow_poc_evaluation.md` com instruções e template de resultados/gaps. |
| 3.3 | Quickstart em texto/código | Guia mínimo (markdown ou página no repo): “Do primeiro order em <10 min” usando a API (e/ou SDK), com links para o chat para dúvidas de parâmetro. **Feito:** `docs/cow_quickstart_first_order.md`. Opcional: script exemplo (ex.: Sepolia) como extensão futura. |
| 3.4 | Documentação do PoC | README atualizado, possível `docs/COW_POC_PLAN.md` (este doc), e se aplicável um sumário para submissão à RFP (o que foi feito, como testar, limites). |

**Entregável Fase 3:** Evidência de que o assistente cobre as prioridades da RFP + quickstart documentado.

---

## 5. Decisões técnicas resumidas

| Aspecto | Decisão |
|--------|--------|
| **Fontes de dados** | 1) Markdown de cowprotocol/docs (filtrado por integração). 2) Order Book OpenAPI (endpoints, schemas, erros). |
| **Vector store** | Manter FAISS no PoC (como no OP); migrar para pgvector/Neon só se for requisito de deploy. |
| **Embedding** | Manter modelo configurável (ex.: OpenAI ada-002 ou text-embedding-3-small). |
| **LLM** | Manter configurável (ex.: GPT-4o-mini / Claude). |
| **Forum / Snapshot** | Não usar na PoC (fora do escopo da RFP de integração). |
| **Naming** | Renomear para `cow-*` onde fizer sentido para clareza; ou manter `op-*` e identificar por config. |

---

## 6. Riscos e dependências

- **OpenAPI:** Se a spec do Order Book não estiver pública ou estável, a Fase 2 pode depender de acesso ou de export manual a partir de api.cow.fi/docs.
- **Manutenção:** RFP menciona “Swagger/OpenAPI sync as a prerequisite”; a PoC pode assumir um snapshot da spec e documentar que updates exigem re-ingestão.
- **Escopo da doc:** Focar apenas em paths do `docs/` relacionados a CoW Protocol (referência de APIs, tutorials de integração); excluir CoW AMM, MEV Blocker, etc., conforme RFP.

---

## 7. Próximos passos imediatos

1. **Confirmar** com o time: Track A apenas (RAG) ou híbrido com conteúdo manual (Track B) depois.
2. **Implementar Fase 1:** config, script de clone/processamento de cowprotocol/docs, `CowDocsProcessingStrategy`, troca de fontes no DataExporter, setup + API + frontend com branding CoW.
3. **Localizar** OpenAPI Order Book (URL ou arquivo) para preparar Fase 2.
4. **Definir** 20–30 golden questions e critérios de aceite para a validação da RFP.

---

## 8. Passos técnicos concretos (checklist)

### 8.1 Repo e config

- [x] Manter `op-brains`; usar flag `USE_COW` e config CoW no mesmo pacote.
- [x] Em `op-brains`: `config.py` com `USE_COW`, `SCOPE`, `DOCS_PATH`/`COW_DOCS_PATH`, `COW_FAISS_PATH`; sem DB para CoW.
- [x] `documents/cow.py`: `CowDocsProcessingStrategy` (ler artefato, split por headers, `metadata.url` = `https://docs.cow.fi/...`).
- [x] `documents/__init__.py`: quando `USE_COW`, `chat_sources = [[CowDocsProcessingStrategy]]`.
- [x] Ajustar `setup.py` para escopo CoW (TYPE_GUIDELINES, import condicional de op_data).

### 8.2 Ingestão CoW Docs

- [x] Script `scripts/cow-1-create-docs-dataset/main.py`: clone cowprotocol/docs, percorrer `docs/cow-protocol/**/*.md` e `docs/README.md`, gerar `==> path <==\n{content}` em `data/cow-docs/cow_docs.txt` (opção `--no-pull`).
- [x] Em `cow.py`: mapear path para URL `https://docs.cow.fi/...` (sem `.md`).
- [x] Config: `USE_COW` + `COW_DOCS_PATH`; `CowDocsProcessingStrategy` usa `DOCS_PATH`.

### 8.3 OpenAPI (Fase 2)

- [x] **URL do OpenAPI:** `https://raw.githubusercontent.com/cowprotocol/services/main/crates/orderbook/openapi.yml` (referenciado em docs/reference/apis/orderbook.mdx).
- [x] Script `scripts/cow-2-fetch-openapi/main.py` para baixar o spec em `data/cow-docs/openapi.yml`.
- [x] Módulo `op_brains/documents/openapi_orderbook.py`: parse do spec (YAML), geração de chunks por endpoint e por schema; metadata `api-endpoint` / `api-schema`, URL para docs.cow.fi.
- [x] Quando `USE_COW` e `COW_OPENAPI_PATH` aponta para ficheiro existente, `OpenApiOrderbookStrategy` é a segunda fonte em `chat_sources`. Rebuild do FAISS para incluir chunks OpenAPI.

### 8.4 Backend e frontend

- [x] **Backend PoC:** API já simplificada: só Quart + CORS + `/up` + `/predict` (sem DB, analytics, cron). Ver `pkg/op-app/op_app/api.py`.
- [x] Backend CoW: op-app com `USE_COW=true` chama `process_question` do op-brains e usa FAISS/índices CoW (docs + OpenAPI).
- [x] **System prompt (2.5):** Em `model_utils.py`, instruções CoW no responder (parameter-level, citar endpoint/URL) e no Answer; preprocessor com termos CoW; `ContextHandling.format` inclui `docs_fragment` e `api-endpoint`/`api-schema` no contexto.
- [x] Frontend: branding CoW via `NEXT_PUBLIC_BRAND=cow` (header “CoW Protocol”, empty state, quick prompts: buyAmount/slippage, approval gasless, fast vs optimal, erros). `.envrc.example`: `NEXT_PUBLIC_CHAT_API_URL=http://localhost:8000/predict`.

### 8.5 Deploy e validação

- [x] README com instruções: ingestão → (opcional) fetch OpenAPI → build FAISS → rodar API → rodar www; golden questions referenciadas.
- [x] Golden questions em `docs/cow_golden_questions.md` (24 perguntas nas áreas: order creation, approvals, quoting, errors, endpoints).
- [x] Avaliação PoC (3.2): `docs/cow_poc_evaluation.md` com instruções para rodar golden questions e template de resultados/gaps.
- [x] Quickstart (3.3): `docs/cow_quickstart_first_order.md` – guia “do primeiro order em <10 min” com links para API e chat.

### 8.6 Quickstart (“primeiro order em &lt;10 min”)

- [x] Fluxo documentado no README (CoW PoC): criar artefato docs → (opcional) fetch OpenAPI → build FAISS → rodar API → rodar www com `NEXT_PUBLIC_BRAND=cow`. O chat serve como suporte para dúvidas de parâmetro; guia “do primeiro order” em código fica como extensão futura (ex.: script Sepolia).

---

## 9. Referências rápidas

- RFP: https://forum.cow.fi/t/cow-protocol-integration-documentation/3360  
- CoW Docs: https://docs.cow.fi/  
- CoW Docs repo: https://github.com/cowprotocol/docs  
- Order Book API (doc): https://docs.cow.fi/cow-protocol/reference/apis/orderbook  
- OP Chat: https://op-chat.bleu.builders/chat  
- OP AI Tools repo: https://github.com/bleu/op-ai-tools  
