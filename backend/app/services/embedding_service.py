"""High-level embedding service (swappable provider via config)."""
from __future__ import annotations

from app.config import Settings
from app.infrastructure.embedding_client import embed_texts


async def embed_chunks(settings: Settings, texts: list[str]) -> list[list[float]]:
    """Embed a batch of chunk texts using the configured model."""
    return await embed_texts(texts, model=settings.embedding_model)
