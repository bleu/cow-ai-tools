"""Load FAISS index from a local directory (used by cow_brains)."""
from typing import Optional
import os
from langchain_community.vectorstores import FAISS
from rag_brains.chat.apis import access_APIs
from aiocache import cached

try:
    from cow_core.logger import get_logger
    _logger = get_logger(__name__)
except Exception:
    _logger = None


@cached(ttl=60 * 60 * 24)
async def load_faiss_indexes(
    vectorstore: str = "faiss",
    faiss_path: Optional[str] = None,
    embedding_model: Optional[str] = None,
) -> FAISS:
    """Load FAISS index from faiss_path using embedding_model. Both must be provided."""
    if vectorstore != "faiss":
        raise ValueError(f"Unsupported vectorstore: {vectorstore}")
    if faiss_path is None or embedding_model is None:
        raise ValueError("faiss_path and embedding_model are required")
    embeddings = access_APIs.get_embedding(embedding_model)
    if os.path.isdir(faiss_path):
        return FAISS.load_local(faiss_path, embeddings, allow_dangerous_deserialization=True)
    raise FileNotFoundError(f"FAISS index not found at {faiss_path}")
