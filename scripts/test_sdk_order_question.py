#!/usr/bin/env python3
"""
Test SDK order-creation question locally to verify prompt/retriever changes.

Run (from repo root; GOOGLE_API_KEY in pkg/cow-app/.env to match backend):
  cd pkg/cow-app && OP_CHAT_BASE_PATH=../../data poetry run python -u ../../scripts/test_sdk_order_question.py

  If deployed works but local hangs: use the same API key in pkg/cow-app/.env as in your deployment (Vercel/Railway). The script loads that file first so it matches the backend. If it still hangs after "Starting RAG predict...", the first Gemini call may be rate-limited (429); wait or check quota.

Checklist for the answer (SDK-consistent):
  - Prefer the flow the docs present as main (e.g. TradingSdk / getQuote → postSwapOrderFromQuote).
  - Code example uses exact class/method names from context (no invented APIs).
  - Does NOT lead with CowSdk + orderBook.getQuote/orderBook.sendOrder unless context only has that.
"""
import asyncio
import os
import sys

repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo not in sys.path:
    sys.path.insert(0, repo)

if not os.getenv("OP_CHAT_BASE_PATH") and os.path.isdir(os.path.join(repo, "data", "cow-docs", "faiss")):
    os.environ["OP_CHAT_BASE_PATH"] = os.path.join(repo, "data")

# Load .env same as deployed/local backend: pkg/cow-app/.env first (API loads this),
# then repo root, so cow-app key takes precedence and matches backend.
from dotenv import load_dotenv
_env_app = os.path.join(repo, "pkg", "cow-app", ".env")
_env_root = os.path.join(repo, ".env")
if os.path.isfile(_env_app):
    load_dotenv(_env_app)
if os.path.isfile(_env_root):
    load_dotenv(_env_root)


def _env_diagnostic():
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
    key_ok = bool(key.strip())
    base = os.getenv("OP_CHAT_BASE_PATH", "")
    return f"GOOGLE_API_KEY={'set' if key_ok else 'NOT SET'}, OP_CHAT_BASE_PATH={base or '(not set)'}"

QUESTION = "How do I create an order using the SDK?"


def check_sdk_consistent(ans: str):
    """Return (ok, list of notes). Prefer TradingSdk flow; no hardcoded CowSdk as primary."""
    lower = (ans or "").lower()
    notes = []
    # Prefer high-level flow (TradingSdk / getQuote / postSwapOrderFromQuote) when in context
    if "tradingsdk" in lower or "trading sdk" in lower or "postswaporderfromquote" in lower or "post swap order" in lower:
        notes.append("+ Mentions TradingSdk / postSwapOrderFromQuote (recommended flow)")
    if "getquote" in lower or "get quote" in lower:
        notes.append("+ getQuote flow present")
    # Should not lead with low-level only
    if "cowsdk" in lower and "orderbook" in lower and "tradingsdk" not in lower and "trading sdk" not in lower:
        notes.append("- Only CowSdk+orderBook (no TradingSdk); consider adding TradingSdk context")
    if "typescript" in lower or "javascript" in lower:
        notes.append("+ Includes TS/JS code example")
    ok = bool(notes) and not any(n.startswith("-") for n in notes)
    return ok, notes


async def main():
    print("Env:", _env_diagnostic(), flush=True)
    print("Question:", QUESTION, flush=True)
    print("Calling process_question (verbose=True to see progress)...", flush=True)
    from cow_brains.process_question import process_question

    r = await process_question(QUESTION, [], verbose=True)
    err = r.get("error")
    data = r.get("data") or {}
    ans = (data.get("answer") or "").strip()
    urls = data.get("url_supporting") or []

    if err:
        print("ERROR:", err)
        return
    print("Answer:\n")
    print(ans)
    print()
    print("References:", len(urls))
    for u in urls:
        print(" -", u)
    print()
    ok, notes = check_sdk_consistent(ans)
    print("SDK consistency check:", "OK" if ok else "Review")
    for n in notes:
        print(" ", n)


if __name__ == "__main__":
    asyncio.run(main())
