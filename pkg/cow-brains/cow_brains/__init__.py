"""
CoW Protocol RAG: docs + Order Book API. No Optimism/OP code.
CoW-only RAG: config, documents, build_faiss, process_question (uses rag_brains).
"""
from cow_brains.process_question import process_question
from cow_brains.config import (
    SCOPE,
    CHAT_MODEL,
    EMBEDDING_MODEL,
    DOCS_PATH,
    COW_FAISS_PATH,
    COW_OPENAPI_PATH,
)

__all__ = [
    "process_question",
    "SCOPE",
    "CHAT_MODEL",
    "EMBEDDING_MODEL",
    "DOCS_PATH",
    "COW_FAISS_PATH",
    "COW_OPENAPI_PATH",
]
