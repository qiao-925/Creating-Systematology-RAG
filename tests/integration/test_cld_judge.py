"""Integration tests: cld/judge.py — CLD quality judging with mock LLM."""

from __future__ import annotations

import pytest

from backend.core.modules.cld.judge import judge_cld_output, self_review_gate, _parse_judge_response
from tests.fixtures.systematology_fixtures import (
    MockLLM,
    make_golden_shared_cld,
    make_specialist_outputs,
)


# =====================================================================
# _parse_judge_response Tests
# =====================================================================

class TestParseJudgeResponse:
    def test_plain_json(self):
        result = _parse_judge_response(
            '{"approved": true, "quality_score": 0.85, "issues": [], "suggestions": [], "reasoning": "good"}'
        )
        assert result["approved"] is True
        assert result["quality_score"] == 0.85

    def test_json_in_code_block(self):
        text = '```json\n{"approved": false, "quality_score": 0.3, "issues": ["too simple"], "suggestions": ["add nodes"], "reasoning": "meh"}\n```'
        result = _parse_judge_response(text)
        assert result["approved"] is False
        assert result["quality_score"] == 0.3
        assert result["issues"] == ["too simple"]

    def test_malformed_json_fallback_to_braces(self):
        text = 'some text {"approved": true, "quality_score": 0.6, "issues": [], "suggestions": ["tip"], "reasoning": "ok"} more text'
        result = _parse_judge_response(text)
        assert result["approved"] is True
        assert result["quality_score"] == 0.6

    def test_completely_unparseable(self):
        result = _parse_judge_response("just some random text, no JSON at all here")
        assert result["approved"] is True  # default
        assert result["quality_score"] == 0.5


# =====================================================================
# judge_cld_output Tests
# =====================================================================

class TestJudgeCLDOutput:
    @pytest.mark.asyncio
    async def test_happy_path_with_mock_llm(self):
        cld = make_golden_shared_cld()
        specialists = make_specialist_outputs()
        conflicts: list[dict] = []
        llm = MockLLM()

        result = await judge_cld_output(cld, specialists, conflicts, llm)
        assert "approved" in result
        assert "quality_score" in result
        assert 0.0 <= result["quality_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_with_conflicts(self):
        cld = make_golden_shared_cld()
        specialists = make_specialist_outputs()
        conflicts = [{
            "source": "n_subsidy", "target": "n_demand",
            "perspectives": {"p1": "causes", "p2": "inhibits"},
            "severity": "high",
        }]
        llm = MockLLM()
        result = await judge_cld_output(cld, specialists, conflicts, llm)
        assert "approved" in result

    @pytest.mark.asyncio
    async def test_llm_exception_defaults_to_approved(self):
        """When LLM fails, judge falls back to approved=True with 0.5 score."""
        cld = make_golden_shared_cld()
        specialists = make_specialist_outputs()

        class FailingLLM:
            async def acomplete(self, prompt, **kwargs):
                raise RuntimeError("LLM API error")

        result = await judge_cld_output(cld, specialists, [], FailingLLM())
        assert result["approved"] is True
        assert result["quality_score"] == 0.5
        assert "Judge failed" in result["issues"][0]


# =====================================================================
# self_review_gate Tests
# =====================================================================

class TestSelfReviewGate:
    @pytest.mark.asyncio
    async def test_structural_fail_too_few_nodes(self):
        from backend.core.models import CLDNode, SharedCLD
        cld = SharedCLD(nodes=[CLDNode(id="a", label="A")], edges=[])
        specialists = make_specialist_outputs()
        llm = MockLLM()

        passed, review = await self_review_gate(cld, specialists, [], llm)
        assert passed is False
        assert "Too few nodes" in review.get("issues", [""])[0]

    @pytest.mark.asyncio
    async def test_structural_fail_no_edges(self):
        from backend.core.models import CLDNode, SharedCLD
        cld = SharedCLD(
            nodes=[CLDNode(id="a", label="A"), CLDNode(id="b", label="B")],
            edges=[],
        )
        specialists = make_specialist_outputs()
        llm = MockLLM()

        passed, review = await self_review_gate(cld, specialists, [], llm)
        assert passed is False
        assert "No edges" in review.get("issues", [""])[0]

    @pytest.mark.asyncio
    async def test_passes_with_quality_check(self):
        cld = make_golden_shared_cld()
        specialists = make_specialist_outputs()
        llm = MockLLM()  # default response: quality_score=0.7, approved=true

        passed, review = await self_review_gate(cld, specialists, [], llm)
        assert passed is True
        assert review["quality_score"] > 0.35

    @pytest.mark.asyncio
    async def test_fails_on_low_quality_score(self):
        cld = make_golden_shared_cld()
        specialists = make_specialist_outputs()
        low_quality_response = '{"approved": false, "quality_score": 0.2, "issues": ["bad"], "suggestions": [], "reasoning": "poor"}'
        llm = MockLLM(responses={"judge": low_quality_response})

        passed, review = await self_review_gate(cld, specialists, [], llm, min_quality_score=0.35)
        assert passed is False
