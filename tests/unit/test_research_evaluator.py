"""Tests for the research output quality evaluator."""

import pytest

from backend.business.research_kernel.state import (
    Confidence,
    EvidenceItem,
    ResearchOutput,
    StopReason,
)
from backend.infrastructure.evaluation.research_evaluator import (
    EvaluationResult,
    ResearchEvaluator,
)


def _make_output(
    judgment: str = "系统思维比还原论更适合处理复杂适应系统的涌现行为",
    evidence_texts: list[str] | None = None,
    confidence: Confidence = Confidence.MEDIUM,
    tensions: list[str] | None = None,
    next_questions: list[str] | None = None,
    turns_used: int = 5,
    stop_reason: StopReason = StopReason.CONVERGED,
) -> ResearchOutput:
    """Helper to build a ResearchOutput for testing."""
    evidence = []
    for i, text in enumerate(evidence_texts or []):
        evidence.append(
            EvidenceItem(query=f"query_{i}", text=text, source_ref=f"ref_{i}", score=0.8)
        )
    return ResearchOutput(
        judgment=judgment,
        evidence=evidence,
        confidence=confidence,
        tensions=tensions or [],
        next_questions=next_questions or [],
        turns_used=turns_used,
        stop_reason=stop_reason,
    )


class TestEvidenceTraceability:
    def setup_method(self):
        self.evaluator = ResearchEvaluator()

    def test_high_traceability(self):
        output = _make_output(
            judgment="系统思维比还原论更适合处理复杂适应系统的涌现行为",
            evidence_texts=[
                "系统思维强调整体性和涌现行为的不可还原性",
                "还原论在处理复杂适应系统时存在明显局限",
            ],
        )
        result = self.evaluator.evaluate(output)
        assert result.evidence_traceability > 0.3

    def test_no_evidence(self):
        output = _make_output(evidence_texts=[])
        result = self.evaluator.evaluate(output)
        assert result.evidence_traceability == 0.0

    def test_no_judgment(self):
        output = _make_output(judgment="短", evidence_texts=["some evidence text here"])
        result = self.evaluator.evaluate(output)
        # Short judgment gets neutral score
        assert result.evidence_traceability >= 0.0


class TestTensionIdentification:
    def setup_method(self):
        self.evaluator = ResearchEvaluator()

    def test_meaningful_tensions(self):
        output = _make_output(
            tensions=["还原论在分子生物学领域仍有独特优势，与系统思维并非完全对立"]
        )
        result = self.evaluator.evaluate(output)
        assert result.tension_identification >= 0.5

    def test_no_tensions_high_confidence(self):
        output = _make_output(
            confidence=Confidence.HIGH,
            evidence_texts=["some evidence"],
            tensions=[],
        )
        result = self.evaluator.evaluate(output)
        assert result.tension_identification == 0.7  # Acceptable for high confidence

    def test_generic_tensions_only(self):
        output = _make_output(tensions=["需要更多研究", "有待进一步验证"])
        result = self.evaluator.evaluate(output)
        assert result.tension_identification <= 0.3

    def test_no_tensions_low_confidence(self):
        output = _make_output(confidence=Confidence.LOW, tensions=[])
        result = self.evaluator.evaluate(output)
        assert result.tension_identification == 0.0


class TestConvergenceEfficiency:
    def setup_method(self):
        self.evaluator = ResearchEvaluator()

    def test_ideal_convergence(self):
        output = _make_output(
            turns_used=5,
            evidence_texts=["evidence"],
        )
        result = self.evaluator.evaluate(output, budget_turns=10)
        assert result.convergence_efficiency == 1.0

    def test_budget_exhausted(self):
        output = _make_output(
            turns_used=10,
            stop_reason=StopReason.BUDGET_EXHAUSTED,
            evidence_texts=["evidence"],
        )
        result = self.evaluator.evaluate(output, budget_turns=10)
        assert result.convergence_efficiency <= 0.5

    def test_zero_turns(self):
        output = _make_output(turns_used=0)
        result = self.evaluator.evaluate(output, budget_turns=10)
        assert result.convergence_efficiency == 0.0

    def test_fast_convergence(self):
        output = _make_output(turns_used=2, evidence_texts=["evidence"])
        result = self.evaluator.evaluate(output, budget_turns=10)
        assert result.convergence_efficiency >= 0.7


class TestEvaluationResult:
    def test_rule_based_score(self):
        result = EvaluationResult(
            evidence_traceability=0.8,
            tension_identification=0.6,
            convergence_efficiency=1.0,
        )
        assert abs(result.rule_based_score - 0.8) < 0.01

    def test_overall_with_llm(self):
        result = EvaluationResult(
            evidence_traceability=0.8,
            tension_identification=0.6,
            convergence_efficiency=1.0,
            judgment_has_position=1.0,
            next_questions_quality=0.7,
        )
        assert result.overall_score is not None
        assert 0.5 < result.overall_score < 1.0

    def test_to_dict(self):
        result = EvaluationResult(evidence_traceability=0.5)
        d = result.to_dict()
        assert "evidence_traceability" in d
        assert "rule_based_score" in d
        assert "overall_score" in d
