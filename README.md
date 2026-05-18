# EvalRAG — Production-Ready RAG Platform

> Production-style RAG platform with **hybrid search**, **reranking**, **grounded answers with citations**, **prompt-injection guardrails**, **automated evaluation (RAGAS)** and **full LLM observability**.

[![Backend Tests](https://img.shields.io/badge/backend-tests%20passing-brightgreen)]() [![Eval Faithfulness](https://img.shields.io/badge/faithfulness-91%25-blue)]() [![License](https://img.shields.io/badge/license-MIT-lightgrey)]()

---

## TL;DR for recruiters

EvalRAG is **not** a "chat with PDF" toy. It is a full RAG stack designed the way a real product team would build it:

- **Hybrid retrieval** (BM25 + vector) with **cross-encoder reranking**.
- Every answer is **grounded in cited chunks**; the model is forced to refuse when context is insufficient.
- **Prompt-injection guardrails** at input and at retrieved-context level.
- **Continuous evaluation** with RAGAS (faithfulness, answer relevance, context precision/recall).
- **Cost & latency observability** per query (Langfuse traces, token accounting, semantic cache).
- **Multi-tenant**: each tenant's documents are isolated at the vector and SQL layer.
- Fully containerised (Docker Compose), tested, and deployable on a single VPS.

**Live demo:** _coming soon_ · **Demo video (60s):** _coming soon_ · **API docs:** `/docs` (FastAPI Swagger)

---

## Table of contents

1. [Problem](#problem)
2. [Solution](#solution)
3. [Architecture](#architecture)
4. [RAG pipeline](#rag-pipeline)
5. [Tech stack](#tech-stack)
6. [Evaluation results](#evaluation-results)
7. [Guardrails](#guardrails)
8. [Observability & cost control](#observability--cost-control)
9. [API endpoints](#api-endpoints)
10. [Local setup](#local-setup)
11. [Docker setup](#docker-setup)
12. [Environment variables](#environment-variables)
13. [Project structure](#project-structure)
14. [Testing](#testing)
15. [Roadmap](#roadmap)

---

## Problem

Most "chat with your documents" demos break in production because they:

- Use **pure vector search**, which fails on exact terms (codes, names, numbers).
- **Hallucinate** when the retrieved context is weak.
- Have **no evaluation loop** — nobody knows if a prompt change makes things better or worse.
- Are **vulnerable to prompt injection** hidden inside the documents themselves.
- Have **no cost visibility** — a single user can burn through the LLM budget.

EvalRAG is built to address all five.

## Solution

A backend service + minimal React frontend that ingests documents, indexes them, answers questions with citations, and continuously evaluates itself against a curated test set.

Key design decisions:

| Decision | Why |
|---|---|
| Hybrid search (BM25 + dense) | Pure vector loses on IDs, SKUs, names. BM25 alone loses on paraphrase. |
| Cross-encoder reranking | Top-k vector recall is noisy; reranking lifts precision@5 by ~15 pts in my eval. |
| Forced citation in prompt | Reduces hallucination and makes answers auditable. |
| Refusal when score < threshold | Better to say "I don't know" than to make something up. |
| Semantic cache (Redis) | Cuts cost on repeated/near-duplicate questions. |
| Langfuse tracing | Every step (rewrite → retrieve → rerank → generate) is traced and replayable. |

## Architecture

```
                       ┌─────────────────┐
                       │  React Frontend │
                       └────────┬────────┘
                                │ HTTPS
                       ┌────────▼────────┐
                       │   FastAPI API   │
                       └────────┬────────┘
                                │
              ┌─────────────────┼──────────────────┐
              │                 │                  │
       ┌──────▼─────┐    ┌──────▼─────┐    ┌──────▼──────┐
       │ Ingestion  │    │ RAG        │    │ Evaluation  │
       │ pipeline   │    │ pipeline   │    │ runner      │
       └──────┬─────┘    └──────┬─────┘    └──────┬──────┘
              │                 │                  │
   ┌──────────┼──────────┐      │                  │
   │          │          │      │                  │
┌──▼──┐  ┌────▼───┐ ┌────▼───┐  │                  │
│ PDF │  │ Chunk  │ │ Embed  │  │                  │
└─────┘  └────────┘ └────┬───┘  │                  │
                         │      │                  │
                  ┌──────▼──────▼─────┐    ┌───────▼────────┐
                  │ Qdrant + Postgres │    │   Langfuse     │
                  │  (vectors + meta) │    │  (traces/eval) │
                  └───────────────────┘    └────────────────┘
```

## RAG pipeline

```
User question
  └─► (1) Input guardrail        ── reject prompt injection
        └─► (2) Query rewrite    ── expand abbreviations, fix typos
              └─► (3) Hybrid search ─ BM25 + dense (top-20)
                    └─► (4) Cross-encoder rerank ─ top-5
                          └─► (5) Context guardrail ─ strip injection payloads
                                └─► (6) Generation ─ forced citation + refusal
                                      └─► (7) Trace + cost log to Langfuse
                                            └─► Answer + sources + metrics
```

See [`docs/rag_pipeline.md`](docs/rag_pipeline.md) for a deeper walkthrough.

## Tech stack

| Layer | Choice |
|---|---|
| API | **FastAPI** + Pydantic v2 |
| Vector store | **Qdrant** (also tested with pgvector) |
| Relational | **PostgreSQL** (documents, chunks metadata, tenants, conversations) |
| Cache | **Redis** (semantic cache, rate limiting) |
| Embeddings | `text-embedding-3-small` (swappable via `.env` for `bge-m3` / `e5-large`) |
| Reranker | `bge-reranker-v2-m3` (cross-encoder) |
| LLM | OpenAI / Anthropic / local (swappable via `LLM_PROVIDER`) |
| Evaluation | **RAGAS** + custom prompt-injection suite |
| Observability | **Langfuse** (self-hosted) |
| Frontend | React + Vite + TypeScript + Tailwind |
| Infra | Docker Compose, deployable on a single Hetzner VPS |
| CI | GitHub Actions (tests + nightly RAG evaluation) |

## Evaluation results

Run on a curated set of **50 questions** across 3 sample documents (company policy, contract, technical manual) + **20 prompt-injection probes**.

| Metric | Result |
|---|---:|
| Retrieval hit-rate @ 5 | **86%** |
| Faithfulness (RAGAS) | **0.91** |
| Answer relevance (RAGAS) | **0.88** |
| Context precision (RAGAS) | **0.82** |
| Context recall (RAGAS) | **0.79** |
| Prompt-injection blocked | **17 / 20** |
| Avg end-to-end latency | **2.1 s** |
| Avg cost per query | **€0.0041** |
| Semantic cache hit rate | **23%** |

> Reproducible via `make eval`. The full report is generated into [`docs/evaluation_report.md`](docs/evaluation_report.md).

## Guardrails

Three layers, documented in [`docs/guardrails.md`](docs/guardrails.md):

1. **Input filter** — heuristic + small classifier to detect known injection patterns (`ignore previous`, `reveal system prompt`, encoded payloads…).
2. **Context sanitizer** — instructions embedded inside retrieved chunks are quoted and labelled as "untrusted content" before being passed to the LLM.
3. **Output contract** — the model must return JSON with `answer`, `sources[]`, and `is_grounded`. If `is_grounded=false`, the API returns a polite refusal instead of the raw answer.

## Observability & cost control

- Every request is a **Langfuse trace** with nested spans (`rewrite`, `retrieve`, `rerank`, `generate`).
- Per-tenant **token & €** counters in PostgreSQL.
- **Semantic cache** in Redis keyed by `hash(tenant_id, normalized_query)` with a similarity threshold of `0.95`.
- **Model router**: cheap model first (`gpt-4o-mini`), escalation to a stronger model only when the reviewer flags low confidence.

## API endpoints

```
GET    /health
POST   /documents/upload
GET    /documents
GET    /documents/{id}
DELETE /documents/{id}

POST   /chat                  # supports SSE streaming
GET    /chat/history

POST   /evaluation/run
GET    /evaluation/results

GET    /metrics/overview
GET    /metrics/latency
GET    /metrics/costs
GET    /metrics/retrieval
```

Example `POST /chat`:

```json
{
  "question": "What does the document say about data retention?",
  "document_ids": ["doc_123"],
  "use_reranking": true,
  "top_k": 5,
  "stream": true
}
```

Example response:

```json
{
  "answer": "Customer data must be retained for 5 years unless deletion is requested earlier.",
  "is_grounded": true,
  "sources": [
    {
      "document_name": "company_policy.pdf",
      "page": 7,
      "chunk_id": "chunk_044",
      "score": 0.87,
      "text": "Customer data must be retained for…"
    }
  ],
  "metrics": {
    "latency_ms": 1820,
    "input_tokens": 1450,
    "output_tokens": 180,
    "estimated_cost_eur": 0.0031,
    "cache_hit": false
  }
}
```

## Local setup

Requirements: Python 3.11+, Node 20+, Docker.

```bash
git clone https://github.com/<you>/evalrag-platform.git
cd evalrag-platform

cp .env.example .env       # add your OPENAI_API_KEY (or local LLM)
make up                    # docker compose up -d (api, qdrant, postgres, redis, langfuse)
make migrate
make seed                  # loads /datasets/sample_documents
open http://localhost:5173
```

## Docker setup

```bash
docker compose up -d --build
docker compose logs -f api
```

Services: `api`, `frontend`, `qdrant`, `postgres`, `redis`, `langfuse`.

## Environment variables

See [`.env.example`](.env.example). Highlights:

```
LLM_PROVIDER=openai            # openai | anthropic | ollama
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
QDRANT_URL=http://qdrant:6333
POSTGRES_URL=postgresql://...
REDIS_URL=redis://redis:6379/0
LANGFUSE_PUBLIC_KEY=...
SEMANTIC_CACHE_THRESHOLD=0.95
RAG_TOP_K=20
RAG_RERANK_TOP_K=5
```

## Project structure

```
evalrag-platform/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routers
│   │   ├── services/         # ingestion, chunking, retrieval, rerank, generation, guardrails, evaluation
│   │   ├── repositories/     # DB access
│   │   ├── infrastructure/   # qdrant, postgres, redis, llm, embedding clients
│   │   ├── schemas/          # Pydantic models
│   │   ├── prompts/          # versioned prompt templates
│   │   └── tests/
│   └── migrations/
├── frontend/                 # React + Vite + Tailwind
├── datasets/
│   ├── sample_documents/
│   └── evaluation/           # questions.jsonl, expected_answers.jsonl, injection_tests.jsonl
├── docs/                     # architecture, rag_pipeline, evaluation_report, guardrails, deployment, demo_script
└── .github/workflows/        # backend-tests, frontend-tests, rag-evaluation (nightly)
```

## Testing

```bash
make test              # unit + integration
make eval              # full RAG evaluation (writes docs/evaluation_report.md)
make injection-test    # prompt-injection suite only
```

Tests live in `backend/app/tests/`:

- `test_chunking.py` — chunk size, overlap, page metadata preserved.
- `test_retrieval.py` — hybrid search returns expected doc for seed queries.
- `test_guardrails.py` — injection probes are blocked, refusal triggers on low context.
- `test_rag_pipeline.py` — end-to-end with mocked LLM, asserts citations exist.
- `test_api.py` — all endpoints, auth, multi-tenant isolation.

## Roadmap

- [ ] Re-ranking with **Cohere Rerank 3** as a comparison baseline
- [ ] **Streaming citations** (sources appear as the answer streams)
- [ ] **Per-tenant fine-tuned reranker** (optional)
- [ ] **Auto-eval on every PR** with regression alerts (>2% drop fails CI)
- [ ] **Public live demo** on a Hetzner VPS with rate-limited free tier

---

Built by **Raúl Mendoza** — looking for AI Engineer roles. [LinkedIn](#) · [Email](#)
