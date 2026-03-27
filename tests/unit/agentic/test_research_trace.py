from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

from backend.business.rag_engine.agentic.engine import AgenticQueryEngine
from backend.business.rag_engine.agentic.research_trace import (
    build_research_trace,
    extract_research_decision,
    extract_research_decision_with_trace,
)


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
    assert research["open_tensions_source"] == "heuristic_fallback"
    assert research["stop_reason"] == "evidence_sufficient_for_now"
    assert research["recommended_action"] == "synthesize_answer"
    assert research["next_question_source"] == "heuristic_fallback"
    assert research["has_reasoning_trace"] is True
    assert research["decision_source"] == "heuristic_fallback"
    assert research["decision_parse_status"] == "missing"
    assert research["decision_fields_present"] == []


def test_build_research_trace_without_evidence():
    research = build_research_trace(
        question="钱学森如何定义综合集成方法？",
        answer="目前还不能给出稳定回答。",
        sources=[],
        reasoning_content=None,
    )

    assert research["supporting_evidence"] == []
    assert research["open_tensions"] == ["当前回答缺少可核实来源，无法支撑阶段性判断。"]
    assert research["open_tensions_source"] == "heuristic_fallback"
    assert research["stop_reason"] == "insufficient_evidence"
    assert research["recommended_action"] == "stop_due_to_insufficient_evidence"
    assert "还缺少哪些一手材料或文档" in research["next_question"]
    assert research["next_question_source"] == "heuristic_fallback"
    assert research["decision_source"] == "heuristic_fallback"


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
    assert research["open_tensions_source"] == "heuristic_fallback"
    assert research["stop_reason"] == "needs_more_evidence"
    assert research["recommended_action"] == "continue_gathering_evidence"
    assert "下一步应补什么证据" in research["next_question"]
    assert research["next_question_source"] == "heuristic_fallback"
    assert research["decision_parse_status"] == "missing"


def test_extract_research_decision_strips_block_and_parses_json():
    answer = """阶段性判断已经形成。

<research_decision>
{"recommended_action":"synthesize_answer","stop_reason":"evidence_sufficient_for_now","open_tensions":[],"next_question":"是否存在反例？"}
</research_decision>
"""

    cleaned_answer, decision = extract_research_decision(answer)

    assert cleaned_answer == "阶段性判断已经形成。"
    assert decision == {
        "recommended_action": "synthesize_answer",
        "stop_reason": "evidence_sufficient_for_now",
        "open_tensions": [],
        "next_question": "是否存在反例？",
    }


def test_extract_research_decision_parses_markdown_wrapped_json():
    answer = """阶段性判断已经形成。

<research_decision>
```json
{"recommended_action":"continue_gathering_evidence","stop_reason":"needs_more_evidence","open_tensions":["定义边界仍不清晰"],"next_question":"还缺哪些边界定义？"}
```
</research_decision>
"""

    cleaned_answer, decision = extract_research_decision(answer)

    assert cleaned_answer == "阶段性判断已经形成。"
    assert decision == {
        "recommended_action": "continue_gathering_evidence",
        "stop_reason": "needs_more_evidence",
        "open_tensions": ["定义边界仍不清晰"],
        "next_question": "还缺哪些边界定义？",
    }


def test_extract_research_decision_with_trace_reports_invalid_json():
    answer = """阶段性判断已经形成。

<research_decision>
{"recommended_action":"synthesize_answer",
</research_decision>
"""

    cleaned_answer, decision, decision_trace = extract_research_decision_with_trace(answer)

    assert cleaned_answer == "阶段性判断已经形成。"
    assert decision is None
    assert decision_trace == {
        "decision_source": "heuristic_fallback",
        "decision_parse_status": "invalid_json",
        "decision_fields_present": [],
    }


def test_extract_research_decision_repairs_inconsistent_action_and_stop_reason():
    answer = """阶段性判断已经形成。

<research_decision>
{"recommended_action":"continue_gathering_evidence","stop_reason":"evidence_sufficient_for_now","open_tensions":[],"next_question":"还缺哪些边界定义？"}
</research_decision>
"""

    cleaned_answer, decision = extract_research_decision(answer)

    assert cleaned_answer == "阶段性判断已经形成。"
    assert decision == {
        "recommended_action": "continue_gathering_evidence",
        "stop_reason": "needs_more_evidence",
        "open_tensions": [],
        "next_question": "还缺哪些边界定义？",
    }


