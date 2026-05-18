"""Pydantic schemas for documents."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    page_count: int
    chunk_count: int
    byte_size: int
    status: str
    error: str | None = None
    created_at: datetime
    indexed_at: datetime | None = None


class DocumentUploadResponse(BaseModel):
    document: DocumentOut
    deduplicated: bool = False
