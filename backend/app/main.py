"""FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_chat, routes_documents, routes_eval, routes_health
from app.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.infrastructure import embedding_client, llm_client, postgres, qdrant


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    log = get_logger("startup")
    settings = get_settings()

    Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)

    await postgres.init_pool(settings)
    await qdrant.init_qdrant(settings)
    embedding_client.init_embedding_client(settings)
    llm_client.init_llm_client(settings)
    log.info("startup.complete", env=settings.app_env)

    try:
        yield
    finally:
        await postgres.close_pool()
        await qdrant.close_qdrant()


def create_app() -> FastAPI:
    app = FastAPI(
        title="EvalRAG API",
        version="0.1.0",
        description="Production-ready RAG platform.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(routes_health.router)
    app.include_router(routes_chat.router)
    app.include_router(routes_documents.router)
    app.include_router(routes_eval.router)
    return app


app = create_app()
