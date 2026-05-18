"""Pure-logic retrieval metrics. No I/O — trivially unit-testable."""
from __future__ import annotations

from collections.abc import Iterable


def recall_at_k(retrieved: Iterable[str], expected: Iterable[str], k: int) -> float:
    """Binary recall: 1.0 if any expected item appears in the top-k retrieved list, else 0.0.

    This is the standard "hit rate at k" used in IR papers when there is at least
    one relevant document per query.
    """
    if k <= 0:
        return 0.0
    expected_set = set(expected)
    if not expected_set:
        return 0.0
    top_k = list(retrieved)[:k]
    return 1.0 if any(item in expected_set for item in top_k) else 0.0


def reciprocal_rank(retrieved: Iterable[str], expected: Iterable[str]) -> float:
    """1 / rank_of_first_expected_item. 0.0 if no expected item appears."""
    expected_set = set(expected)
    if not expected_set:
        return 0.0
    for rank, item in enumerate(retrieved, start=1):
        if item in expected_set:
            return 1.0 / rank
    return 0.0


def mean(values: Iterable[float]) -> float | None:
    """Mean of a non-empty iterable, or None for an empty one."""
    seq = list(values)
    return sum(seq) / len(seq) if seq else None
