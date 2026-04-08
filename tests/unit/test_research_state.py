"""
研究内核状态与输出模型的单元测试

覆盖：EvidenceItem、ResearchState、ResearchOutput 的创建、验证、状态变更和转换。
"""

import pytest
from pydantic import ValidationError

from backend.business.research_kernel.state import (
    Confidence,
    EvidenceItem,
    ResearchOutput,
    ResearchState,
    StopReason,
)


# ========== EvidenceItem ==========


class TestEvidenceItem:
    """证据项模型测试"""

    def test_create_minimal(self):
        item = EvidenceItem(query="什么是系统学？", text="系统学研究系统的一般规律。")
        assert item.query == "什么是系统学？"
        assert item.text == "系统学研究系统的一般规律。"
        assert item.score == 0.0
        assert item.source_ref == ""

    def test_create_full(self):
        item = EvidenceItem(
            query="钱学森的贡献",
            text="提出开放的复杂巨系统理论。",
            source_ref="file:钱学森.md",
            score=0.92,
            metadata={"file_name": "钱学森.md"},
        )
        assert item.source_ref == "file:钱学森.md"
        assert item.score == 0.92
        assert item.metadata["file_name"] == "钱学森.md"

    def test_empty_query_raises(self):
        with pytest.raises(ValidationError):
            EvidenceItem(query="", text="有内容")

    def test_empty_text_raises(self):
        with pytest.raises(ValidationError):
            EvidenceItem(query="有查询", text="")

    def test_whitespace_only_query_raises(self):
        with pytest.raises(ValidationError):
            EvidenceItem(query="   ", text="有内容")

    def test_strips_whitespace(self):
        item = EvidenceItem(query="  问题  ", text="  内容  ")
        assert item.query == "问题"
        assert item.text == "内容"

    def test_score_bounds(self):
        with pytest.raises(ValidationError):
            EvidenceItem(query="q", text="t", score=1.5)
        with pytest.raises(ValidationError):
            EvidenceItem(query="q", text="t", score=-0.1)


# ========== ResearchState ==========


class TestResearchState:
    """研究状态模型测试"""

    def test_create_minimal(self):
        state = ResearchState(original_question="什么是系统学？")
        assert state.original_question == "什么是系统学？"
        assert state.focused_question == ""
        assert state.confidence == Confidence.LOW
        assert state.current_turn == 0
        assert state.budget_turns == 10
        assert not state.is_stopped
        assert state.budget_remaining == 10
        assert state.evidence_count == 0

    def test_empty_question_raises(self):
        with pytest.raises(ValidationError):
            ResearchState(original_question="")

    def test_whitespace_question_raises(self):
        with pytest.raises(ValidationError):
            ResearchState(original_question="   ")

    def test_record_evidence(self):
        state = ResearchState(original_question="测试问题")
        item = EvidenceItem(query="子查询", text="证据文本", source_ref="file:a.md", score=0.8)
        state.record_evidence(item)
        assert state.evidence_count == 1
        assert state.has_evidence
        assert state.evidence_ledger[0].query == "子查询"

    def test_increment_turn(self):
        state = ResearchState(original_question="测试", budget_turns=3)
        assert state.budget_remaining == 3

        state.increment_turn()
        assert state.current_turn == 1
        assert state.budget_remaining == 2
        assert not state.is_stopped

        state.increment_turn()
        state.increment_turn()
        assert state.current_turn == 3
        assert state.budget_remaining == 0
        assert state.is_stopped
        assert state.stop_reason == StopReason.BUDGET_EXHAUSTED

    def test_budget_bounds(self):
        with pytest.raises(ValidationError):
            ResearchState(original_question="q", budget_turns=0)
        with pytest.raises(ValidationError):
            ResearchState(original_question="q", budget_turns=51)

    def test_full_state(self):
        state = ResearchState(
            original_question="原始问题",
            focused_question="聚焦问题",
            research_boundary="边界说明",
            evidence_plan=["计划1", "计划2"],
            confidence=Confidence.MEDIUM,
            budget_turns=5,
            unresolved_tensions=["张力A"],
            next_questions=["追问1"],
        )
        assert state.focused_question == "聚焦问题"
        assert len(state.evidence_plan) == 2
        assert state.confidence == Confidence.MEDIUM
        assert state.unresolved_tensions == ["张力A"]


