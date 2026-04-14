"""Tests for the evaluate_judgment research tool."""

import pytest

from backend.business.research_kernel.state import (
    Confidence,
    EvidenceItem,
    ResearchState,
)
from backend.business.research_kernel.tools.evaluate import (
    create_evaluate_tool,
    _format_report,
    _generate_suggestions,
)
from backend.infrastructure.evaluation.research_evaluator import (
    EvaluationResult,
    ResearchEvaluator,
)


def _make_state(
    question: str = "系统科学与还原论的优劣",
    judgment: str = "",
    evidence_texts: list[str] | None = None,
    confidence: Confidence = Confidence.LOW,
    tensions: list[str] | None = None,
    budget_turns: int = 10,
    current_turn: int = 0,
) -> ResearchState:
    """Helper to build a ResearchState for testing."""
    state = ResearchState(
        original_question=question,
        budget_turns=budget_turns,
    )
    state.current_judgment = judgment
    state.confidence = confidence
    state.unresolved_tensions = tensions or []
    state.current_turn = current_turn

    for i, text in enumerate(evidence_texts or []):
        state.record_evidence(
            EvidenceItem(query=f"query_{i}", text=text, source_ref=f"ref_{i}", score=0.8)
        )
    return state


class TestEvaluateToolCreation:
    def test_creates_function_tool(self):
        state = _make_state()
        tool = create_evaluate_tool(state, budget_turns=10)
        assert tool.metadata.name == "evaluate_judgment"

    def test_no_judgment_returns_warning(self):
        state = _make_state(judgment="")
        tool = create_evaluate_tool(state, budget_turns=10)
        result = tool.call()
        assert "尚未形成判断" in str(result)


class TestEvaluateToolExecution:
    def test_returns_scores(self):
        state = _make_state(
            judgment="系统思维比还原论更适合处理复杂适应系统的涌现行为",
            evidence_texts=[
                "系统思维强调整体性和涌现行为的不可还原性",
                "还原论在处理复杂适应系统时存在明显局限",
            ],
            tensions=["还原论在分子生物学领域仍有独特优势"],
            current_turn=5,
        )
        tool = create_evaluate_tool(state, budget_turns=10)
        result = str(tool.call())

        assert "判断质量评估" in result
        assert "证据可追溯性" in result
        assert "张力识别" in result
        assert "收束效率" in result
        assert "综合规则分" in result

    def test_good_output_shows_pass(self):
        state = _make_state(
            judgment="系统思维比还原论更适合处理复杂适应系统的涌现行为",
            evidence_texts=[
                "系统思维强调整体性和涌现行为的不可还原性",
                "还原论在处理复杂适应系统时存在明显局限",
            ],
            tensions=["还原论在分子生物学领域仍有独特优势"],
            current_turn=5,
        )
        tool = create_evaluate_tool(state, budget_turns=10)
        result = str(tool.call())
        assert "✓" in result

    def test_no_evidence_gives_low_traceability(self):
        state = _make_state(
            judgment="系统思维比还原论更适合处理复杂系统",
            current_turn=1,
        )
        tool = create_evaluate_tool(state, budget_turns=10)
        result = str(tool.call())
        assert "⚠" in result

    def test_does_not_consume_budget(self):
        state = _make_state(
            judgment="test judgment",
            evidence_texts=["test evidence text for judgment"],
            current_turn=3,
        )
        turn_before = state.current_turn
        tool = create_evaluate_tool(state, budget_turns=10)
        tool.call()
        assert state.current_turn == turn_before


class TestFormatReport:
    def test_shows_remaining_budget(self):
        state = _make_state(
            judgment="test",
            evidence_texts=["evidence"],
            current_turn=3,
            budget_turns=10,
        )
        result = EvaluationResult(
            evidence_traceability=0.5,
            tension_identification=0.8,
            convergence_efficiency=1.0,
        )
        report = _format_report(result, state)
        assert "剩余预算: 7轮" in report


class TestGenerateSuggestions:
    def test_low_traceability_suggests_improvement(self):
        state = _make_state(judgment="test")
        result = EvaluationResult(
            evidence_traceability=0.05,
            tension_identification=0.8,
            convergence_efficiency=1.0,
        )
        suggestions = _generate_suggestions(result, state)
        assert len(suggestions) >= 1
        assert "可追溯性" in suggestions[0]

    def test_no_tensions_suggests_identification(self):
        state = _make_state(judgment="test")
        result = EvaluationResult(
            evidence_traceability=0.5,
            tension_identification=0.0,
            convergence_efficiency=1.0,
        )
        suggestions = _generate_suggestions(result, state)
        assert any("张力" in s for s in suggestions)

    def test_all_pass_no_suggestions(self):
        state = _make_state(
            judgment="test",
            tensions=["real tension here"],
        )
        result = EvaluationResult(
            evidence_traceability=0.5,
            tension_identification=0.8,
            convergence_efficiency=1.0,
        )
        suggestions = _generate_suggestions(result, state)
        assert len(suggestions) == 0

    def test_generic_tensions_suggests_rewrite(self):
        state = _make_state(
            judgment="test",
            tensions=["需要更多研究"],
        )
        result = EvaluationResult(
            evidence_traceability=0.5,
            tension_identification=0.2,
            convergence_efficiency=1.0,
        )
        suggestions = _generate_suggestions(result, state)
        assert any("泛化" in s for s in suggestions)
