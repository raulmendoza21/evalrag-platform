"""Recursive character chunking that preserves page metadata."""
from __future__ import annotations

from dataclasses import dataclass

import tiktoken

_ENCODER = tiktoken.get_encoding("cl100k_base")
_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@dataclass(frozen=True)
class Chunk:
    page: int
    chunk_index: int
    text: str
    token_count: int


def chunk_pages(
    pages: list[str],
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> list[Chunk]:
    """Chunk each page independently so chunk → page mapping is preserved."""
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be < chunk_size")

    out: list[Chunk] = []
    global_index = 0
    for page_idx, page_text in enumerate(pages, start=1):
        if not page_text.strip():
            continue
        for piece in _recursive_split(page_text, chunk_size, chunk_overlap):
            piece = piece.strip()
            if not piece:
                continue
            out.append(
                Chunk(
                    page=page_idx,
                    chunk_index=global_index,
                    text=piece,
                    token_count=_count_tokens(piece),
                )
            )
            global_index += 1
    return out


def _recursive_split(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    for sep in _SEPARATORS:
        if sep == "":
            return _hard_split(text, chunk_size, chunk_overlap)
        parts = text.split(sep)
        if len(parts) == 1:
            continue
        return _merge_parts(parts, sep, chunk_size, chunk_overlap)
    return [text]


def _merge_parts(parts: list[str], sep: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    chunks: list[str] = []
    buf = ""
    for part in parts:
        candidate = (buf + sep + part) if buf else part
        if len(candidate) <= chunk_size:
            buf = candidate
            continue
        if buf:
            chunks.append(buf)
            buf = _tail(buf, chunk_overlap) + sep + part if chunk_overlap else part
        else:
            chunks.extend(_hard_split(part, chunk_size, chunk_overlap))
            buf = ""
        # If buf grew too large after carrying overlap, hard split it.
        if len(buf) > chunk_size:
            chunks.extend(_hard_split(buf, chunk_size, chunk_overlap))
            buf = ""
    if buf:
        chunks.append(buf)
    return chunks


def _hard_split(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    step = max(1, chunk_size - chunk_overlap)
    return [text[i : i + chunk_size] for i in range(0, len(text), step)]


def _tail(text: str, n: int) -> str:
    return text[-n:] if n > 0 and len(text) > n else text


def _count_tokens(text: str) -> int:
    return len(_ENCODER.encode(text))
