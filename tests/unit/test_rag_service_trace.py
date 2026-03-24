"""
RAGService 研究型 trace 透传回归测试。
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from backend.business.rag_api.rag_service import RAGService


@pytest.fixture
def mock_index_manager():
    with patch("backend.infrastructure.indexer.IndexManager") as mock:
        yield mock


@pytest.fixture
def mock_agentic_engine():
    with patch("backend.business.rag_engine.agentic.AgenticQueryEngine") as mock:
        yield mock


def make_source() -> dict:
    return {
        "text": "证据片段",
        "score": 0.92,
        "metadata": {"file_name": "evidence.md"},
        "file_name": "evidence.md",
    }


@pytest.mark.fast
class TestRAGServiceTrace:
    def test_collect_trace_preserves_research_trace_for_agentic_query(
        self,
        mock_index_manager,
        mock_agentic_engine,
    ):
        trace_info = {
            "research": {
                "current_judgment": "系统科学与系统工程在目标导向上已经分化。",
                "recommended_action": "continue_gathering_evidence",
            },
            "total_time": 1.23,
        }
        mock_agentic_engine.return_value.query.return_value = (
            "阶段性回答",
            [make_source()],
            "先检索，再综合。",
            trace_info,
        )

        service = RAGService(collection_name="research-test", use_agentic_rag=True)
        response = service.query(
            "为什么系统科学和系统工程会走向不同路径？",
            user_id="user-1",
            session_id="session-1",
            collect_trace=True,
        )

        assert response.metadata["trace_info"] == trace_info
        assert response.metadata["trace_info"]["research"]["recommended_action"] == "continue_gathering_evidence"
        assert response.metadata["reasoning_content"] == "先检索，再综合。"
        mock_agentic_engine.return_value.query.assert_called_once_with(
            "为什么系统科学和系统工程会走向不同路径？",
            collect_trace=True,
        )
        mock_index_manager.assert_called_once()

    def test_collect_trace_disabled_omits_trace_metadata(
        self,
        mock_index_manager,
        mock_agentic_engine,
    ):
        mock_agentic_engine.return_value.query.return_value = (
            "阶段性回答",
            [make_source()],
            "推理过程",
            {"research": {"current_judgment": "已有判断"}},
        )

        service = RAGService(collection_name="research-test", use_agentic_rag=True)
        response = service.query("研究问题", collect_trace=False)

        assert "trace_info" not in response.metadata
        assert response.metadata["reasoning_content"] == "推理过程"
        mock_agentic_engine.return_value.query.assert_called_once_with(
            "研究问题",
            collect_trace=False,
        )
        mock_index_manager.assert_called_once()
