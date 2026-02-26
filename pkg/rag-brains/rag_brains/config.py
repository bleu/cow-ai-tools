"""Minimal config for RAG pipeline. CoW-specific config lives in cow_brains.config."""
import os
from dotenv import load_dotenv

load_dotenv()

BASE_PATH = os.getenv("OP_CHAT_BASE_PATH", os.path.expanduser("../../data"))
SCOPE = os.getenv("RAG_SCOPE", "CoW Protocol / Order Book API / Integration")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.0-flash")
