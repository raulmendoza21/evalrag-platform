-- Eval runs persistence. JSONB for per-item details keeps the schema flexible.
CREATE TABLE IF NOT EXISTS eval_runs (
    id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id        uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    dataset_name     text NOT NULL,
    num_items        int  NOT NULL,
    k                int  NOT NULL,
    recall_at_k      double precision,
    mrr_at_k         double precision,
    faithfulness     double precision,
    answer_relevance double precision,
    items            jsonb NOT NULL,
    created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_eval_runs_tenant_created
    ON eval_runs (tenant_id, created_at DESC);
