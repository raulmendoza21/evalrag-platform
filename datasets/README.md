# Eval datasets

Format: one JSON object per line (JSONL). Required key: `question`.

Optional keys:

- `expected_doc_filenames` — list of strings. When provided, the runner computes **recall@k** and **MRR** by matching the *filenames* of the documents whose chunks were retrieved against this expected list. Filenames must match what you uploaded (case-sensitive).
- `reference_answer` — reserved for a future correctness judge. Not used today.

Example item with retrieval labels:

```json
{"question": "What was Q3 revenue?", "expected_doc_filenames": ["acme-10q-q3.pdf"], "reference_answer": "Q3 revenue was $4.2M."}
```

## Provided datasets

- `sample.jsonl` — 5 generic questions that work on any uploaded corpus. No retrieval labels (recall@k / MRR will be `null`); only LLM-as-judge metrics (faithfulness, answer_relevance) are computed.

## Running an eval

```bash
curl -X POST http://localhost:8000/eval/run \
  -H "Content-Type: application/json" \
  -d '{"dataset":"sample","k":5,"judge":true}'
```

Or from the React UI: Eval panel → pick dataset → Run.

Dataset files must live under `./datasets/` on the host. Docker compose mounts that
directory read-only at `/datasets` inside the api container.
