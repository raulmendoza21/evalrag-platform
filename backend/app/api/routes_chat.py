"""Chat API — grounded answers with citations."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.core.exceptions import EvalRAGError
from app.dependencies import get_tenant_id
from app.schemas.chat_schema import (
    ChatRequest,
    ChatResponse,
    CitationOut,
    RetrievedChunkOut,
)
from app.services import rag_pipeline

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    settings: Settings = Depends(get_settings),
    tenant_id: UUID = Depends(get_tenant_id),
) -> ChatResponse:
    try:
        result = await rag_pipeline.answer_question(
            settings=settings,
            tenant_id=tenant_id,
            query=body.query,
            top_k=body.top_k,
        )
    except EvalRAGError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    cited_ids = set(result.citations)
    citations = [
        CitationOut(chunk_id=c.chunk_id, document_id=c.document_id, page=c.page)
        for c in result.retrieved
        if c.chunk_id in cited_ids
    ]
    retrieved = [
        RetrievedChunkOut(
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            page=c.page,
            chunk_index=c.chunk_index,
            score=c.score,
            sources=list(c.sources),
            text=c.text,
        )
        for c in result.retrieved
    ]
    return ChatResponse(
        answer=result.answer,
        citations=citations,
        retrieved=retrieved,
        latency_ms=result.latency_ms,
    )
