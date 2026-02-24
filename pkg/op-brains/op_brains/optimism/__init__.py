"""
Optimism project: document strategies for governance + forum RAG.

Use when PROJECT=optimism. Exposes chat_sources and strategies for op_data/summarizer.
"""
from op_brains.optimism.documents import (
    FragmentsProcessingStrategy,
    SummaryProcessingStrategy,
    ForumPostsProcessingStrategy,
)

chat_sources = [
    [FragmentsProcessingStrategy],
    [SummaryProcessingStrategy],
]

__all__ = [
    "chat_sources",
    "FragmentsProcessingStrategy",
    "SummaryProcessingStrategy",
    "ForumPostsProcessingStrategy",
]
