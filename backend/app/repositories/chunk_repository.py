"""Chunk persistence."""
from __future__ import annotations

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
