from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from backend.business.rag_engine.agentic.engine import AgenticQueryEngine
from backend.business.rag_engine.agentic.research_trace import build_research_trace


def test_build_research_trace_with_evidence():
    research = build_research_trace(
        question="系统科学的核心判断是什么？",
        answer="系统科学强调整体性、关系性和跨层次建模。",
        sources=[
            {
                "text": "系统科学关注整体、关系与层次。",
                "score": 0.91,
                "metadata": {"file_name": "systems.md"},
            }
        ],
        reasoning_content="先归纳定义，再检查证据覆盖。",
    )

    assert research["current_judgment"] == "系统科学强调整体性、关系性和跨层次建模"
    assert research["supporting_evidence"][0]["file_name"] == "systems.md"
    assert research["open_tensions"] == []
    assert research["stop_reason"] == "evidence_sufficient_for_now"
    assert research["recommended_action"] == "synthesize_answer"
    assert research["has_reasoning_trace"] is True


def test_build_research_trace_without_evidence():
    research = build_research_trace(
        question="钱学森如何定义综合集成方法？",
        answer="目前还不能给出稳定回答。",
        sources=[],
        reasoning_content=None,
    )

    assert research["supporting_evidence"] == []
    assert research["open_tensions"] == ["当前回答缺少可核实来源，无法支撑阶段性判断。"]
    assert research["stop_reason"] == "insufficient_evidence"
    assert research["recommended_action"] == "stop_due_to_insufficient_evidence"
    assert "还缺少哪些一手材料或文档" in research["next_question"]


def test_build_research_trace_with_uncertainty():
    research = build_research_trace(
        question="系统工程与运筹学的边界是什么？",
        answer="两者有部分重叠，但具体边界仍需更多案例来验证。",
        sources=[
            {
                "text": "系统工程与运筹学都涉及优化与决策。",
                "score": 0.82,
                "metadata": {"file_name": "comparison.md"},
            }
        ],
        reasoning_content=None,
    )

    assert research["open_tensions"] == ["两者有部分重叠，但具体边界仍需更多案例来验证"]
    assert research["stop_reason"] == "needs_more_evidence"
    assert research["recommended_action"] == "continue_gathering_evidence"
    assert "下一步应补什么证据" in research["next_question"]


def test_agentic_query_engine_adds_research_trace(mocker):
    observer_manager = SimpleNamespace(
        observers=[],
        on_query_start=Mock(return_value=[]),
        on_query_end=Mock(),
    )
    index_manager = Mock()
    index_manager.get_index.return_value = Mock()

    mocker.patch.object(AgenticQueryEngine, "_setup_llm", return_value=Mock())
    mocker.patch.object(AgenticQueryEngine, "_setup_observer_manager", return_value=observer_manager)

    engine = AgenticQueryEngine(index_manager=index_manager)
    engine.formatter = Mock(format=Mock(return_value="格式化后的回答"))

    agent = Mock()
    response = Mock()
    response.__str__ = Mock(return_value="阶段性判断已经形成。")

    mocker.patch.object(engine, "_get_planning_agent", return_value=agent)
    mocker.patch.object(engine, "_call_agent_with_timeout", return_value=response)
    mocker.patch(
        "backend.business.rag_engine.agentic.engine.extract_sources_from_agent",
        return_value=[{"text": "证据片段", "score": 0.88, "metadata": {"file_name": "evidence.md"}}],
    )
    mocker.patch(
        "backend.business.rag_engine.agentic.engine.extract_reasoning_from_agent",
        return_value="先检索，再综合。",
    )

    answer, sources, reasoning, trace_info = engine.query("研究问题", collect_trace=True)

    assert answer == "格式化后的回答"
    assert len(sources) == 1
    assert reasoning == "先检索，再综合。"
    assert trace_info is not None
    assert trace_info["research"]["current_judgment"] == "阶段性判断已经形成"
    assert trace_info["research"]["supporting_evidence"][0]["file_name"] == "evidence.md"
    assert trace_info["research"]["recommended_action"] == "synthesize_answer"
