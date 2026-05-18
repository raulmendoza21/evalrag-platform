.PHONY: up down logs migrate seed test eval injection-test fmt lint

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f api

migrate:
	docker compose exec api python -m app.scripts.migrate

seed:
	docker compose exec api python -m app.scripts.seed_sample_docs

test:
	docker compose exec api pytest -q

eval:
	docker compose exec api python -m app.scripts.run_evaluation

injection-test:
	docker compose exec api pytest -q app/tests/test_guardrails.py

fmt:
	docker compose exec api ruff format .

lint:
	docker compose exec api ruff check .
