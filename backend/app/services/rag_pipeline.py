"""RAG pipeline orchestrator: query -> retrieve -> generate."""
from __future__ import annotations

import time
from dataclasses import dataclass
from uuid import UUID

from app.config import Settings
from app.core.logging import get_logger
from app.services.generation_service import generate_grounded_answer
from app.services.retrieval_service import RetrievedChunk, hybrid_search

log = get_logger(__name__)


@dataclass
class ChatResult:
    answer: str
    citations: list[UUID]
    retrieved: list[RetrievedChunk]
    latency_ms: int


async def answer_question(
    settings: Settings,
    tenant_id: UUID,
    query: str,
    top_k: int = 5,
) -> ChatResult:
    started = time.perf_counter()

    retrieved = await hybrid_search(
        settings=settings,
        tenant_id=tenant_id,
        query=query,
        k_final=top_k,
    )

    answer, citations = await generate_grounded_answer(
        settings=settings,
        query=query,
        chunks=retrieved,
    )

    latency_ms = int((time.perf_counter() - started) * 1000)
    log.info(
        "chat.answered",
        tenant=str(tenant_id),
        retrieved=len(retrieved),
        cited=len(citations),
        latency_ms=latency_ms,
    )
    return ChatResult(
        answer=answer,
        citations=citations,
        retrieved=retrieved,
        latency_ms=latency_ms,
    )
