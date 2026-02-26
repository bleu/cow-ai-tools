#!/usr/bin/env python3
"""
Test the four golden questions locally (RAG + Gemini).
Run: cd pkg/cow-app && OP_CHAT_BASE_PATH=../../data poetry run python ../../scripts/test_cow_answers_local.py
"""
import asyncio
import os
import sys

repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if __name__ == "__main__":
    if repo not in sys.path:
        sys.path.insert(0, repo)

_env = os.path.join(repo, "pkg", "cow-app", ".env")
if os.path.isfile(_env):
    from dotenv import load_dotenv
    load_dotenv(_env)
if not os.getenv("OP_CHAT_BASE_PATH") and os.path.isdir(os.path.join(repo, "data", "cow-docs", "faiss")):
    os.environ["OP_CHAT_BASE_PATH"] = os.path.join(repo, "data")
os.environ.setdefault("PROJECT", "cow")

QUESTIONS = [
    "How do I set token approval via ABI for a gasless swap?",
    "How do I set buyAmount with slippage when creating an order?",
    "What does InsufficientBalance mean and how do I fix it?",
    "When should I use fast vs optimal quoting?",
]


def refused(ans: str) -> bool:
    lower = (ans or "").lower()
    return (
        "cannot provide" in lower
        or "unable to provide" in lower
        or "unable to answer" in lower
        or "does not include" in lower
        or "does not contain" in lower
        or "refer to the official documentation" in lower
        or "does not provide specific details" in lower
        or "with the given context" in lower
    )


async def main():
    from cow_brains.process_question import process_question

    print("Testing CoW answers locally (4 questions)...\n")
    n_ok = 0
    for i, q in enumerate(QUESTIONS, 1):
        print(f"[{i}/4] {q[:60]}...")
        try:
            r = await process_question(q, [], verbose=False)
            err = r.get("error")
            data = r.get("data") or {}
            ans = (data.get("answer") or "").strip()
            urls = data.get("url_supporting") or []
            if err:
                print(f"      ERROR: {err[:80]}")
                continue
            ref = "Refused" if refused(ans) else "OK"
            if not refused(ans) and ans:
                n_ok += 1
            print(f"      Refs: {len(urls)} | {ref}")
            print(f"      Excerpt: {(ans[:200] + '...') if len(ans) > 200 else ans}")
        except Exception as e:
            print(f"      Exception: {e}")
        print()
    print(f"Result: {n_ok}/4 questions answered without refusal.")


if __name__ == "__main__":
    asyncio.run(main())
