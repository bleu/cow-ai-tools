"""CoW Protocol documentation (==> path <== artifact) for RAG."""
import re
import time
from typing import List

import pandas as pd
from langchain_core.documents.base import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter

from cow_brains.config import DOCS_PATH

NOW = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
DOCS_BASE_URL = "https://docs.cow.fi/"


def _path_to_url(rel_path: str) -> str:
    """Build docs.cow.fi URL from artifact path. Uses lowercase path to match live site."""
    s = rel_path.strip()
    if s.endswith(".md"):
        s = s[:-3]
    if s == "docs/README":
        return DOCS_BASE_URL.rstrip("/")
    if s.startswith("docs/"):
        s = s[5:]  # len("docs/") == 5
    # Live site uses lowercase paths and hyphens in slugs (e.g. vault-relayer not vault_relayer)
    path = "/".join(p.lower().replace("_", "-") for p in s.split("/") if p)
    return (DOCS_BASE_URL + path).rstrip("/")


class CowDocsProcessingStrategy:
    name_source = "documentation"

    @staticmethod
    async def langchain_process(
        file_path: str = DOCS_PATH,
        headers_to_split_on: List[tuple] | None = None,
        **kwargs,
    ) -> List[Document]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
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
        fragments = await CowDocsProcessingStrategy.langchain_process(**kwargs)
        data = [(f.metadata["url"], NOW, f, "fragments_docs") for f in fragments]
        return pd.DataFrame(data, columns=["url", "last_date", "content", "type_db_info"])
