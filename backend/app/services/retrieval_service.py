"""Hybrid retrieval: dense (Qdrant) + sparse (Postgres BM25) fused with RRF."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from qdrant_client.http import models as qm

from app.config import Settings
from app.infrastructure import postgres, qdrant
from app.infrastructure.embedding_client import embed_texts
from app.repositories import chunk_repository


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: UUID
    document_id: UUID
    page: int
    chunk_index: int
    text: str
    score: float
    sources: tuple[str, ...]  # ("dense",) / ("sparse",) / ("dense","sparse")


def reciprocal_rank_fusion(
    rankings: list[list[UUID]],
    k: int = 60,
) -> list[tuple[UUID, float]]:
    """Fuse multiple ranked lists with Reciprocal Rank Fusion.

    For each ranking, score(doc) += 1 / (k + rank_position_starting_at_1).
    Returns items sorted by fused score desc.
    """
    scores: dict[UUID, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


async def _dense_search(
    settings: Settings,
    tenant_id: UUID,
    query_vector: list[float],
    limit: int,
) -> list[tuple[UUID, float]]:
    client = qdrant.get_qdrant()
    hits = await client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        query_filter=qm.Filter(
            must=[
                qm.FieldCondition(
                    key="tenant_id", match=qm.MatchValue(value=str(tenant_id))
                )
            ]
        ),
        limit=limit,
    )
    return [(UUID(str(h.id)), float(h.score)) for h in hits]


async def hybrid_search(
    settings: Settings,
    tenant_id: UUID,
    query: str,
    k_dense: int = 20,
    k_sparse: int = 20,
    k_final: int = 5,
) -> list[RetrievedChunk]:
    """Run dense + sparse retrieval, fuse with RRF, hydrate, return top-k."""
    if not query.strip() or k_final <= 0:
        return []

    # Dense
    vectors = await embed_texts([query], model=settings.embedding_model)
    dense_hits = await _dense_search(settings, tenant_id, vectors[0], k_dense)
    dense_ids = [cid for cid, _ in dense_hits]

    # Sparse
    pool = postgres.get_pool()
    async with pool.acquire() as conn:
        sparse_hits = await chunk_repository.search_sparse(conn, tenant_id, query, k_sparse)
    sparse_ids = [cid for cid, _ in sparse_hits]

    # Fuse
    fused = reciprocal_rank_fusion([dense_ids, sparse_ids])
    top_ids = [cid for cid, _ in fused[:k_final]]
    if not top_ids:
        return []

    # Hydrate
    async with pool.acquire() as conn:
        hydrated = await chunk_repository.get_chunks_by_ids(conn, tenant_id, top_ids)

    dense_set = {cid for cid, _ in dense_hits}
    sparse_set = {cid for cid, _ in sparse_hits}
    fused_scores = dict(fused)

    out: list[RetrievedChunk] = []
    for cid in top_ids:
        row = hydrated.get(cid)
        if row is None:
            continue  # stale Qdrant vector; chunk row was deleted
        sources: list[str] = []
        if cid in dense_set:
            sources.append("dense")
        if cid in sparse_set:
            sources.append("sparse")
        out.append(
            RetrievedChunk(
                chunk_id=cid,
                document_id=row["document_id"],
                page=row["page"],
                chunk_index=row["chunk_index"],
                text=row["text"],
                score=fused_scores[cid],
                sources=tuple(sources),
            )
        )
    return out
