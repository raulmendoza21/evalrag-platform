"""Shared FastAPI dependencies (tenant resolution, etc.)."""
from __future__ import annotations

from uuid import UUID

from fastapi import Header, HTTPException, status

from app.infrastructure import postgres
from app.repositories import document_repository


async def get_tenant_id(x_tenant: str | None = Header(default=None)) -> UUID:
    """Resolve the tenant from the X-Tenant header. Defaults to 'default' tenant for MVP."""
    pool = postgres.get_pool()
    async with pool.acquire() as conn:
        if x_tenant in (None, "", "default"):
            return await document_repository.get_default_tenant_id(conn)
        row = await conn.fetchrow("SELECT id FROM tenants WHERE name = $1", x_tenant)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown tenant '{x_tenant}'"
            )
        return row["id"]
