"""Apply SQL migrations in lexicographic order."""
from __future__ import annotations

import asyncio
from pathlib import Path

import asyncpg

from app.config import get_settings

MIGRATIONS_DIR = Path("/app/migrations")


async def _ensure_table(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            name TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


async def _applied(conn: asyncpg.Connection) -> set[str]:
    rows = await conn.fetch("SELECT name FROM schema_migrations")
    return {r["name"] for r in rows}


async def run() -> None:
    settings = get_settings()
    conn = await asyncpg.connect(settings.postgres_url)
    try:
        await _ensure_table(conn)
        already = await _applied(conn)
        files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for f in files:
            if f.name in already:
                print(f"[skip] {f.name}")
                continue
            print(f"[apply] {f.name}")
            sql = f.read_text(encoding="utf-8")
            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO schema_migrations (name) VALUES ($1)", f.name
                )
        print("[done] migrations applied")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run())
