"""Unit tests for the chunking service."""
from __future__ import annotations

import pytest

from app.services.chunking_service import chunk_pages


def test_empty_pages_returns_no_chunks() -> None:
    assert chunk_pages([], chunk_size=100, chunk_overlap=10) == []
    assert chunk_pages(["", "   ", "\n\n"], chunk_size=100, chunk_overlap=10) == []


def test_short_page_produces_single_chunk() -> None:
    chunks = chunk_pages(["Hello world."], chunk_size=100, chunk_overlap=10)
    assert len(chunks) == 1
    assert chunks[0].page == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].text == "Hello world."
    assert chunks[0].token_count > 0


def test_chunks_respect_max_size() -> None:
    long_text = ("Lorem ipsum dolor sit amet. " * 200).strip()
    chunks = chunk_pages([long_text], chunk_size=200, chunk_overlap=40)
    assert len(chunks) > 1
    for c in chunks:
        # Allow small overshoot only on the very last hard-split fragment.
        assert len(c.text) <= 240, f"chunk too large: {len(c.text)}"


def test_chunks_preserve_page_metadata() -> None:
    pages = [
        "Page one content. " * 50,
        "Page two content. " * 50,
        "Page three content. " * 50,
    ]
    chunks = chunk_pages(pages, chunk_size=200, chunk_overlap=40)
    pages_seen = {c.page for c in chunks}
    assert pages_seen == {1, 2, 3}


def test_chunk_indexes_are_unique_and_monotonic() -> None:
    pages = ["A" * 1000, "B" * 1000]
    chunks = chunk_pages(pages, chunk_size=200, chunk_overlap=40)
    indexes = [c.chunk_index for c in chunks]
    assert indexes == sorted(indexes)
    assert len(set(indexes)) == len(indexes)


def test_overlap_must_be_less_than_size() -> None:
    with pytest.raises(ValueError):
        chunk_pages(["x"], chunk_size=100, chunk_overlap=100)
