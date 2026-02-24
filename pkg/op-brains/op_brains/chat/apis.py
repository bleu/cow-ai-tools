from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.embeddings import HuggingFaceEmbeddings
from op_brains.config import (
    EMBEDDING_MODEL,
    CHAT_MODEL,
)


def _is_gemini_embedding(model: str) -> bool:
    m = (model or "").lower()
    return "gemini" in m or m in ("text-embedding-004", "embedding-001", "models/embedding-001", "models/gemini-embedding-001")


class access_APIs:
    @staticmethod
    def get_llm(model: str = CHAT_MODEL, **kwargs):
        if "gpt" in model:
            return ChatOpenAI(model=model, **kwargs)
        elif "claude" in model:
            return ChatAnthropic(model=model, **kwargs)
        elif "gemini" in model.lower():
            from .gemini_adapter import GeminiChatAdapter
            return GeminiChatAdapter(model=model, **kwargs)
        elif "free" in model:
            from .test_chat_model import GroqLLM
            return GroqLLM()
        else:
            raise ValueError(f"Model {model} not recognized")

    @staticmethod
    def get_embedding(model: str = EMBEDDING_MODEL, **kwargs):
        if _is_gemini_embedding(model):
            from .gemini_adapter import GeminiEmbeddings
            # Same GOOGLE_API_KEY as chat. Default: gemini-embedding-001 (3072 dims).
            if model.startswith("models/"):
                embedding_model = model
            elif model in ("text-embedding-004", "embedding-001"):
                embedding_model = f"models/{model}"
            else:
                embedding_model = "models/gemini-embedding-001"
            return GeminiEmbeddings(model=embedding_model, **kwargs)
        if "free" in model:
            return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        return OpenAIEmbeddings(model=model, **kwargs)
