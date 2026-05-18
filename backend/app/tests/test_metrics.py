"""Unit tests for eval retrieval metrics."""
from __future__ import annotations

from app.eval.metrics import mean, recall_at_k, reciprocal_rank


def test_recall_at_k_hit_in_top_k() -> None:
    assert recall_at_k(["a", "b", "c"], expected=["b"], k=3) == 1.0


def test_recall_at_k_hit_outside_top_k() -> None:
    assert recall_at_k(["a", "b", "c", "d"], expected=["d"], k=3) == 0.0


def test_recall_at_k_empty_expected() -> None:
    assert recall_at_k(["a", "b"], expected=[], k=3) == 0.0


def test_recall_at_k_k_zero() -> None:
    assert recall_at_k(["a", "b"], expected=["a"], k=0) == 0.0


def test_recall_at_k_multiple_expected_any_match() -> None:
    assert recall_at_k(["x", "y", "b"], expected=["a", "b"], k=5) == 1.0


def test_reciprocal_rank_first_position() -> None:
    assert reciprocal_rank(["a", "b"], expected=["a"]) == 1.0


def test_reciprocal_rank_second_position() -> None:
    assert reciprocal_rank(["a", "b"], expected=["b"]) == 0.5


def test_reciprocal_rank_no_hit() -> None:
    assert reciprocal_rank(["a", "b"], expected=["z"]) == 0.0


def test_reciprocal_rank_first_match_wins_over_later() -> None:
    # If both 'b' and 'd' are expected, the earlier one (rank 2) defines RR.
    assert reciprocal_rank(["a", "b", "c", "d"], expected=["b", "d"]) == 0.5


def test_mean_basic_and_empty() -> None:
    assert mean([1.0, 0.0, 1.0]) == 2.0 / 3.0
    assert mean([]) is None
