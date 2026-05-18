-- 001_initial_schema.sql
-- Core schema for EvalRAG (multi-tenant).

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS tenants (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name         TEXT NOT NULL UNIQUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO tenants (name) VALUES ('default')
    ON CONFLICT (name) DO NOTHING;

CREATE TABLE IF NOT EXISTS documents (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    filename      TEXT NOT NULL,
    content_hash  TEXT NOT NULL,
    page_count    INTEGER NOT NULL DEFAULT 0,
    chunk_count   INTEGER NOT NULL DEFAULT 0,
    byte_size     INTEGER NOT NULL DEFAULT 0,
    status        TEXT NOT NULL DEFAULT 'pending', -- pending | indexed | failed
    error         TEXT,
    storage_path  TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    indexed_at    TIMESTAMPTZ,
    UNIQUE (tenant_id, content_hash)
);

CREATE INDEX IF NOT EXISTS idx_documents_tenant ON documents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);

CREATE TABLE IF NOT EXISTS chunks (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id   UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    page          INTEGER NOT NULL,
    chunk_index   INTEGER NOT NULL,
    text          TEXT NOT NULL,
    token_count   INTEGER NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_tenant   ON chunks(tenant_id);
-- BM25-style full-text search (used later in hybrid retrieval).
CREATE INDEX IF NOT EXISTS idx_chunks_text_fts ON chunks
    USING GIN (to_tsvector('simple', text));
