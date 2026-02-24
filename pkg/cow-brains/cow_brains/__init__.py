"""
CoW Protocol RAG: docs + Order Book API. No Optimism/OP code.
Use this package when PROJECT=cow; use op_brains when running Optimism.
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
