"""
Configuration for Optimism project only. For CoW, use the cow_brains package.
"""
import os
import importlib.resources
import op_artifacts.dbs
import op_artifacts
from dotenv import load_dotenv

load_dotenv()

BASE_PATH = os.getenv("OP_CHAT_BASE_PATH", os.path.expanduser("../../data"))
VECTORSTORE = os.getenv("VECTORSTORE", "faiss")
DOCS_PATH = str(importlib.resources.files(op_artifacts) / "governance_docs.txt")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.0-flash")

CHAT_TEMPERATURE = float(os.getenv("CHAT_TEMPERATURE", "0"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
K_RETRIEVER = int(os.getenv("K_RETRIEVER", "8"))
LOG_FILE = os.path.join(BASE_PATH, "logs.csv")
CHAT_MODEL_OPENAI = os.getenv("CHAT_MODEL_OPENAI", "gpt-4o")
SUMMARIZER_MODEL = os.getenv("SUMMARIZER_MODEL", "gpt-4o-mini")

DB_STORAGE_PATH = importlib.resources.files(op_artifacts.dbs)
POSTHOG_API_KEY = os.getenv("POSTHOG_API_KEY", "")
RAW_FORUM_DB = "RawTopic"
FORUM_SUMMARY_DB = "Topic"
USE_SUMMARY_MOCK_DATA = os.getenv("USE_SUMMARY_MOCK_DATA", "False") == "True"
SNAPSHOT_DB = "SnapshotProposal"

SCOPE = "OPTIMISM GOVERNANCE/OPTIMISM COLLECTIVE/OPTIMISM L2"
