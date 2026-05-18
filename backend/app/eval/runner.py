"""Eval run orchestrator: dataset -> rag pipeline -> metrics + judge -> summary."""
from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from app.config import Settings
from app.core.logging import get_logger
from app.eval.dataset import EvalItem, load_dataset
from app.eval.judge import judge_answer
from app.eval.metrics import mean, recall_at_k, reciprocal_rank
from app.infrastructure import postgres
from app.repositories import document_repository
from app.services import rag_pipeline

log = get_logger(__name__)


@dataclass
class EvalItemResult:
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


@dataclass
class EvalRunSummary:
    dataset_name: str
    num_items: int
    k: int
    recall_at_k: float | None
    mrr_at_k: float | None
    faithfulness: float | None
    answer_relevance: float | None
    items: list[EvalItemResult]

    def to_jsonable(self) -> dict[str, Any]:
        d = asdict(self)
        return d


async def _filenames_for_doc_ids(
    tenant_id: UUID, doc_ids: list[UUID]
) -> dict[UUID, str]:
    if not doc_ids:
        return {}
    pool = postgres.get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, filename FROM documents
             WHERE tenant_id = $1 AND id = ANY($2::uuid[])
            """,
            tenant_id,
            doc_ids,
        )
    return {r["id"]: r["filename"] for r in rows}


async def _process_item(
    settings: Settings,
    tenant_id: UUID,
    item: EvalItem,
    k: int,
    run_judge: bool,
) -> EvalItemResult:
    chat = await rag_pipeline.answer_question(
        settings=settings,
        tenant_id=tenant_id,
        query=item.question,
        top_k=k,
    )

    # Map document_ids → filenames for retrieval grading
    cited_ids_set = set(chat.citations)
    retrieved_doc_ids = list({c.document_id for c in chat.retrieved})
    id_to_name = await _filenames_for_doc_ids(tenant_id, retrieved_doc_ids)
    retrieved_filenames_in_order: list[str] = []
    seen: set[str] = set()
    for c in chat.retrieved:
        name = id_to_name.get(c.document_id)
        if name and name not in seen:
            retrieved_filenames_in_order.append(name)
            seen.add(name)
    cited_filenames = sorted(
        {id_to_name[c.document_id] for c in chat.retrieved if c.chunk_id in cited_ids_set and c.document_id in id_to_name}
    )

    if item.has_retrieval_label:
        rec = recall_at_k(retrieved_filenames_in_order, item.expected_doc_filenames, k)
        rr = reciprocal_rank(retrieved_filenames_in_order, item.expected_doc_filenames)
    else:
        rec = None
        rr = None

    faith: float | None = None
    rel: int | None = None
    rationale: str | None = None
    if run_judge:
        try:
            verdict = await judge_answer(
                settings=settings,
                question=item.question,
                answer=chat.answer,
                contexts=chat.retrieved,
            )
            faith = verdict["faithfulness"]
            rel = verdict["answer_relevance"]
            rationale = verdict["rationale"]
        except Exception as exc:  # noqa: BLE001
            log.warning("eval.judge_failed", error=str(exc))

    return EvalItemResult(
        question=item.question,
        answer=chat.answer,
        expected_doc_filenames=list(item.expected_doc_filenames),
        retrieved_doc_filenames=retrieved_filenames_in_order,
        cited_doc_filenames=cited_filenames,
        recall_at_k=rec,
        reciprocal_rank=rr,
        faithfulness=faith,
        answer_relevance=rel,
        judge_rationale=rationale,
        latency_ms=chat.latency_ms,
    )


async def run_eval(
    settings: Settings,
    tenant_id: UUID,
    dataset_path: str | Path,
    k: int = 5,
    run_judge: bool = True,
    concurrency: int = 2,
) -> EvalRunSummary:
    items = load_dataset(dataset_path)
    log.info("eval.start", dataset=str(dataset_path), n=len(items), k=k, judge=run_judge)

    sem = asyncio.Semaphore(concurrency)

    async def _bounded(it: EvalItem) -> EvalItemResult:
        async with sem:
            return await _process_item(settings, tenant_id, it, k, run_judge)

    results = await asyncio.gather(*(_bounded(it) for it in items))

    recall_vals = [r.recall_at_k for r in results if r.recall_at_k is not None]
    rr_vals = [r.reciprocal_rank for r in results if r.reciprocal_rank is not None]
    faith_vals = [r.faithfulness for r in results if r.faithfulness is not None]
    rel_vals = [float(r.answer_relevance) for r in results if r.answer_relevance is not None]

    summary = EvalRunSummary(
        dataset_name=Path(dataset_path).stem,
        num_items=len(items),
        k=k,
        recall_at_k=mean(recall_vals),
        mrr_at_k=mean(rr_vals),
        faithfulness=mean(faith_vals),
        answer_relevance=mean(rel_vals),
        items=results,
    )
    log.info(
        "eval.done",
        recall=summary.recall_at_k,
        mrr=summary.mrr_at_k,
        faith=summary.faithfulness,
        rel=summary.answer_relevance,
    )
    return summary
