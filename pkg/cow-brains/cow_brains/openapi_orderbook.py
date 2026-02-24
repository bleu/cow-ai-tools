"""CoW Order Book OpenAPI → LangChain documents for RAG."""
import time
from pathlib import Path
from typing import Any, List

import pandas as pd
from langchain_core.documents.base import Document

try:
    import yaml
except ImportError:
    yaml = None

from cow_brains.config import COW_OPENAPI_PATH

NOW = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
ORDERBOOK_DOCS_URL = "https://docs.cow.fi/cow-protocol/reference/apis/orderbook"


def _desc(o: Any) -> str:
    if o is None:
        return ""
    if isinstance(o, str):
        return o.strip()
    if isinstance(o, dict) and "description" in o:
        return str(o["description"]).strip()
    return ""


def _ref_name(ref: Any) -> str:
    if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
        return ref.split("/")[-1]
    return str(ref)


def _endpoint_chunk(path: str, method: str, op: dict, spec: dict) -> str:
    parts = [f"## {method.upper()} {path}", ""]
    if op.get("summary"):
        parts.append(op["summary"].strip())
        parts.append("")
    if op.get("description"):
        parts.append(op["description"].strip())
        parts.append("")
    params = op.get("parameters") or []
    if params:
        parts.append("### Parameters")
        for p in params:
            name = p.get("name", "?")
            loc = p.get("in", "query")
            desc = _desc(p)
            req = "required" if p.get("required") else "optional"
            parts.append(f"- **{name}** ({loc}, {req}): {desc or p.get('schema', {})}")
        parts.append("")
    body = op.get("requestBody")
    if body:
        content = (body.get("content") or {}).get("application/json") or {}
        schema = content.get("schema")
        if schema:
            parts.append("### Request body")
            parts.append(f"Schema: {_ref_name(schema.get('$ref', schema))}")
            parts.append("")
    responses = op.get("responses") or {}
    for c in sorted(c for c in responses if c.startswith(("4", "5"))):
        parts.append(f"- **{c}**: {_desc(responses[c])}")
    return "\n".join(parts)


def _schema_chunk(name: str, schema: dict, components: dict) -> str:
    parts = [f"## Schema: {name}", ""]
    if schema.get("description"):
        parts.append(schema["description"].strip())
        parts.append("")
    props = schema.get("properties") or {}
    if props:
        parts.append("### Properties")
        for k, v in props.items():
            ref = v.get("$ref")
            typ = _ref_name(ref) if ref else v.get("type", "object")
            desc = _desc(v)
            req = " (required)" if k in (schema.get("required") or []) else ""
            parts.append(f"- **{k}**{req}: {typ}. {desc}")
    return "\n".join(parts)


def parse_openapi_to_documents(file_path: str) -> List[Document]:
    if yaml is None or not file_path:
        return []
    path = Path(file_path)
    if not path.is_file():
        return []
    try:
        spec = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return []
    if not spec or "paths" not in spec:
        return []
    components = spec.get("components") or {}
    schemas = components.get("schemas") or {}
    docs: List[Document] = []
    for path_str, path_item in spec.get("paths", {}).items():
        for method in ("get", "post", "put", "delete", "patch"):
            op = path_item.get(method)
            if not op:
                continue
            content = _endpoint_chunk(path_str, method, op, spec)
            if content.strip():
                docs.append(Document(
                    page_content=content,
                    metadata={"url": ORDERBOOK_DOCS_URL, "type_db_info": "api-endpoint", "path": path_str, "method": method.upper(), "operationId": op.get("operationId", "")},
                ))
    for name, schema in schemas.items():
        if not isinstance(schema, dict):
            continue
        content = _schema_chunk(name, schema, schemas)
        if content.strip():
            docs.append(Document(
                page_content=content,
                metadata={"url": ORDERBOOK_DOCS_URL, "type_db_info": "api-schema", "schema_name": name},
            ))
    return docs


class OpenApiOrderbookStrategy:
    name_source = "openapi_orderbook"

    @classmethod
    async def langchain_process(cls, file_path: str = "", **kwargs) -> List[Document]:
        path = file_path or COW_OPENAPI_PATH or ""
        return parse_openapi_to_documents(path) if path else []

    @classmethod
    async def dataframe_process(cls, **kwargs) -> pd.DataFrame:
        docs = await cls.langchain_process(**kwargs)
        if not docs:
            return pd.DataFrame(columns=["url", "last_date", "content", "type_db_info"])
        data = [(d.metadata.get("url", ""), NOW, d, d.metadata.get("type_db_info", "api")) for d in docs]
        return pd.DataFrame(data, columns=["url", "last_date", "content", "type_db_info"])