def test_build_research_trace_prefers_explicit_research_decision():
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
        research_decision={
            "recommended_action": "stop_due_to_insufficient_evidence",
            "open_tensions": ["现有资料缺少系统工程边界的一手定义"],
            "next_question": "还需要补哪些一手定义，才能比较两者边界？",
        },
    )

    assert research["open_tensions"] == ["现有资料缺少系统工程边界的一手定义"]
    assert research["open_tensions_source"] == "structured_output"
    assert research["stop_reason"] == "insufficient_evidence"
    assert research["recommended_action"] == "stop_due_to_insufficient_evidence"
    assert research["next_question"] == "还需要补哪些一手定义，才能比较两者边界？"
    assert research["next_question_source"] == "structured_output"
    assert research["decision_source"] == "structured_output"
    assert research["decision_parse_status"] == "provided_directly"
    assert research["decision_fields_present"] == [
        "next_question",
        "open_tensions",
        "recommended_action",
        "stop_reason",
    ]


def test_build_research_trace_respects_explicit_empty_open_tensions():
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
        research_decision={
            "recommended_action": "synthesize_answer",
            "stop_reason": "evidence_sufficient_for_now",
            "open_tensions": [],
            "next_question": "是否还存在会推翻当前判断的反例？",
        },
    )

    assert research["open_tensions"] == []
    assert research["open_tensions_source"] == "structured_output"
    assert research["stop_reason"] == "evidence_sufficient_for_now"
    assert research["recommended_action"] == "synthesize_answer"
    assert research["next_question"] == "是否还存在会推翻当前判断的反例？"
    assert research["next_question_source"] == "structured_output"
    assert research["decision_source"] == "structured_output"


def test_build_research_trace_backfills_tensions_for_continue_action_without_explicit_tensions():
    research = build_research_trace(
        question="系统工程与运筹学的边界是什么？",
        answer="当前阶段形成了初步判断。",
        sources=[
            {
                "text": "系统工程与运筹学都涉及优化与决策。",
                "score": 0.82,
                "metadata": {"file_name": "comparison.md"},
            }
        ],
        research_decision={
            "recommended_action": "continue_gathering_evidence",
            "stop_reason": "needs_more_evidence",
            "open_tensions": [],
            "next_question": "还需要补哪些边界案例？",
        },
    )

    assert research["open_tensions"] == ["当前判断仍存在关键张力，需要继续补证据。"]
    assert research["open_tensions_source"] == "heuristic_fallback"
    assert research["stop_reason"] == "needs_more_evidence"
    assert research["recommended_action"] == "continue_gathering_evidence"
    assert research["next_question"] == "还需要补哪些边界案例？"
    assert research["next_question_source"] == "structured_output"


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
    response.__str__ = Mock(
        return_value=(
            "阶段性判断已经形成。\n\n"
            "<research_decision>"
            '{"recommended_action":"continue_gathering_evidence","stop_reason":"needs_more_evidence",'
            '"open_tensions":["还缺少跨时期案例"],"next_question":"下一步该补哪些跨时期案例？"}'
            "</research_decision>"
        )
    )

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
    engine.formatter.format.assert_called_once_with("阶段性判断已经形成。", sources)
    assert trace_info is not None
    assert trace_info["research"]["current_judgment"] == "阶段性判断已经形成"
    assert trace_info["research"]["supporting_evidence"][0]["file_name"] == "evidence.md"
    assert trace_info["research"]["recommended_action"] == "continue_gathering_evidence"
    assert trace_info["research"]["open_tensions"] == ["还缺少跨时期案例"]
    assert trace_info["research"]["open_tensions_source"] == "structured_output"
    assert trace_info["research"]["decision_source"] == "structured_output"
    assert trace_info["research"]["decision_parse_status"] == "parsed"
    assert trace_info["research"]["decision_fields_present"] == [
        "next_question",
        "open_tensions",
        "recommended_action",
        "stop_reason",
    ]
    assert trace_info["research"]["next_question_source"] == "structured_output"
