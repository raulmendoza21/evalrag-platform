"""LLM-as-judge: faithfulness + answer relevance in a single call.

We co-locate both judgments to amortise tokens and to give the judge the full
context at once. The judge model is the same as the chat model; in a stricter
setup you would use a larger model (e.g. gpt-4o or claude-sonnet) as the judge.
"""
from __future__ import annotations

import json

from app.config import Settings
from app.core.exceptions import EvalRAGError
from app.infrastructure.llm_client import complete_json
from app.services.retrieval_service import RetrievedChunk

JUDGE_SYSTEM = """You are a strict evaluator of a retrieval-augmented QA system.

Given a USER_QUESTION, the ANSWER produced by the system, and the CONTEXTS that were
shown to the system, score the ANSWER on two axes:

1. faithfulness — binary. 1 if every factual claim in the ANSWER is supported by the CONTEXTS, 0 otherwise. A refusal ("not enough information") with no claims counts as 1.
2. answer_relevance — integer 1-5. 5 = directly and completely addresses the question; 1 = off-topic or empty.

Respond with strict JSON:
{
  "faithfulness": 0 | 1,
  "answer_relevance": 1 | 2 | 3 | 4 | 5,
  "rationale": "one short sentence"
}
"""


def _format_contexts(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "(no contexts retrieved)"
    return "\n\n".join(
        f"[{i}] (page {c.page})\n{c.text.strip()}"
        for i, c in enumerate(chunks, start=1)
    )


async def judge_answer(
    settings: Settings,
    question: str,
    answer: str,
    contexts: list[RetrievedChunk],
) -> dict:
    user = (
        f"USER_QUESTION:\n{question.strip()}\n\n"
        f"ANSWER:\n{answer.strip() or '(empty)'}\n\n"
        f"CONTEXTS:\n{_format_contexts(contexts)}"
    )
    raw = await complete_json(
        model=settings.llm_model,
        system=JUDGE_SYSTEM,
        user=user,
        temperature=0.0,
    )
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise EvalRAGError(f"Judge returned invalid JSON: {exc}") from exc

    faith = payload.get("faithfulness")
    rel = payload.get("answer_relevance")
    try:
        faith_score = 1.0 if int(faith) == 1 else 0.0
    except (TypeError, ValueError):
        faith_score = 0.0
    try:
        rel_score = max(1, min(5, int(rel)))
    except (TypeError, ValueError):
        rel_score = 1
    return {
        "faithfulness": faith_score,
        "answer_relevance": rel_score,
        "rationale": str(payload.get("rationale") or "")[:500],
    }
