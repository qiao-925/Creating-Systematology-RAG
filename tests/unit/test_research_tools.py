"""
研究内核工具集单元测试

覆盖：evidence、synthesis、reflection 工具的核心逻辑。
search 工具依赖 IndexManager，通过 mock 验证调用链。
"""

import pytest
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

from backend.business.research_kernel.state import (
    Confidence,
    EvidenceItem,
    ResearchState,
)
from backend.business.research_kernel.tools.evidence import create_evidence_tool
from backend.business.research_kernel.tools.synthesis import create_synthesis_tool
from backend.business.research_kernel.tools.reflection import create_reflection_tool
from backend.business.research_kernel.tools.search import (
    create_search_tools,
    _format_results,
    _extract_source_ref,
)


# ========== Fixtures ==========


@pytest.fixture
def state():
    return ResearchState(original_question="钱学森系统学的核心方法论是什么？", budget_turns=5)


@pytest.fixture
def state_with_evidence(state):
    state.record_evidence(
        EvidenceItem(query="系统学方法论", text="从定性到定量的综合集成法。", source_ref="file:方法论.md", score=0.9)
    )
    state.record_evidence(
        EvidenceItem(query="开放复杂巨系统", text="提出处理开放复杂巨系统的方法论。", source_ref="file:巨系统.md", score=0.85)
    )
    return state


# ========== Evidence Tool ==========


class TestEvidenceTool:

    def test_record_evidence_success(self, state):
        tool = create_evidence_tool(state)
        result = tool.call(query="子查询", text="证据文本", source_ref="file:a.md", score=0.8)
        assert "证据已记录" in str(result)
        assert state.evidence_count == 1
        assert state.current_turn == 1

    def test_record_multiple(self, state):
        tool = create_evidence_tool(state)
        tool.call(query="q1", text="t1", source_ref="ref1", score=0.9)
        tool.call(query="q2", text="t2", source_ref="ref2", score=0.7)
        assert state.evidence_count == 2
        assert state.current_turn == 2

    def test_empty_query_rejected(self, state):
        tool = create_evidence_tool(state)
        result = tool.call(query="", text="有内容", source_ref="", score=0.0)
        assert "错误" in str(result)
        assert state.evidence_count == 0

    def test_empty_text_rejected(self, state):
        tool = create_evidence_tool(state)
        result = tool.call(query="有查询", text="", source_ref="", score=0.0)
        assert "错误" in str(result)
        assert state.evidence_count == 0

    def test_score_clamped(self, state):
        tool = create_evidence_tool(state)
        tool.call(query="q", text="t", source_ref="", score=1.5)
        assert state.evidence_ledger[0].score == 1.0

    def test_budget_exhaustion(self):
        state = ResearchState(original_question="q", budget_turns=2)
        tool = create_evidence_tool(state)
        tool.call(query="q1", text="t1")
        tool.call(query="q2", text="t2")
        assert state.is_stopped

    def test_budget_exhaustion_rejects_further_evidence(self):
        """预算耗尽后，拒绝追加证据且不改变 state"""
        state = ResearchState(original_question="q", budget_turns=2)
        tool = create_evidence_tool(state)
        tool.call(query="q1", text="t1")
        tool.call(query="q2", text="t2")
        assert state.is_stopped
        evidence_before = state.evidence_count
        turn_before = state.current_turn
        result = str(tool.call(query="q3", text="t3"))
        assert "预算已耗尽" in result
        assert state.evidence_count == evidence_before
        assert state.current_turn == turn_before


# ========== Synthesis Tool ==========


