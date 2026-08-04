"""Integration tests: fcm/rater.py — LLM-based edge weight rating."""

from __future__ import annotations

import pytest

from backend.core.modules.fcm.rater import rate_edges, _parse_ratings
from tests.fixtures.systematology_fixtures import MockLLM, make_golden_shared_cld

VALID_RATINGS = """[
  {"source": "n_subsidy", "target": "n_demand", "rating": "+H", "confidence": 0.85, "reasoning": "Strong direct causal link"},
  {"source": "n_demand", "target": "n_price", "rating": "+M", "confidence": 0.6, "reasoning": "Moderate effect"},
  {"source": "n_price", "target": "n_supply", "rating": "+M", "confidence": 0.6, "reasoning": "Normal supply response"},
  {"source": "n_supply", "target": "n_growth", "rating": "+H", "confidence": 0.7, "reasoning": "Construction drives growth"},
  {"source": "n_growth", "target": "n_inflation", "rating": "+M", "confidence": 0.5, "reasoning": "Growth can increase CPI"},
  {"source": "n_subsidy", "target": "n_growth", "rating": "+H", "confidence": 0.8, "reasoning": "Fiscal policy impacts GDP"},
  {"source": "n_inflation", "target": "n_demand", "rating": "-H", "confidence": 0.75, "reasoning": "Inflation reduces purchasing power"}
]"""


# =====================================================================
# _parse_ratings Tests
# =====================================================================

class TestParseRatings:
    def test_valid_ratings(self):
        result = _parse_ratings(VALID_RATINGS)
        assert len(result) == 7
        assert ("n_subsidy", "n_demand") in result
        weight, confidence, reasoning = result[("n_subsidy", "n_demand")]
        assert weight == 0.7  # +H
        assert confidence == 0.85

    def test_negative_rating(self):
        text = '[{"source": "a", "target": "b", "rating": "-VH", "confidence": 0.9, "reasoning": "Strong inhibition"}]'
        result = _parse_ratings(text)
        weight, _, _ = result[("a", "b")]
        assert weight == -0.9

    def test_rating_in_code_block(self):
        simple_rating = '[{"source": "a", "target": "b", "rating": "+H", "confidence": 0.8, "reasoning": "strong"}]'
        text = f'```json\n{simple_rating}\n```'
        result = _parse_ratings(text)
        assert len(result) > 0

    def test_empty_input(self):
        assert _parse_ratings("") == {}

    def test_completely_unparseable(self):
        assert _parse_ratings("not json at all") == {}

    def test_unknown_rating_defaults_to_0_5(self):
        text = '[{"source": "a", "target": "b", "rating": "unknown", "confidence": 0.5, "reasoning": ""}]'
        result = _parse_ratings(text)
        weight, _, _ = result[("a", "b")]
        assert weight == 0.5


# =====================================================================
# rate_edges Tests
# =====================================================================

class TestRateEdges:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        cld = make_golden_shared_cld()
        llm = MockLLM(responses={"Rating Scale": VALID_RATINGS})

        result = await rate_edges(cld, llm)
        assert len(result) == 7
        for (src, tgt), (weight, confidence, reasoning) in result.items():
            assert -1.0 <= weight <= 1.0
            assert 0.0 <= confidence <= 1.0

    @pytest.mark.asyncio
    async def test_fallback_on_llm_error(self):
        cld = make_golden_shared_cld()

        class FailingLLM:
            async def acomplete(self, prompt, **kwargs):
                raise RuntimeError("API error")

        result = await rate_edges(cld, FailingLLM())
        # Should fall back to mapper defaults
        assert len(result) > 0
        for (src, tgt), (weight, confidence, reasoning) in result.items():
            assert reasoning == "fallback"
            assert confidence == 0.3

    @pytest.mark.asyncio
    async def test_empty_cld_returns_empty(self):
        from backend.core.models import SharedCLD

        cld = SharedCLD(nodes=[], edges=[])
        llm = MockLLM(responses={"Rating Scale": "[]"})

        result = await rate_edges(cld, llm)
        assert result == {}
