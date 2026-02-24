"""
FAISS index loading for Optimism (from IncrementalIndexerService).
For loading a local FAISS directory (e.g. CoW), use faiss_path= and embedding_model=.
"""
from typing import Tuple, Optional
import os

from langchain_community.vectorstores import FAISS

from op_brains.config import DB_STORAGE_PATH, EMBEDDING_MODEL
import asyncio
from op_brains.chat.apis import access_APIs

from typing import Optional
import time
from aiocache import cached

try:
    from op_core.logger import get_logger
    _logger = get_logger(__name__)
except Exception:
    _logger = None


@cached(ttl=60 * 60 * 24)
async def load_faiss_indexes(
    vectorstore: str = "faiss",
    faiss_path: Optional[str] = None,
    embedding_model: Optional[str] = None,
) -> FAISS:
    """Load FAISS index. If faiss_path and embedding_model are provided, load from that path (for external callers e.g. cow_brains). Otherwise load Optimism indexes from IncrementalIndexerService."""
    if vectorstore != "faiss":
        raise ValueError(f"Unsupported vectorstore: {vectorstore}")

    if faiss_path is not None and embedding_model is not None:
        embeddings = access_APIs.get_embedding(embedding_model)
        if os.path.isdir(faiss_path):
            return FAISS.load_local(faiss_path, embeddings, allow_dangerous_deserialization=True)
        raise FileNotFoundError(f"FAISS index not found at {faiss_path}")

    embeddings = access_APIs.get_embedding(EMBEDDING_MODEL)
    from op_data.sources.incremental_indexer import IncrementalIndexerService
    loaded_dbs = await IncrementalIndexerService.load_faiss_indexes(embeddings)
    merged_db = None
    for key, faiss_index in loaded_dbs.items():
        if merged_db is None:
            merged_db = faiss_index
        else:
            try:
                merged_db.merge_from(faiss_index)
            except Exception as e:
                if _logger:
                    _logger.error("Failed to merge faiss databases")
                raise e
    return merged_db
