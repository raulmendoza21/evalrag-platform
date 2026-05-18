"""OpenAI chat completions client (separate from embeddings for clarity)."""
from __future__ import annotations

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import Settings
from app.core.exceptions import EvalRAGError


class LLMError(EvalRAGError):
    pass


_client: AsyncOpenAI | None = None


def init_llm_client(settings: Settings) -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key or "missing")
    return _client


def get_llm_client() -> AsyncOpenAI:
    if _client is None:
        raise RuntimeError("LLM client not initialised")
    return _client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
async def complete_json(
    model: str,
    system: str,
    user: str,
    temperature: float = 0.1,
) -> str:
    """Call the chat API with JSON-object response format. Returns the raw JSON string."""
    client = get_llm_client()
    try:
        resp = await client.chat.completions.create(
            model=model,
            temperature=temperature,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
    except Exception as exc:  # noqa: BLE001
        raise LLMError(str(exc)) from exc
    content = resp.choices[0].message.content or ""
    if not content.strip():
        raise LLMError("Empty completion from LLM")
    return content
