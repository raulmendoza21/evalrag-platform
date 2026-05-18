"""Document orchestration: upload → extract → chunk → embed → persist."""
from __future__ import annotations

from uuid import UUID

from qdrant_client.http import models as qm

from app.config import Settings
from app.core.exceptions import IngestionError
from app.core.logging import get_logger
from app.infrastructure import postgres, qdrant, storage
from app.repositories import chunk_repository, document_repository
from app.services.chunking_service import chunk_pages
from app.services.embedding_service import embed_chunks
from app.services.ingestion_service import extract_pages_from_pdf

log = get_logger(__name__)


async def upload_and_index(
    settings: Settings,
    tenant_id: UUID,
    filename: str,
    data: bytes,
) -> tuple[dict, bool]:
    """Idempotent upload + full ingestion pipeline.

    Returns (document_row, deduplicated).
    """
    content_hash = storage.compute_sha256(data)
    pool = postgres.get_pool()

    async with pool.acquire() as conn:
        existing = await document_repository.find_by_hash(conn, tenant_id, content_hash)
        if existing is not None:
            log.info("document.dedup", document_id=str(existing["id"]))
            return existing, True

    # Save bytes BEFORE creating the row so the path is final.
    # Use the content hash as a temp id; the real document_id is set after the insert
    # but we keep a stable file name by reusing the document_id once known.
    async with pool.acquire() as conn:
        async with conn.transaction():
            doc = await document_repository.create_pending(
                conn,
                tenant_id=tenant_id,
                filename=filename,
                content_hash=content_hash,
                byte_size=len(data),
                storage_path="",  # placeholder, updated below
            )
            document_id: UUID = doc["id"]
            path = storage.save_bytes(
                settings.storage_dir, str(tenant_id), str(document_id), data
            )
            await conn.execute(
                "UPDATE documents SET storage_path=$2 WHERE id=$1", document_id, path
            )

    # Ingestion happens outside the create transaction so failures can be marked.
    try:
        pages = extract_pages_from_pdf(data)
        if not any(p.strip() for p in pages):
            raise IngestionError("PDF has no extractable text")

        chunks = chunk_pages(
            pages,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )
        if not chunks:
            raise IngestionError("Chunking produced no chunks")

        vectors = await embed_chunks(settings, [c.text for c in chunks])
        if len(vectors) != len(chunks):
            raise IngestionError("Embedding count mismatch")

        async with pool.acquire() as conn:
            async with conn.transaction():
                chunk_ids = await chunk_repository.bulk_insert_chunks(
                    conn, tenant_id, document_id, chunks
                )

        await _upsert_vectors(settings, tenant_id, document_id, chunks, chunk_ids, vectors)

        async with pool.acquire() as conn:
            updated = await document_repository.mark_indexed(
                conn, document_id, page_count=len(pages), chunk_count=len(chunks)
            )
        log.info(
            "document.indexed",
            document_id=str(document_id),
            pages=len(pages),
            chunks=len(chunks),
        )
        return updated, False

    except Exception as exc:  # noqa: BLE001
        async with pool.acquire() as conn:
            await document_repository.mark_failed(conn, document_id, str(exc))
        log.error("document.failed", document_id=str(document_id), error=str(exc))
        raise


async def _upsert_vectors(
    settings: Settings,
    tenant_id: UUID,
    document_id: UUID,
    chunks: list,
    chunk_ids: list[UUID],
    vectors: list[list[float]],
) -> None:
    client = qdrant.get_qdrant()
    points = [
        qm.PointStruct(
            id=str(chunk_id),
            vector=vec,
            payload={
                "tenant_id": str(tenant_id),
                "document_id": str(document_id),
                "page": chunk.page,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
            },
        )
        for chunk, chunk_id, vec in zip(chunks, chunk_ids, vectors, strict=True)
    ]
    await client.upsert(collection_name=settings.qdrant_collection, points=points)


async def list_for_tenant(tenant_id: UUID) -> list[dict]:
    pool = postgres.get_pool()
    async with pool.acquire() as conn:
        return await document_repository.list_documents(conn, tenant_id)


async def get_for_tenant(tenant_id: UUID, document_id: UUID) -> dict | None:
    pool = postgres.get_pool()
    async with pool.acquire() as conn:
        return await document_repository.get_document(conn, tenant_id, document_id)


async def delete_for_tenant(
    settings: Settings, tenant_id: UUID, document_id: UUID
) -> bool:
    pool = postgres.get_pool()
    async with pool.acquire() as conn:
        deleted = await document_repository.delete_document(conn, tenant_id, document_id)
    if deleted:
        client = qdrant.get_qdrant()
        await client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=qm.FilterSelector(
                filter=qm.Filter(
                    must=[
                        qm.FieldCondition(
                            key="document_id",
                            match=qm.MatchValue(value=str(document_id)),
                        ),
                        qm.FieldCondition(
                            key="tenant_id",
                            match=qm.MatchValue(value=str(tenant_id)),
                        ),
                    ]
                )
            ),
        )
    return deleted
