# Deployment

## Single VPS (Hetzner CX22, ~€5/month)

1. Provision Ubuntu 24.04, install Docker.
2. Clone repo, copy `.env`.
3. `docker compose up -d --build`.
4. Put Caddy in front for HTTPS:

```
evalrag.example.com {
    reverse_proxy api:8000
    handle_path /app/* {
        reverse_proxy frontend:5173
    }
}
```

## Backups

- Postgres: nightly `pg_dump` to S3-compatible storage.
- Qdrant: snapshot endpoint + cron.
- Documents: original files stored in `storage/` (mounted volume), backed up via `restic`.

## Monitoring

- Langfuse for LLM traces.
- Optional: Prometheus + Grafana dashboards (latency, cost, cache hit-rate).
- Healthcheck `/health` polled every 30 s.
