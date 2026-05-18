"""Grounded answer generation with mandatory citations."""
from __future__ import annotations

import json
from uuid import UUID

from app.config import Settings
from app.core.exceptions import EvalRAGError
from app.infrastructure.llm_client import complete_json
from app.services.retrieval_service import RetrievedChunk

SYSTEM_PROMPT = """You are a careful research assistant. You answer ONLY from the CONTEXTS provided by the user.

Rules:
1. If the contexts do not contain enough information to answer, set "answer" to "I don't have enough information in the provided documents to answer that." and return an empty citations list.
2. Every factual claim in your answer must be supported by at least one citation.
3. A citation refers to a context by its "id" (an integer shown in [brackets]). NEVER invent ids.
4. Keep the answer concise (3-6 sentences unless the question requires more).
5. Respond with valid JSON only, matching this schema:
   {
     "answer": "string",
     "citation_ids": [integer, integer, ...]
   }
"""


def _format_contexts(chunks: list[RetrievedChunk]) -> str:
    blocks: list[str] = []
    for idx, c in enumerate(chunks, start=1):
        blocks.append(
            f"[{idx}] (document_id={c.document_id}, page={c.page})\n{c.text.strip()}"
        )
    return "\n\n".join(blocks)


class GenerationResult(dict):
    """Typed dict-ish container with helper access."""


async def generate_grounded_answer(
    settings: Settings,
    query: str,
    chunks: list[RetrievedChunk],
) -> tuple[str, list[UUID]]:
    """Return (answer, list_of_cited_chunk_ids).

    If no chunks are provided, returns a polite refusal without calling the LLM.
    """
    if not chunks:
        return (
            "I don't have enough information in the provided documents to answer that.",
            [],
        )

    user_msg = (
        f"QUESTION:\n{query.strip()}\n\n"
        f"CONTEXTS:\n{_format_contexts(chunks)}"
    )
    raw = await complete_json(
        model=settings.llm_model,
        system=SYSTEM_PROMPT,
        user=user_msg,
        temperature=0.1,
    )

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise EvalRAGError(f"LLM returned invalid JSON: {exc}") from exc

    answer = str(payload.get("answer") or "").strip()
    raw_ids = payload.get("citation_ids") or []
    cited: list[UUID] = []
    for cid in raw_ids:
        try:
            idx = int(cid)
        except (TypeError, ValueError):
            continue
        if 1 <= idx <= len(chunks):
            cited.append(chunks[idx - 1].chunk_id)
    return answer, cited
