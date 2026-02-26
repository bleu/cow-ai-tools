#!/usr/bin/env python3
"""
Test that the approval/ABI/gasless question is answered using the vault-relayer docs.

Option A – against deployed API (no local FAISS/keys needed):
  COW_API_URL=https://cow-ai-tools-production.up.railway.app python scripts/test_approval_question.py

Option B – local RAG (needs FAISS index + GOOGLE_API_KEY in pkg/cow-app/.env):
  cd pkg/cow-app && OP_CHAT_BASE_PATH=../../data poetry run python ../../scripts/test_approval_question.py
"""
import asyncio
import os
import sys

# Allow running from repo root when invoked as ../../scripts/test_approval_question.py from pkg/cow-app
if __name__ == "__main__":
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Load pkg/cow-app/.env so GOOGLE_API_KEY is set when running locally
_env = os.path.join(repo, "pkg", "cow-app", ".env")
if os.path.isfile(_env):
    from dotenv import load_dotenv
    load_dotenv(_env)
# Set base path if not set (for when run from pkg/op-app with ../../data)
if not os.getenv("OP_CHAT_BASE_PATH") and os.path.isdir(os.path.join(repo, "data", "cow-docs", "faiss")):
    os.environ["OP_CHAT_BASE_PATH"] = os.path.join(repo, "data")

os.environ.setdefault("PROJECT", "cow")

# If COW_API_URL is set, call the HTTP API instead of process_question
COW_API_URL = os.getenv("COW_API_URL", "").strip()


async def main():
    question = "How do I set token approval via ABI for a gasless swap?"

    if COW_API_URL:
        import urllib.request
        import json
        url = (COW_API_URL.rstrip("/") + "/predict").replace("/predict/predict", "/predict")
        req = urllib.request.Request(
            url,
            data=json.dumps({"question": question, "memory": []}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
        error = result.get("error")
        data = result.get("data") or {}
        answer = (data.get("answer") or "").strip()
        urls = data.get("url_supporting") or []
    else:
        from cow_brains.process_question import process_question

        result = await process_question(question, memory=[], verbose=False)
        error = result.get("error")
        data = result.get("data") or {}
        answer = (data.get("answer") or "").strip()
        urls = data.get("url_supporting") or []

    print(f"Question: {question}\n")
    if error:
        print(f"ERROR: {error}\n")
        sys.exit(1)

    print("Answer (first 1200 chars):")
    print("-" * 60)
    print(answer[:1200] + ("..." if len(answer) > 1200 else ""))
    print("-" * 60)
    print(f"\nReferences: {len(urls)} URL(s)")
    for i, u in enumerate(urls[:5], 1):
        print(f"  [{i}] {u}")

    # Success criteria: answer should mention approval/vault/relayer/allowance and not say "cannot provide"
    lower = answer.lower()
    has_content = any(
        phrase in lower
        for phrase in (
            "vault relayer",
            "gpv2vaultrelayer",
            "approv",
            "allowance",
            "erc-20",
            "gasless",
            "balancer",
        )
    )
    refused = "cannot provide" in lower or "does not include" in lower or "does not contain" in lower

    if has_content and not refused:
        print("\n✓ PASS: Answer includes approval/vault-relayer content and does not refuse.")
    elif refused:
        print("\n✗ FAIL: Answer still says it cannot provide / docs do not include.")
    else:
        print("\n? CHECK: Answer may be relevant; verify manually.")


if __name__ == "__main__":
    asyncio.run(main())
