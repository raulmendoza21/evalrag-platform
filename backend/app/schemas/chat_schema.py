"""Schemas for /chat."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class CitationOut(BaseModel):
    chunk_id: UUID
    document_id: UUID
    page: int


class RetrievedChunkOut(BaseModel):
    chunk_id: UUID
    document_id: UUID
    page: int
    chunk_index: int
    score: float
    sources: list[str]
    text: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationOut]
    retrieved: list[RetrievedChunkOut]
    latency_ms: int
