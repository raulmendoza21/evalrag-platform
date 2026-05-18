"""Document persistence."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

import asyncpg


async def get_default_tenant_id(conn: asyncpg.Connection) -> UUID:
    row = await conn.fetchrow("SELECT id FROM tenants WHERE name = 'default'")
    if row is None:
        raise RuntimeError("Default tenant not seeded; run migrations.")
    return row["id"]


async def find_by_hash(
    conn: asyncpg.Connection, tenant_id: UUID, content_hash: str
) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        "SELECT * FROM documents WHERE tenant_id = $1 AND content_hash = $2",
        tenant_id,
        content_hash,
    )
    return dict(row) if row else None


async def create_pending(
    conn: asyncpg.Connection,
    tenant_id: UUID,
    filename: str,
    content_hash: str,
    byte_size: int,
    storage_path: str,
) -> dict[str, Any]:
    row = await conn.fetchrow(
        """
        INSERT INTO documents (tenant_id, filename, content_hash, byte_size, storage_path)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
        """,
        tenant_id,
        filename,
        content_hash,
        byte_size,
        storage_path,
    )
    return dict(row)


async def mark_indexed(
    conn: asyncpg.Connection,
    document_id: UUID,
    page_count: int,
    chunk_count: int,
) -> dict[str, Any]:
    row = await conn.fetchrow(
        """
        UPDATE documents
           SET status='indexed', page_count=$2, chunk_count=$3, indexed_at=$4, error=NULL
         WHERE id=$1
        RETURNING *
        """,
        document_id,
        page_count,
        chunk_count,
        datetime.utcnow(),
    )
    return dict(row)


async def mark_failed(
    conn: asyncpg.Connection, document_id: UUID, error: str
) -> None:
    await conn.execute(
        "UPDATE documents SET status='failed', error=$2 WHERE id=$1",
        document_id,
        error[:1000],
    )


async def list_documents(
    conn: asyncpg.Connection, tenant_id: UUID
) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        "SELECT * FROM documents WHERE tenant_id=$1 ORDER BY created_at DESC",
        tenant_id,
    )
    return [dict(r) for r in rows]


async def get_document(
    conn: asyncpg.Connection, tenant_id: UUID, document_id: UUID
) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        "SELECT * FROM documents WHERE tenant_id=$1 AND id=$2",
        tenant_id,
        document_id,
    )
    return dict(row) if row else None


async def delete_document(
    conn: asyncpg.Connection, tenant_id: UUID, document_id: UUID
) -> bool:
    result = await conn.execute(
        "DELETE FROM documents WHERE tenant_id=$1 AND id=$2",
        tenant_id,
        document_id,
    )
    return result.endswith(" 1")
