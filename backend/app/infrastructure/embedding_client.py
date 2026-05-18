"""Embeddings client (OpenAI by default, swappable)."""
from __future__ import annotations

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import Settings
from app.core.exceptions import EmbeddingError

_client: AsyncOpenAI | None = None


def init_embedding_client(settings: Settings) -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.openai_api_key:
            # Allow boot without key; will fail on first embedding call.
            _client = AsyncOpenAI(api_key="missing")
        else:
            _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


def get_embedding_client() -> AsyncOpenAI:
    if _client is None:
        raise RuntimeError("Embedding client not initialised")
    return _client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def embed_texts(texts: list[str], model: str) -> list[list[float]]:
    if not texts:
        return []
    client = get_embedding_client()
    try:
        resp = await client.embeddings.create(model=model, input=texts)
    except Exception as exc:  # noqa: BLE001
        raise EmbeddingError(str(exc)) from exc
    return [d.embedding for d in resp.data]
