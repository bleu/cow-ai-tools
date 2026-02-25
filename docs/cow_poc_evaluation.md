# CoW PoC – Evaluation (Phase 3.2)

Instructions for running the **golden questions** in the chat, measuring relevance/accuracy, and documenting results and gaps.

## How to evaluate

1. **Bring up the stack:** docs artifact + (optional) OpenAPI in `data/cow-docs/`, FAISS built, API with `USE_COW=true`, frontend with `NEXT_PUBLIC_BRAND=cow` and `NEXT_PUBLIC_CHAT_API_URL` pointing to the API.

2. **Question source:** [docs/cow_golden_questions.md](cow_golden_questions.md) (24 questions in 5 areas).

3. **For each question:**
   - Paste the question in the chat (no extra context).
   - Annotate: **useful response (yes/no)**, **cites doc/spec (yes/no)**, **parameter-level accuracy (yes/no/N/A)**, **notes** (hallucinated errors, wrong URL, etc.).

4. **Success criteria (suggested):**
   - Response cites documentation or Order Book API when applicable.
   - Response is accurate at parameter level (field names, endpoints) when the question asks for it.
   - Does not invent endpoints, error codes, or behavior.

## Results template

Fill in after an evaluation run. Evaluation date: ___________

| # | Question (summary) | Useful response | Cites doc/spec | Parameter accuracy | Notes |
|---|--------------------|-----------------|----------------|--------------------|-------|
| 1 | buyAmount + slippage | | | | |
| 2 | Does buyAmount include slippage? | | | | |
| … | … | | | | |
| 24 | order status | | | | |

**Summary:** ___/24 useful responses; ___/24 cite doc/spec; ___/24 parameter accuracy when applicable.

## Identified gaps

(List topics or questions where the assistant failed or answered vaguely/incorrectly, and possible improvements: missing doc, chunking, prompt, etc.)

- 
- 

---

*Update this file after each evaluation run to track PoC evolution.*
