"""Schemas for /eval/*."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EvalRunRequest(BaseModel):
    dataset: str = Field(
        default="sample",
        description="Dataset name resolved to /datasets/<name>.jsonl inside the container.",
    )
    k: int = Field(default=5, ge=1, le=20)
    judge: bool = Field(default=True, description="Run LLM-as-judge faithfulness + relevance.")


class EvalItemOut(BaseModel):
    question: str
    answer: str
    expected_doc_filenames: list[str]
    retrieved_doc_filenames: list[str]
    cited_doc_filenames: list[str]
    recall_at_k: float | None
    reciprocal_rank: float | None
    faithfulness: float | None
    answer_relevance: int | None
    judge_rationale: str | None
    latency_ms: int


class EvalRunSummaryOut(BaseModel):
    id: UUID | None = None
    dataset_name: str
    num_items: int
    k: int
    recall_at_k: float | None
    mrr_at_k: float | None
    faithfulness: float | None
    answer_relevance: float | None
    created_at: datetime | None = None
    items: list[EvalItemOut] = []


class EvalRunListItem(BaseModel):
    id: UUID
    dataset_name: str
    num_items: int
    k: int
    recall_at_k: float | None
    mrr_at_k: float | None
    faithfulness: float | None
    answer_relevance: float | None
    created_at: datetime
