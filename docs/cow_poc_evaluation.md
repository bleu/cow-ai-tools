# CoW PoC – Avaliação (Fase 3.2)

Instruções para rodar as **golden questions** no chat, medir relevância/precisão e documentar resultados e gaps.

## Como avaliar

1. **Subir o stack:** artefato docs + (opcional) OpenAPI em `data/cow-docs/`, FAISS construído, API com `USE_COW=true`, frontend com `NEXT_PUBLIC_BRAND=cow` e `NEXT_PUBLIC_CHAT_API_URL` apontando para a API.

2. **Fonte das perguntas:** [docs/cow_golden_questions.md](cow_golden_questions.md) (24 perguntas em 5 áreas).

3. **Por cada pergunta:**
   - Colar a pergunta no chat (sem contexto extra).
   - Anotar: **resposta útil (sim/não)**, **cita doc/spec (sim/não)**, **precisão em parâmetro (sim/não/NA)**, **notas** (erros inventados, URL errada, etc.).

4. **Critérios de sucesso (sugerido):**
   - Resposta cita documentação ou Order Book API quando aplicável.
   - Resposta é precisa em nível de parâmetro (nomes de campos, endpoints) quando a pergunta pede.
   - Não inventa endpoints, códigos de erro ou comportamentos.

## Template de resultados

Preencher após uma rodada de avaliação. Data da avaliação: ___________

| # | Pergunta (resumida) | Resposta útil | Cita doc/spec | Precisão parâmetro | Notas |
|---|---------------------|---------------|----------------|--------------------|-------|
| 1 | buyAmount + slippage | | | | |
| 2 | buyAmount inclui slippage? | | | | |
| … | … | | | | |
| 24 | status do order | | | | |

**Resumo:** ___/24 respostas úteis; ___/24 citam doc/spec; ___/24 precisão parâmetro quando aplicável.

## Gaps identificados

(Listar temas ou perguntas em que o assistente falhou ou respondeu de forma vaga/incorreta, e possíveis melhorias: doc faltando, chunking, prompt, etc.)

- 
- 

---

*Atualizar este ficheiro após cada rodada de avaliação para acompanhar evolução do PoC.*
