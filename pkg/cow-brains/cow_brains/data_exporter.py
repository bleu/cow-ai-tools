"""DataExporter for CoW documents (docs + OpenAPI + CoW Swap)."""
import pandas as pd
from typing import Optional
import asyncio
import time

from cow_brains.documents_cow import CowDocsProcessingStrategy
from cow_brains.documents_cowswap import CowSwapDocsProcessingStrategy
from cow_brains.documents_cowsdk import CowSdkDocsProcessingStrategy
from cow_brains.openapi_orderbook import OpenApiOrderbookStrategy

# CoW Swap and CoW SDK are optional: add only if corresponding artifact exists
chat_sources = [
    [CowDocsProcessingStrategy],
    [OpenApiOrderbookStrategy],
    [CowSwapDocsProcessingStrategy],
    [CowSdkDocsProcessingStrategy],
]


class DataExporter:
    _dataframe_cache: Optional[pd.DataFrame] = None
    _dataframe_cache_time: Optional[float] = None
    _dataframe_cache_with_embedded: Optional[bool] = None
    _cache_lock = asyncio.Lock()
    CACHE_TTL = 60 * 60 * 24

    @classmethod
    async def get_dataframe(cls, only_not_embedded=False):
        async with cls._cache_lock:
            current_time = time.time()
            if (
                cls._dataframe_cache is None
                or (current_time - cls._dataframe_cache_time) > cls.CACHE_TTL
                or cls._dataframe_cache_with_embedded != only_not_embedded
            ):
                context_df = []
                for priority_class in chat_sources:
                    dfs_class = await asyncio.gather(
                        *[source.dataframe_process(only_not_embedded=only_not_embedded) for source in priority_class]
                    )
                    dfs_class = pd.concat(dfs_class)
                    dfs_class = dfs_class.sort_values(by="last_date", ascending=False)
                    context_df.append(dfs_class)
                cls._dataframe_cache_with_embedded = only_not_embedded
                cls._dataframe_cache = pd.concat(context_df)
                cls._dataframe_cache_time = current_time
        return cls._dataframe_cache
