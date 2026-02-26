#!/usr/bin/env python3
"""
Mede a latência da API Gemini (chat + embeddings). Rode com GOOGLE_API_KEY definido.

  cd pkg/cow-app && GOOGLE_API_KEY=... poetry run python ../../scripts/test_gemini_latency.py

(Use o ambiente do cow-app para ter google-generativeai instalado.)

Se algum passo levar >5s, a API Gemini ou a rede é provável causa do atraso no chat CoW.
"""
import os
import sys
import time
from pathlib import Path

# Carregar .env do cow-app se existir
_repo = Path(__file__).resolve().parents[1]
_env = _repo / "pkg" / "cow-app" / ".env"
if _env.is_file():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env)
    except ImportError:
        pass

def main():
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        print("Defina GOOGLE_API_KEY (ou GEMINI_API_KEY) e rode de novo.")
        return 1

    try:
        import google.generativeai as genai
    except ImportError:
        print("Instale: pip install google-generativeai")
        return 1

    genai.configure(api_key=key)
    print("Testando latência da API Gemini (1 chamada por tipo)...\n")

    # 1. Embedding
    try:
        t0 = time.perf_counter()
        genai.embed_content(
            model="models/gemini-embedding-001",
            content="How do I set token approval for gasless swap?",
        )
        elapsed = time.perf_counter() - t0
        print(f"  embed_content:         {elapsed:.2f}s")
        if elapsed > 3:
            print("    -> Lento. Embeddings podem ser o gargalo.")
    except Exception as e:
        print(f"  embed_content: ERRO {e}")
        return 1

    # 2. Chat (generate_content)
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        t0 = time.perf_counter()
        model.generate_content(
            "Reply in one word: OK",
            generation_config=genai.GenerationConfig(max_output_tokens=10),
        )
        elapsed = time.perf_counter() - t0
        print(f"  generate_content:     {elapsed:.2f}s")
        if elapsed > 5:
            print("    -> Lento. O chat Gemini é provável causa do atraso.")
    except Exception as e:
        print(f"  generate_content: ERRO {e}")
        return 1

    print("\nSe os dois passos forem rápidos (<2s cada), o atraso vem do número de chamadas no RAG (várias buscas + 2 LLM).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
