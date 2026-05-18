"""Qdrant client wrapper."""
from __future__ import annotations

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm

from app.config import Settings

_client: AsyncQdrantClient | None = None


async def init_qdrant(settings: Settings) -> AsyncQdrantClient:
    global _client
    if _client is None:
        _client = AsyncQdrantClient(url=settings.qdrant_url)
        await _ensure_collection(_client, settings)
    return _client


async def close_qdrant() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None


def get_qdrant() -> AsyncQdrantClient:
    if _client is None:
        raise RuntimeError("Qdrant client not initialised")
    return _client


async def _ensure_collection(client: AsyncQdrantClient, settings: Settings) -> None:
    existing = {c.name for c in (await client.get_collections()).collections}
    if settings.qdrant_collection in existing:
        return
    await client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=qm.VectorParams(
            size=settings.embedding_dim,
            distance=qm.Distance.COSINE,
        ),
    )
    # Payload indexes for filtering
    for field in ("tenant_id", "document_id"):
        await client.create_payload_index(
            collection_name=settings.qdrant_collection,
            field_name=field,
            field_schema=qm.PayloadSchemaType.KEYWORD,
        )
