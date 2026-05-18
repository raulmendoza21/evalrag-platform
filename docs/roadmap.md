# Roadmap

## v0.1 — MVP
- [x] Project skeleton, Docker Compose, READMEs
- [ ] Upload + ingestion + chunking + embedding
- [ ] Basic `/chat` with vector retrieval and citations
- [ ] Minimal frontend (Documents + Chat)

## v0.2 — Production feel
- [ ] Hybrid search (BM25 + dense) with RRF
- [ ] Cross-encoder reranking
- [ ] SSE streaming responses
- [ ] Semantic cache (Redis)
- [ ] Multi-tenant isolation + JWT auth

## v0.3 — Guardrails & eval
- [ ] Input + context guardrails
- [ ] RAGAS evaluation pipeline + nightly CI job
- [ ] Prompt-injection test suite (20 probes)
- [ ] Metrics dashboard

## v0.4 — Polish
- [ ] Live demo on Hetzner with rate-limited free tier
- [ ] 60-second Loom demo video
- [ ] Blog post: _"Why hybrid search beat my vector-only baseline by 12 points"_
- [ ] Per-PR eval regression check (>2% drop fails CI)
