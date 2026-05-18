"""Eval API — kick off a run, list past runs, fetch a single run."""
from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.core.exceptions import EvalRAGError
from app.dependencies import get_tenant_id
from app.eval.runner import run_eval
from app.infrastructure import postgres
from app.repositories import eval_repository
from app.schemas.eval_schema import (
    EvalItemOut,
    EvalRunListItem,
    EvalRunRequest,
    EvalRunSummaryOut,
)

router = APIRouter(prefix="/eval", tags=["eval"])

DATASETS_ROOT = Path("/datasets")


def _resolve_dataset_path(name: str) -> Path:
    # Prevent path traversal — only flat filenames allowed.
    safe = Path(name).name
    if not safe or safe.startswith("."):
        raise HTTPException(400, "Invalid dataset name")
    candidate = DATASETS_ROOT / f"{safe}.jsonl"
    if not candidate.exists():
        raise HTTPException(404, f"Dataset not found: {candidate}")
    return candidate


@router.post("/run", response_model=EvalRunSummaryOut)
async def run(
    body: EvalRunRequest,
    settings: Settings = Depends(get_settings),
    tenant_id: UUID = Depends(get_tenant_id),
) -> EvalRunSummaryOut:
    path = _resolve_dataset_path(body.dataset)
    try:
        summary = await run_eval(
            settings=settings,
            tenant_id=tenant_id,
            dataset_path=path,
            k=body.k,
            run_judge=body.judge,
        )
    except EvalRAGError as exc:
        raise HTTPException(502, str(exc)) from exc

    items_json = [EvalItemOut(**item.__dict__).model_dump(mode="json") for item in summary.items]

    pool = postgres.get_pool()
    async with pool.acquire() as conn:
        meta = await eval_repository.insert_run(
            conn=conn,
            tenant_id=tenant_id,
            dataset_name=summary.dataset_name,
            num_items=summary.num_items,
            k=summary.k,
            recall_at_k=summary.recall_at_k,
            mrr_at_k=summary.mrr_at_k,
            faithfulness=summary.faithfulness,
            answer_relevance=summary.answer_relevance,
            items=items_json,
        )

    return EvalRunSummaryOut(
        id=meta["id"],
        created_at=meta["created_at"],
        dataset_name=summary.dataset_name,
        num_items=summary.num_items,
        k=summary.k,
        recall_at_k=summary.recall_at_k,
        mrr_at_k=summary.mrr_at_k,
        faithfulness=summary.faithfulness,
        answer_relevance=summary.answer_relevance,
        items=[EvalItemOut(**item.__dict__) for item in summary.items],
    )


@router.get("/runs", response_model=list[EvalRunListItem])
async def list_runs(
    tenant_id: UUID = Depends(get_tenant_id),
) -> list[EvalRunListItem]:
    pool = postgres.get_pool()
    async with pool.acquire() as conn:
        rows = await eval_repository.list_runs(conn, tenant_id)
    return [EvalRunListItem(**r) for r in rows]


@router.get("/runs/{run_id}", response_model=EvalRunSummaryOut)
async def get_run(
    run_id: UUID,
    tenant_id: UUID = Depends(get_tenant_id),
) -> EvalRunSummaryOut:
    pool = postgres.get_pool()
    async with pool.acquire() as conn:
        row = await eval_repository.get_run(conn, tenant_id, run_id)
    if row is None:
        raise HTTPException(404, "Run not found")
    return EvalRunSummaryOut(
        id=row["id"],
        created_at=row["created_at"],
        dataset_name=row["dataset_name"],
        num_items=row["num_items"],
        k=row["k"],
        recall_at_k=row["recall_at_k"],
        mrr_at_k=row["mrr_at_k"],
        faithfulness=row["faithfulness"],
        answer_relevance=row["answer_relevance"],
        items=[EvalItemOut(**it) for it in row["items"]],
    )
