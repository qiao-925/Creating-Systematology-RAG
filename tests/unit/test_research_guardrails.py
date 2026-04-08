"""
研究内核硬护栏测试

验证四条护栏在代码层的强制性：
1. timeout → AgentWorkflow 配置
2. max_iterations → AgentWorkflow 配置
3. prompt 约束（无证据不出判断）→ synthesize 工具拒绝
4. 输出 schema 强制（ResearchOutput）→ from_state 始终有效
附加：预算耗尽自动收束
"""

import pytest

from backend.business.research_kernel.state import (
    Confidence,
    EvidenceItem,
    ResearchOutput,
    ResearchState,
    StopReason,
)
from backend.business.research_kernel.tools.synthesis import create_synthesis_tool
from backend.business.research_kernel.tools.evidence import create_evidence_tool


class TestNoEvidenceNoJudgment:
    """护栏 #3：无证据不出判断"""

    def test_synthesize_rejected_without_evidence(self):
        state = ResearchState(original_question="测试")
        tool = create_synthesis_tool(state)
        result = str(tool.call(judgment="随意判断", confidence="high"))
        assert "证据账本为空" in result
        assert state.current_judgment == ""

    def test_synthesize_allowed_with_evidence(self):
        state = ResearchState(original_question="测试")
        state.record_evidence(EvidenceItem(query="q", text="t", score=0.5))
        tool = create_synthesis_tool(state)
        result = str(tool.call(judgment="有据可依的判断", confidence="medium"))
        assert "判断已记录" in result
        assert state.current_judgment == "有据可依的判断"


class TestBudgetExhaustion:
    """护栏 #2 补充：预算耗尽自动收束"""

    def test_budget_exhaustion_sets_stop_reason(self):
        state = ResearchState(original_question="测试", budget_turns=2)
        tool = create_evidence_tool(state)
        tool.call(query="q1", text="t1")
        tool.call(query="q2", text="t2")
        assert state.is_stopped
        assert state.stop_reason == StopReason.BUDGET_EXHAUSTED
        assert state.budget_remaining == 0

    def test_output_from_exhausted_state(self):
        state = ResearchState(original_question="测试", budget_turns=1)
        state.record_evidence(EvidenceItem(query="q", text="t", score=0.5))
        state.increment_turn()
        state.current_judgment = "部分结论"
        output = ResearchOutput.from_state(state)
        assert output.stop_reason == StopReason.BUDGET_EXHAUSTED
        assert output.judgment == "部分结论"
        assert output.turns_used == 1


class TestOutputSchemaEnforcement:
    """护栏 #4：输出 schema 始终有效"""

    def test_output_always_valid_from_empty_state(self):
        state = ResearchState(original_question="空状态测试")
        output = ResearchOutput.from_state(state)
        assert isinstance(output, ResearchOutput)
        assert output.judgment  # 非空
        assert output.confidence == Confidence.LOW
        assert output.turns_used == 0

    def test_output_serializable(self):
        state = ResearchState(original_question="序列化测试")
        state.record_evidence(EvidenceItem(query="q", text="t", source_ref="ref", score=0.8))
        state.current_judgment = "判断"
        state.confidence = Confidence.HIGH
        output = ResearchOutput.from_state(state)
        data = output.model_dump()
        restored = ResearchOutput.model_validate(data)
        assert restored.judgment == "判断"
        assert restored.confidence == Confidence.HIGH

    def test_output_from_state_with_all_fields(self):
        state = ResearchState(
            original_question="全字段测试",
            focused_question="聚焦",
            budget_turns=5,
            current_turn=3,
        )
        state.record_evidence(EvidenceItem(query="q1", text="t1", source_ref="r1", score=0.9))
        state.record_evidence(EvidenceItem(query="q2", text="t2", source_ref="r2", score=0.7))
        state.current_judgment = "系统学方法论的核心是综合集成法"
        state.confidence = Confidence.MEDIUM
        state.unresolved_tensions = ["张力A", "张力B"]
        state.next_questions = ["追问1"]
        state.stop_reason = StopReason.CONVERGED

        output = ResearchOutput.from_state(state)
        assert output.judgment == "系统学方法论的核心是综合集成法"
        assert output.confidence == Confidence.MEDIUM
        assert len(output.evidence) == 2
        assert output.evidence_refs == ["r1", "r2"]
        assert output.tensions == ["张力A", "张力B"]
        assert output.next_questions == ["追问1"]
        assert output.turns_used == 3
        assert output.stop_reason == StopReason.CONVERGED


class TestTimeoutAndIterationConfig:
    """护栏 #1 #2：timeout 和 max_iterations 配置验证"""

    def test_agent_accepts_guardrail_params(self):
        from backend.business.research_kernel.agent import ResearchAgent
        from unittest.mock import MagicMock

        agent = ResearchAgent(
            index_manager=MagicMock(),
            llm=MagicMock(),
            budget_turns=5,
            max_iterations=15,
            timeout_seconds=60.0,
        )
        assert agent._budget_turns == 5
        assert agent._max_iterations == 15
        assert agent._timeout_seconds == 60.0
