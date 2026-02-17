import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Common configurations
    DATABASE_URL = os.getenv("DATABASE_URL", "")

    # Paths
    BASE_PATH = os.getenv("OP_CHAT_BASE_PATH", os.path.expanduser("../../data"))

    # Model configurations
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    CHAT_MODEL_OPENAI = os.getenv("CHAT_MODEL_OPENAI", "gpt-4o")
    CHAT_MODEL_CLAUDE = os.getenv("CHAT_MODEL_CLAUDE", "claude-3-sonnet-20240229")

    # Cloudflare R2 configurations
    R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
    R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
    R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL", "")
    R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "op-ai-tools")

    @classmethod
    def get_tortoise_config(cls):
        # Optimized connection pool parameters for Neon Postgres (serverless)
        db_url = cls.DATABASE_URL

        # Neon-specific connection parameters:
        # - min_size=1: Keep minimum connections low for serverless
        # - max_size=5: Reduce max connections to avoid hitting Neon limits
        # - max_queries=1000: Recycle connections after 1000 queries
        # - max_inactive_connection_lifetime=30: Recycle idle connections after 30s (Neon times out after ~60s)
        connection_params = "min_size=1&max_size=5&max_queries=1000&max_inactive_connection_lifetime=30"

        if "?" in db_url:
            db_url += f"&{connection_params}"
        else:
            db_url += f"?{connection_params}"

        return {
            "connections": {"default": db_url},
            "apps": {
                "models": {
                    "models": ["op_data.db.models"],
                    "default_connection": "default",
                },
            },
        }

    @classmethod
    def get_r2_config(cls):
        return {
            "endpoint_url": cls.R2_ENDPOINT_URL,
            "aws_access_key_id": cls.R2_ACCESS_KEY_ID,
            "aws_secret_access_key": cls.R2_SECRET_ACCESS_KEY,
        }


config = Config()
