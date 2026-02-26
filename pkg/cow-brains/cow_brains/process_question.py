"""CoW RAG: process_question using op_brains pipeline with CoW config and prompts."""
from typing import Dict, Any, List, Tuple
import asyncio
import os

from op_brains.chat import model_utils
from op_brains.chat.system_structure import RAGSystem
from op_brains.chat.utils import normalize_answer_text
from op_brains.chat.apis import access_APIs
from cow_brains.config import CHAT_MODEL, SCOPE, COW_FAISS_PATH, EMBEDDING_MODEL
from cow_brains.data_exporter import DataExporter

try:
    from op_core.logger import get_logger
    logger = get_logger(__name__)
except Exception:
    logger = None

COW_RESPONDER_EXTRA = """

Your audience is developers integrating with the CoW Protocol (Order Book API, docs.cow.fi, CoW Swap frontend). Be direct and practical. Use only the provided context. Each source in the context is numbered [1], [2], [3], etc.—cite using only these numbers in order of first use. List only cited references at the end (e.g. References: [1] [2] [3]).
- **Best solution for developers:** Give the best solution based on all the context you have. When the context includes both Order Book API (HTTP/curl) and CoW SDK (TypeScript/JavaScript) docs, prefer the SDK approach as the primary answer—with a TypeScript or JavaScript code example—because that is the better developer experience. You do not require the user to say "SDK" or "TypeScript"; use the SDK when it is in context and fits the question. You can mention the raw API as an alternative if relevant.
- When the provided context clearly describes appData, appDataHash, the order book API, or how to upload/register data, answer from that context. Do not say you lack information if the context explains how to compute or pass appData/appDataHash—use the context to answer.
- For CoW Swap (the frontend app, widget, or swap UI): if the context includes CoW Swap README or docs (monorepo, apps, widget, embed), use it to answer how to run, integrate, or embed the swap interface. Prefer docs.cow.fi for protocol/API and the cowswap repo context for frontend/structure.
- For the CoW SDK (TypeScript/JavaScript, @cowprotocol/cow-sdk): if the context includes cow-sdk README or docs (getQuote, OrderBookApi, order signing, slippage), use it to give code examples and SDK usage. Prefer SDK docs for "how do I do X with the SDK" or "code example"; combine with API docs when the user wants both API and SDK.
- When the user mentions **TypeScript**, **TS**, **JavaScript**, **SDK**, or asks for **code**: if the context includes CoW SDK package READMEs (packages/sdk, packages/trading, packages/order-book, order-signing), answer with a TypeScript or JavaScript code example using the SDK (e.g. getQuote, signOrder, OrderBookApi). Use a ```typescript or ```javascript code block. If the exact SDK API is not clearly documented in the context, still give a short TS/JS snippet that illustrates the flow (e.g. get quote then build order) and cite the API; do not refuse to answer.
- For token approval, ABI, or gasless swaps: the docs describe ERC-20 allowances to the GPv2VaultRelayer, Balancer external/internal balances (gas-efficient), and the vault relayer. If the context mentions any of these (e.g. "Fallback ERC-20 Allowances", "GPv2VaultRelayer", "approve", "sellTokenBalance"), you must use it to answer. Do not say "I cannot provide" when the context clearly describes approval: give the steps (e.g. approve the sell token for the GPv2VaultRelayer contract; for gasless use internal/external balances per context) and a minimal code hint in a code block. Cite the reference; if the exact ABI is not in the context, say "For the contract address and full ABI see reference [N] below."
- For API errors (e.g. InsufficientBalance, InsufficientAllowance, "what does X mean", "how do I fix"): if the context mentions OrderPostError, errorType, 400, or order validation, use it to explain and suggest fixes. If the context does not list error types but the user asks about a named error (e.g. InsufficientBalance): give a brief interpretation from the name (e.g. "InsufficientBalance usually means the user's sell token balance or allowance is too low for the order; ensure sufficient balance and approve the sell token for the GPv2VaultRelayer") and point to the Order Book API reference [1] for full error details. Never say "I am unable to answer" or "the context does not contain" for error questions—always give a direct answer and cite a reference.
- For buyAmount, slippage, or creating an order (not the widget): If the context includes CoW SDK docs (packages/sdk, packages/trading, order-book), lead with the SDK approach: get a quote (e.g. getQuote or quote endpoint), then build and sign the order with the SDK; include a TypeScript/JavaScript code block. Slippage is often via slippageBps or implicit in the quoted buyAmount. If the context has only API docs, use the HTTP flow: (1) POST /api/v1/quote, (2) use quote response to build/sign order, (3) POST to /api/v1/orders with a curl example. Do not answer with widget or UI slippage settings when the user asks about creating an order programmatically.
- For "how do I" questions (approval, API calls, signing, quoting, order creation): always include a minimal code example inside a markdown fenced code block. Prefer ```typescript or ```javascript when the context includes CoW SDK docs (packages/sdk, packages/trading, order-book)—that is the best solution for developers; otherwise use ```bash for curl or ```json for bodies. Never output raw curl or code without wrapping it in a code block. One short snippet is better than none.
- When you mention "official documentation", "docs", or "find the address/endpoint": always tie it to the reference the user can click. Write e.g. "See reference [1] below for the GPv2VaultRelayer address per network" or "The exact endpoint is documented in [1]." so the user uses [1] instead of searching. Never say only "find it in the official documentation" without pointing to [1] (or the relevant reference number).
- If the context contains concrete values (contract address, base URL, endpoint path), use them in the code example instead of placeholders when possible (e.g. mainnet GPv2VaultRelayer address if present in the context).
- Cite in order of first use: [1] = first source you use, [2] = second, etc. Only cite sources you actually use; the reference list at the end must contain exactly those URLs in that order. Do not invent endpoints or addresses.
- Keep explanations concise; lead with steps or code when the user asks how to do something.

Example style (answer + code + explicit reference):

To get a quote, POST to the Order Book API quote endpoint with sellToken, buyToken, sellAmountBeforeFee, kind, and from. Example:

```bash
curl -X POST "https://api.cow.fi/mainnet/api/v1/quote" \\
  -H "Content-Type: application/json" \\
  -d '{"sellToken": "0x...", "buyToken": "0x...", "sellAmountBeforeFee": "1000000", "kind": "sell", "from": "0xYourAddress"}'
```

For the GPv2VaultRelayer address per network, see reference [1] below.

References: [1] <url from context>"""