# ========== ResearchOutput ==========


class TestResearchOutput:
    """研究输出模型测试"""

    def test_create_minimal(self):
        output = ResearchOutput(judgment="核心结论成立。")
        assert output.judgment == "核心结论成立。"
        assert output.confidence == Confidence.LOW
        assert output.turns_used == 0
        assert not output.has_evidence
        assert output.evidence_refs == []

    def test_empty_judgment_raises(self):
        with pytest.raises(ValidationError):
            ResearchOutput(judgment="")

    def test_whitespace_judgment_raises(self):
        with pytest.raises(ValidationError):
            ResearchOutput(judgment="   ")

    def test_full_output(self):
        evidence = [
            EvidenceItem(query="q1", text="证据1", source_ref="file:a.md", score=0.9),
            EvidenceItem(query="q2", text="证据2", source_ref="file:b.md", score=0.85),
        ]
        output = ResearchOutput(
            judgment="核心结论成立。",
            evidence=evidence,
            confidence=Confidence.HIGH,
            tensions=["张力A", "张力B"],
            next_questions=["追问1"],
            turns_used=3,
            stop_reason=StopReason.CONVERGED,
        )
        assert output.has_evidence
        assert len(output.evidence) == 2
        assert output.evidence_refs == ["file:a.md", "file:b.md"]
        assert output.tensions == ["张力A", "张力B"]
        assert output.turns_used == 3

    def test_from_state_with_judgment(self):
        state = ResearchState(
            original_question="系统学的核心方法论",
            focused_question="聚焦",
            current_judgment="系统学的核心方法论是从整体出发的系统分析。",
            confidence=Confidence.MEDIUM,
            budget_turns=5,
            current_turn=3,
            unresolved_tensions=["定量与定性方法之间的张力"],
            next_questions=["如何量化整体性？"],
        )
        state.record_evidence(
            EvidenceItem(query="q1", text="证据", source_ref="file:x.md", score=0.88)
        )
        state.stop_reason = StopReason.CONVERGED

        output = ResearchOutput.from_state(state)
        assert output.judgment == "系统学的核心方法论是从整体出发的系统分析。"
        assert output.confidence == Confidence.MEDIUM
        assert output.turns_used == 3
        assert len(output.evidence) == 1
        assert output.tensions == ["定量与定性方法之间的张力"]
        assert output.next_questions == ["如何量化整体性？"]
        assert output.stop_reason == StopReason.CONVERGED

    def test_from_state_without_judgment(self):
        state = ResearchState(original_question="测试问题")
        output = ResearchOutput.from_state(state)
        assert "测试问题" in output.judgment
        assert "尚未形成" in output.judgment

    def test_from_state_budget_exhausted(self):
        state = ResearchState(original_question="问题", budget_turns=2)
        state.increment_turn()
        state.increment_turn()
        state.current_judgment = "部分结论"

        output = ResearchOutput.from_state(state)
        assert output.stop_reason == StopReason.BUDGET_EXHAUSTED
        assert output.turns_used == 2

    def test_serialization_roundtrip(self):
        output = ResearchOutput(
            judgment="判断",
            evidence=[EvidenceItem(query="q", text="t", source_ref="ref", score=0.5)],
            confidence=Confidence.HIGH,
            tensions=["张力"],
            next_questions=["追问"],
            turns_used=2,
        )
        data = output.model_dump()
        restored = ResearchOutput.model_validate(data)
        assert restored.judgment == output.judgment
        assert restored.confidence == output.confidence
        assert len(restored.evidence) == 1
        assert restored.evidence[0].source_ref == "ref"


# ========== Enum 测试 ==========


class TestEnums:
    def test_confidence_values(self):
        assert Confidence.HIGH == "high"
        assert Confidence.MEDIUM == "medium"
        assert Confidence.LOW == "low"

    def test_stop_reason_values(self):
        assert StopReason.CONVERGED == "converged"
        assert StopReason.BUDGET_EXHAUSTED == "budget_exhausted"
        assert StopReason.NOT_STOPPED == ""