class TestSynthesisTool:

    def test_synthesize_success(self, state_with_evidence):
        tool = create_synthesis_tool(state_with_evidence)
        result = tool.call(
            judgment="系统学的核心方法论是从定性到定量的综合集成法。",
            confidence="medium",
            tensions="定量与定性之间的张力",
            next_questions="如何量化整体性？|具体应用案例？",
        )
        assert "判断已记录" in str(result)
        assert state_with_evidence.current_judgment == "系统学的核心方法论是从定性到定量的综合集成法。"
        assert state_with_evidence.confidence == Confidence.MEDIUM
        assert len(state_with_evidence.unresolved_tensions) == 1
        assert len(state_with_evidence.next_questions) == 2

    def test_empty_judgment_rejected(self, state_with_evidence):
        tool = create_synthesis_tool(state_with_evidence)
        result = tool.call(judgment="", confidence="high")
        assert "错误" in str(result)

    def test_no_evidence_rejected(self, state):
        tool = create_synthesis_tool(state)
        result = tool.call(judgment="随意判断", confidence="high")
        assert "证据账本为空" in str(result)

    def test_invalid_confidence_defaults_to_low(self, state_with_evidence):
        tool = create_synthesis_tool(state_with_evidence)
        tool.call(judgment="判断", confidence="invalid")
        assert state_with_evidence.confidence == Confidence.LOW

    def test_empty_tensions_and_questions(self, state_with_evidence):
        tool = create_synthesis_tool(state_with_evidence)
        tool.call(judgment="判断", confidence="high", tensions="", next_questions="")
        assert state_with_evidence.unresolved_tensions == []
        assert state_with_evidence.next_questions == []


# ========== Reflection Tool ==========


class TestReflectionTool:

    def test_reflect_empty_state(self, state):
        tool = create_reflection_tool(state)
        result = str(tool.call())
        assert "尚未收集任何证据" in result
        assert "钱学森系统学" in result
        assert "建议" in result

    def test_reflect_with_evidence(self, state_with_evidence):
        tool = create_reflection_tool(state_with_evidence)
        result = str(tool.call())
        assert "证据数量：2条" in result
        assert "方法论.md" in result or "file:方法论.md" in result

    def test_reflect_with_judgment(self, state_with_evidence):
        state_with_evidence.current_judgment = "核心方法论是综合集成法。"
        state_with_evidence.confidence = Confidence.MEDIUM
        tool = create_reflection_tool(state_with_evidence)
        result = str(tool.call())
        assert "当前判断" in result
        assert "medium" in result

    def test_reflect_budget_warning(self):
        state = ResearchState(original_question="q", budget_turns=2, current_turn=1)
        state.record_evidence(EvidenceItem(query="q", text="t", score=0.5))
        tool = create_reflection_tool(state)
        result = str(tool.call())
        assert "预算即将耗尽" in result


# ========== Search Helpers ==========


class TestSearchHelpers:

    def test_extract_source_ref_file_name(self):
        assert _extract_source_ref({"file_name": "test.md"}) == "file:test.md"

    def test_extract_source_ref_file_path(self):
        assert _extract_source_ref({"file_path": "/data/test.md"}) == "path:/data/test.md"

    def test_extract_source_ref_unknown(self):
        assert _extract_source_ref({}) == "unknown"

    def test_format_results_empty(self):
        result = _format_results([], "vector", "test query")
        assert "0条" in result

    def test_format_results_with_nodes(self):
        node = SimpleNamespace(
            text="系统科学是研究系统的学科。",
            metadata={"file_name": "系统科学.md"},
        )
        node_with_score = SimpleNamespace(node=node, score=0.91)
        result = _format_results([node_with_score], "vector", "test")
        assert "0.91" in result
        assert "file:系统科学.md" in result
        assert "系统科学是研究系统的学科" in result


class TestSearchToolCreation:

    @patch("backend.business.research_kernel.tools.search.create_retriever")
    def test_create_search_tools_returns_two(self, mock_retriever):
        mock_im = MagicMock()
        mock_im.get_index.return_value = MagicMock()
        tools = create_search_tools(mock_im, similarity_top_k=3)
        assert len(tools) == 2
        names = {t.metadata.name for t in tools}
        assert names == {"vector_search", "hybrid_search"}

    @patch("backend.business.research_kernel.tools.search.create_retriever")
    def test_vector_search_calls_retriever(self, mock_create):
        mock_retriever = MagicMock()
        node = SimpleNamespace(
            text="证据文本", metadata={"file_name": "src.md"}
        )
        mock_retriever.retrieve.return_value = [SimpleNamespace(node=node, score=0.88)]
        mock_create.return_value = mock_retriever

        mock_im = MagicMock()
        mock_im.get_index.return_value = MagicMock()
        tools = create_search_tools(mock_im, similarity_top_k=3)

        vector_tool = next(t for t in tools if t.metadata.name == "vector_search")
        result = str(vector_tool.call(query="测试查询"))
        assert "证据文本" in result
        assert "0.88" in result
        mock_create.assert_called()