def transform_memory_entries(entries: List[Dict[str, str]]) -> List[Tuple[str, str]]:
    return [(e["name"], e["message"]) for e in entries if "message" in e]


async def process_question(
    question: str,
    memory: List[Dict[str, str]],
    verbose: bool = False,
) -> Dict[str, Any]:
    if not os.path.isdir(COW_FAISS_PATH):
        err = f"CoW FAISS index not found at {COW_FAISS_PATH}. Run: python -m cow_brains.build_faiss (with GOOGLE_API_KEY and OP_CHAT_BASE_PATH set)."
        if logger:
            logger.error(err)
        return {"data": {"answer": err, "url_supporting": []}, "error": err}

    contexts_df = await DataExporter.get_dataframe(only_not_embedded=False)
    chat_model = (
        CHAT_MODEL,
        {"temperature": 0.0, "max_retries": 5, "max_tokens": 1024, "timeout": 60},
    )

    try:
        default_retriever = await model_utils.RetrieverBuilder.build_faiss_retriever(
            faiss_path=COW_FAISS_PATH,
            embedding_model=EMBEDDING_MODEL,
            k=8,
        )
        questions_index_retriever = keywords_index_retriever = default_retriever

        def contains(must_contain):
            return lambda similar: [s for s in similar if must_contain in s]

        def _merge_contexts(primary: list, extra: list, max_total: int = 10) -> list:
            """Merge two context lists by URL, keeping order of primary then extra, deduped."""
            seen_urls = set()
            out = []
            for doc_list in (primary, extra):
                for doc in doc_list:
                    meta = getattr(doc, "metadata", None) or {}
                    url = meta.get("url") or getattr(doc, "url", None)
                    key = url or id(doc)
                    if key not in seen_urls:
                        seen_urls.add(key)
                        out.append(doc)
                        if len(out) >= max_total:
                            return out
            return out

        async def retriever(query: dict, reasoning_level: int) -> list:
            if reasoning_level < 1 and "keyword" in query:
                if "instance" in query:
                    return await keywords_index_retriever(
                        query["keyword"], contexts_df, criteria=contains(query["instance"])
                    )
                return await keywords_index_retriever(query["keyword"], contexts_df)
            if "question" in query:
                q = query["question"]
                if reasoning_level < 1:
                    ctx = await questions_index_retriever(q, contexts_df)
                    if len(ctx) > 0:
                        return ctx
                main_ctx = await default_retriever(q, contexts_df)
                q_lower = (q or "").lower()
                # Boosts: one primary by topic; for order/quote/slippage always add SDK so we have best dev solution
                boosts = []
                if any(t in q_lower for t in ("approval", "approve", "abi", "gasless", "allowance", "vault relayer")):
                    boosts.append("GPv2VaultRelayer token allowance approval ERC-20 gasless")
                elif any(t in q_lower for t in ("insufficientbalance", "insufficient allowance", "error type", "what does", "how do i fix", "orderposterror")):
                    boosts.append("OrderPostError InsufficientBalance order validation error 400")
                elif any(t in q_lower for t in ("buyamount", "slippage", "creating an order", "order creation", "sellamount")):
                    boosts.append("POST /api/v1/quote OrderQuoteSide buyAmount sellAmount order parameters")
                    boosts.append("CoW SDK TypeScript getQuote order signing OrderBookApi trading")
                elif any(t in q_lower for t in ("cow swap", "cowswap", "widget", "frontend", "embed", "swap ui", "swap interface")):
                    boosts.append("CoW Swap frontend widget embed monorepo apps")
                elif any(t in q_lower for t in ("sdk", "cow-sdk", "typescript", " ts ", "javascript", "getquote", "orderbookapi", "order signing")):
                    boosts.append("CoW SDK TypeScript getQuote order signing OrderBookApi trading")
                for boost in boosts[:2]:  # cap at 2 to keep latency reasonable
                    extra = await default_retriever(boost, contexts_df)
                    main_ctx = _merge_contexts(main_ctx, extra)
                return main_ctx
            if "query" in query:
                q = query["query"]
                main_ctx = await default_retriever(q, contexts_df)
                q_lower = (q or "").lower()
                boosts = []
                if any(t in q_lower for t in ("approval", "approve", "abi", "gasless", "allowance", "vault relayer")):
                    boosts.append("GPv2VaultRelayer token allowance approval ERC-20 gasless")
                elif any(t in q_lower for t in ("insufficientbalance", "insufficient allowance", "error type", "what does", "how do i fix", "orderposterror")):
                    boosts.append("OrderPostError InsufficientBalance order validation error 400")
                elif any(t in q_lower for t in ("buyamount", "slippage", "creating an order", "order creation", "sellamount")):
                    boosts.append("POST /api/v1/quote OrderQuoteSide buyAmount sellAmount order parameters")
                    boosts.append("CoW SDK TypeScript getQuote order signing OrderBookApi trading")
                elif any(t in q_lower for t in ("cow swap", "cowswap", "widget", "frontend", "embed", "swap ui", "swap interface")):
                    boosts.append("CoW Swap frontend widget embed monorepo apps")
                elif any(t in q_lower for t in ("sdk", "cow-sdk", "typescript", " ts ", "javascript", "getquote", "orderbookapi", "order signing")):
                    boosts.append("CoW SDK TypeScript getQuote order signing OrderBookApi trading")
                for boost in boosts[:2]:
                    extra = await default_retriever(boost, contexts_df)
                    main_ctx = _merge_contexts(main_ctx, extra)
                return main_ctx
            return []

        def preprocessor(llm, **kwargs):
            out = model_utils.Prompt.preprocessor(llm, scope=SCOPE, **kwargs)
            # Limit expansion to reduce retriever calls and latency
            if out and out.get("needs_info") and out.get("expansion"):
                exp = out["expansion"]
                if exp.get("questions"):
                    exp["questions"] = exp["questions"][:2]
                if exp.get("keywords"):
                    exp["keywords"] = exp["keywords"][:2]
            return out

        def responder(llm, final=False, **kwargs):
            return model_utils.Prompt.responder(
                llm, final=final, scope=SCOPE, responder_extra=COW_RESPONDER_EXTRA, **kwargs
            )

        rag_model = RAGSystem(
            reasoning_limit=1,
            models_to_use=[chat_model, chat_model],
            retriever=retriever,
            context_filter=model_utils.ContextHandling.filter,
            system_prompt_preprocessor=preprocessor,
            system_prompt_responder=responder,
        )

        formatted_memory = transform_memory_entries(memory)
        result = await rag_model.predict(
            question, contexts_df, memory=formatted_memory, verbose=verbose
        )
        answer_data = result["answer"]
        raw_answer = answer_data.get("answer") or ""
        normalized_answer = normalize_answer_text(raw_answer)
        return {
            "data": {
                "answer": normalized_answer,
                "url_supporting": answer_data.get("url_supporting") or [],
            },
            "error": None,
        }
    except Exception as e:
        err_msg = str(e)
        if logger:
            logger.error(f"Error during prediction: {err_msg}")
        return {"data": {"answer": err_msg, "url_supporting": []}, "error": err_msg}
