"""Unit tests for retrieval fusion (RRF) and edge cases."""
from __future__ import annotations

from uuid import uuid4

from app.services.retrieval_service import reciprocal_rank_fusion


def test_rrf_empty_inputs() -> None:
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []


def test_rrf_single_ranking_is_monotonic() -> None:
    a, b, c = uuid4(), uuid4(), uuid4()
    fused = reciprocal_rank_fusion([[a, b, c]])
    assert [item for item, _ in fused] == [a, b, c]
    scores = [s for _, s in fused]
    assert scores == sorted(scores, reverse=True)


def test_rrf_items_in_both_rankings_outrank_singles() -> None:
    a, b, c, d = uuid4(), uuid4(), uuid4(), uuid4()
    # 'a' is rank 2 in both → strong signal even though never rank 1.
    fused = reciprocal_rank_fusion([[b, a, c], [d, a, c]])
    items = [item for item, _ in fused]
    assert items[0] == a, "item present in both rankings should win"


def test_rrf_high_ranks_score_higher_than_low() -> None:
    a, b = uuid4(), uuid4()
    fused = dict(reciprocal_rank_fusion([[a, b]]))
    assert fused[a] > fused[b]


def test_rrf_k_parameter_dampens_top_advantage() -> None:
    a, b = uuid4(), uuid4()
    small_k = dict(reciprocal_rank_fusion([[a, b]], k=1))
    big_k = dict(reciprocal_rank_fusion([[a, b]], k=1000))
    ratio_small = small_k[a] / small_k[b]
    ratio_big = big_k[a] / big_k[b]
    assert ratio_small > ratio_big, "larger k should compress score differences"
