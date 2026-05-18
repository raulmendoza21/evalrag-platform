"""Application settings loaded from environment variables."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_env: str = "development"
    app_port: int = 8000
    secret_key: str = "change-me"

    # LLM
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    openai_api_key: str = ""

    # Embeddings
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

    # Vector DB
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "evalrag_chunks"

    # Postgres
    postgres_url: str = Field(
        default="postgresql://evalrag:evalrag@postgres:5432/evalrag"
    )

    # RAG
    chunk_size: int = 800
    chunk_overlap: int = 150

    # Storage
    storage_dir: str = "/storage"


@lru_cache
def get_settings() -> Settings:
    return Settings()
