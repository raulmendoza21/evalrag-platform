"""Health endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.infrastructure import postgres, qdrant

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/health/ready")
async def ready() -> dict:
    """Deep health check: confirms Postgres + Qdrant are reachable."""
    checks: dict[str, str] = {}
    try:
        pool = postgres.get_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        checks["postgres"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["postgres"] = f"error: {exc}"

    try:
        client = qdrant.get_qdrant()
        await client.get_collections()
        checks["qdrant"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["qdrant"] = f"error: {exc}"

    status_ = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status_, "checks": checks}
