"""CoW Swap (cowprotocol/cowswap) README + docs for RAG. Same artifact format as cow_docs (==> path <==)."""
import re
import time
from typing import List

import pandas as pd
from langchain_core.documents.base import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter

from cow_brains.config import COW_SWAP_DOCS_PATH

NOW = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
GITHUB_BASE = "https://github.com/cowprotocol/cowswap/blob/develop/"


def _path_to_url(rel_path: str) -> str:
    """Build GitHub blob URL for cowswap file."""
    s = rel_path.strip()
    return GITHUB_BASE + s


class CowSwapDocsProcessingStrategy:
    name_source = "cowswap_docs"

    @staticmethod
    async def langchain_process(
        file_path: str = "",
        headers_to_split_on: List[tuple] | None = None,
        **kwargs,
    ) -> List[Document]:
        path = file_path or COW_SWAP_DOCS_PATH or ""
        if not path:
            return []
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                docs_read = f.read()
        except FileNotFoundError:
            return []

        parts = re.split(r"==> | <==", docs_read)
        docs = []
        path_parts = []
        for d in parts:
            stripped = d.strip()
            if stripped and "\n" not in d:
                path_parts = [p.strip() for p in d.split("/") if p.strip()]
            elif path_parts and stripped:
                path_str = "/".join(path_parts[:-1])
                doc_name = path_parts[-1]
                docs.append({"path": path_str, "document_name": doc_name, "content": d})
        docs = [d for d in docs if d["content"].strip() != ""]

        if headers_to_split_on is None:
            headers_to_split_on = [
                ("##", "header 2"), ("###", "header 3"), ("####", "header 4"),
                ("#####", "header 5"), ("######", "header 6"),
            ]
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        fragments_docs: List[Document] = []
        for d in docs:
            full_path = f"{d['path']}/{d['document_name']}" if d["path"] else d["document_name"]
            url = _path_to_url(full_path)
            for fragment in splitter.split_text(d["content"]):
                fragment.metadata["url"] = url
                fragment.metadata["path"] = d["path"]
                fragment.metadata["document_name"] = d["document_name"]
                fragment.metadata["type_db_info"] = "docs_fragment"
                fragments_docs.append(fragment)
        return fragments_docs

    @staticmethod
    async def dataframe_process(**kwargs) -> pd.DataFrame:
        fragments = await CowSwapDocsProcessingStrategy.langchain_process(**kwargs)
        if not fragments:
            return pd.DataFrame(columns=["url", "last_date", "content", "type_db_info"])
        data = [(f.metadata["url"], NOW, f, "docs_fragment") for f in fragments]
        return pd.DataFrame(data, columns=["url", "last_date", "content", "type_db_info"])
