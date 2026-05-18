# Architecture

## Overview

EvalRAG is a 4-layer system:

1. **Edge** — React frontend served by Vite (in dev) or static files behind Caddy (in prod).
2. **API** — FastAPI app exposing REST + SSE endpoints.
3. **Pipelines** — ingestion pipeline and RAG pipeline, both implemented as composable services.
4. **Data** — PostgreSQL (relational), Qdrant (vectors), Redis (cache), Langfuse (traces).

## Multi-tenancy

Every row and every vector carries a `tenant_id`. Every query is filtered by `tenant_id` at the SQL and Qdrant level. The same JWT carries the tenant claim. There is no cross-tenant data path.

## Ingestion pipeline

```
upload → extract → clean → chunk → embed → upsert(qdrant) + insert(postgres) → emit ready event
```

Idempotency: `(tenant_id, document_hash)` is unique. Re-uploading the same file is a no-op.

## RAG pipeline

See [`rag_pipeline.md`](rag_pipeline.md).

## Failure modes & fallbacks

| Failure | Behaviour |
|---|---|
| LLM provider down | Fall back to `LLM_FALLBACK_MODEL`, then return 503 with a friendly message |
| Reranker down | Skip rerank, log a warning, return top-k vector results |
| Qdrant down | Return 503 (RAG is meaningless without retrieval) |
| Redis down | Disable semantic cache, keep serving |
| Langfuse down | Trace asynchronously, drop on failure (never blocks the request) |

## Deployment

Designed for a single Hetzner CX22 VPS with Caddy in front. See [`deployment.md`](deployment.md).
