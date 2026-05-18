"""Chunk persistence + retrieval-side queries."""
from __future__ import annotations

from typing import Any
from uuid import UUID

import asyncpg

from app.services.chunking_service import Chunk


async def bulk_insert_chunks(
    conn: asyncpg.Connection,
    tenant_id: UUID,
    document_id: UUID,
    chunks: list[Chunk],
) -> list[UUID]:
    """Insert chunks and return their generated UUIDs in chunk_index order."""
    if not chunks:
        return []
    rows = await conn.fetch(
        """
        INSERT INTO chunks (document_id, tenant_id, page, chunk_index, text, token_count)
        SELECT $1, $2, c.page, c.chunk_index, c.text, c.token_count
          FROM UNNEST($3::int[], $4::int[], $5::text[], $6::int[])
            AS c(page, chunk_index, text, token_count)
        RETURNING id, chunk_index
        """,
        document_id,
        tenant_id,
        [c.page for c in chunks],
        [c.chunk_index for c in chunks],
        [c.text for c in chunks],
        [c.token_count for c in chunks],
    )
    rows_sorted = sorted(rows, key=lambda r: r["chunk_index"])
    return [r["id"] for r in rows_sorted]


async def search_sparse(
    conn: asyncpg.Connection,
    tenant_id: UUID,
    query: str,
    limit: int,
) -> list[tuple[UUID, float]]:
    """BM25-style ranking via Postgres ts_rank_cd on the GIN index."""
    if not query.strip() or limit <= 0:
        return []
    rows = await conn.fetch(
        """
        SELECT id,
               ts_rank_cd(to_tsvector('simple', text), q) AS score
          FROM chunks, plainto_tsquery('simple', $1) AS q
         WHERE tenant_id = $2
           AND to_tsvector('simple', text) @@ q
         ORDER BY score DESC
         LIMIT $3
        """,
        query,
        tenant_id,
        limit,
    )
    return [(r["id"], float(r["score"])) for r in rows]


async def get_chunks_by_ids(
    conn: asyncpg.Connection,
    tenant_id: UUID,
    chunk_ids: list[UUID],
) -> dict[UUID, dict[str, Any]]:
    """Hydrate chunk rows by id, filtered by tenant. Returns {chunk_id: row}."""
    if not chunk_ids:
        return {}
    rows = await conn.fetch(
        """
        SELECT id, document_id, tenant_id, page, chunk_index, text, token_count
          FROM chunks
         WHERE tenant_id = $1
           AND id = ANY($2::uuid[])
        """,
        tenant_id,
        chunk_ids,
    )
    return {r["id"]: dict(r) for r in rows}
