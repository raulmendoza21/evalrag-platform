"""Persistence for eval runs."""
from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import asyncpg


async def insert_run(
    conn: asyncpg.Connection,
    tenant_id: UUID,
    dataset_name: str,
    num_items: int,
    k: int,
    recall_at_k: float | None,
    mrr_at_k: float | None,
    faithfulness: float | None,
    answer_relevance: float | None,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    row = await conn.fetchrow(
        """
        INSERT INTO eval_runs (
            tenant_id, dataset_name, num_items, k,
            recall_at_k, mrr_at_k, faithfulness, answer_relevance, items
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb)
        RETURNING id, created_at
        """,
        tenant_id,
        dataset_name,
        num_items,
        k,
        recall_at_k,
        mrr_at_k,
        faithfulness,
        answer_relevance,
        json.dumps(items),
    )
    return dict(row)


async def list_runs(
    conn: asyncpg.Connection, tenant_id: UUID, limit: int = 20
) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        """
        SELECT id, dataset_name, num_items, k,
               recall_at_k, mrr_at_k, faithfulness, answer_relevance, created_at
          FROM eval_runs
         WHERE tenant_id = $1
         ORDER BY created_at DESC
         LIMIT $2
        """,
        tenant_id,
        limit,
    )
    return [dict(r) for r in rows]


async def get_run(
    conn: asyncpg.Connection, tenant_id: UUID, run_id: UUID
) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        "SELECT * FROM eval_runs WHERE tenant_id = $1 AND id = $2",
        tenant_id,
        run_id,
    )
    if row is None:
        return None
    d = dict(row)
    if isinstance(d.get("items"), str):
        d["items"] = json.loads(d["items"])
    return d
