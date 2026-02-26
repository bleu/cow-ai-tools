"""CoW Protocol project config only. No Optimism references."""
import os
from dotenv import load_dotenv

load_dotenv()


def _resolve_base_path():
    raw = os.getenv("OP_CHAT_BASE_PATH", "").strip()
    if raw and "/path/to/cow-ai-tools" in raw:
        # Placeholder in .env: use repo data dir (pkg/cow-brains/cow_brains -> repo/data)
        this_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.abspath(os.path.join(this_dir, "..", "..", ".."))
        return os.path.join(repo_root, "data")
    if raw:
        return raw
    return os.path.expanduser("../../data")


BASE_PATH = _resolve_base_path()
DOCS_PATH = os.getenv("COW_DOCS_PATH", os.path.join(BASE_PATH, "cow-docs", "cow_docs.txt"))
COW_SWAP_DOCS_PATH = os.getenv("COW_SWAP_DOCS_PATH", os.path.join(BASE_PATH, "cow-docs", "cow_swap_docs.txt"))
COW_FAISS_PATH = os.getenv("COW_FAISS_PATH", os.path.join(BASE_PATH, "cow-docs", "faiss"))
COW_OPENAPI_PATH = os.getenv("COW_OPENAPI_PATH", os.path.join(BASE_PATH, "cow-docs", "openapi.yml"))

if not os.path.isabs(DOCS_PATH):
    DOCS_PATH = os.path.abspath(DOCS_PATH)
if COW_SWAP_DOCS_PATH and not os.path.isabs(COW_SWAP_DOCS_PATH):
    COW_SWAP_DOCS_PATH = os.path.abspath(COW_SWAP_DOCS_PATH)
if not os.path.isfile(COW_SWAP_DOCS_PATH or ""):
    COW_SWAP_DOCS_PATH = ""
if not os.path.isabs(COW_FAISS_PATH):
    COW_FAISS_PATH = os.path.abspath(COW_FAISS_PATH)
if COW_OPENAPI_PATH and not os.path.isabs(COW_OPENAPI_PATH):
    COW_OPENAPI_PATH = os.path.abspath(COW_OPENAPI_PATH)
if not COW_OPENAPI_PATH or not os.path.isfile(COW_OPENAPI_PATH):
    COW_OPENAPI_PATH = ""

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.0-flash")
SCOPE = "CoW Protocol / Order Book API / Integration / docs.cow.fi"
