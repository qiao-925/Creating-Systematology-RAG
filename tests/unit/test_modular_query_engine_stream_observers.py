"""
ModularQueryEngine.stream_query 的观测回调集成测试
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock

import pytest

from backend.business.rag_engine.core.engine import ModularQueryEngine


class _DummyObserverManager:
    def __init__(self) -> None:
        self.starts: List[Tuple[str, Dict[str, Any]]] = []
        self.ends: List[Tuple[str, str, List[dict], Optional[Dict[str, str]], Dict[str, Any]]] = []

    def on_query_start(self, query: str, **kwargs) -> Dict[str, Optional[str]]:
        self.starts.append((query, kwargs))
        return {"dummy": "trace"}

    def on_query_end(
        self,
        query: str,
        answer: str,
        sources: List[dict],
        trace_ids: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> None:
        self.ends.append((query, answer, sources, trace_ids, kwargs))


@pytest.mark.fast
def test_stream_query_calls_observers(monkeypatch):
    engine = ModularQueryEngine.__new__(ModularQueryEngine)
    engine.query_processor = MagicMock()
    engine.query_processor.process.return_value = {
        "original_query": "orig",
        "final_query": "final",
        "understanding": None,
        "rewritten_queries": ["final"],
        "processing_method": "simple",
    }
    engine.llm = object()
    engine.formatter = object()
    engine.retriever = object()
    engine.postprocessors = []
    engine.query_router = None
    engine.enable_auto_routing = False
    engine.retrieval_strategy = "vector"
    engine.similarity_top_k = 3
    engine.observer_manager = _DummyObserverManager()

    expected_sources = [{"index": 1, "text": "ctx", "score": 0.1, "metadata": {}}]

    async def fake_execute_stream_query(*_args, **_kwargs):
        yield {"type": "token", "data": "h"}
        yield {"type": "token", "data": "i"}
        yield {"type": "sources", "data": expected_sources}
        yield {"type": "reasoning", "data": "reason"}
        yield {
            "type": "done",
            "data": {"answer": "HI", "sources": expected_sources, "reasoning_content": "reason"},
        }

    monkeypatch.setattr(
        "backend.business.rag_engine.core.engine.execute_stream_query",
        fake_execute_stream_query,
    )

    async def _run():
        chunks = []
        async for chunk in engine.stream_query("orig"):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(_run())

    assert len(chunks) == 5
    assert engine.observer_manager.starts == [("final", {})]

    assert len(engine.observer_manager.ends) == 1
    end_query, end_answer, end_sources, end_trace_ids, end_kwargs = engine.observer_manager.ends[0]
    assert end_query == "final"
    assert end_answer == "HI"
    assert end_sources == expected_sources
    assert end_trace_ids == {"dummy": "trace"}
    assert end_kwargs["query_processing_result"]["original_query"] == "orig"
    assert end_kwargs["retrieval_strategy"] == "vector"
    assert end_kwargs["similarity_top_k"] == 3
    assert "retrieval_time" in end_kwargs


@pytest.mark.fast
def test_stream_query_error_still_calls_observer_end(monkeypatch):
    engine = ModularQueryEngine.__new__(ModularQueryEngine)
    engine.query_processor = MagicMock()
    engine.query_processor.process.return_value = {
        "original_query": "orig",
        "final_query": "final",
        "understanding": None,
        "rewritten_queries": ["final"],
        "processing_method": "simple",
    }
    engine.llm = object()
    engine.formatter = object()
    engine.retriever = object()
    engine.postprocessors = []
    engine.query_router = None
    engine.enable_auto_routing = False
    engine.retrieval_strategy = "vector"
    engine.similarity_top_k = 3
    engine.observer_manager = _DummyObserverManager()

    async def fake_execute_stream_query(*_args, **_kwargs):
        yield {"type": "error", "data": {"message": "boom"}}
        raise RuntimeError("boom")

    monkeypatch.setattr(
        "backend.business.rag_engine.core.engine.execute_stream_query",
        fake_execute_stream_query,
    )

    async def _run():
        async for _chunk in engine.stream_query("orig"):
            pass

    with pytest.raises(RuntimeError):
        asyncio.run(_run())

    assert engine.observer_manager.starts == [("final", {})]
    assert len(engine.observer_manager.ends) == 1
    end_query, end_answer, end_sources, end_trace_ids, end_kwargs = engine.observer_manager.ends[0]
    assert end_query == "final"
    assert end_answer == ""
    assert end_sources == []
    assert end_trace_ids == {"dummy": "trace"}
    assert "errors" in end_kwargs
    assert any("boom" in str(err) for err in end_kwargs["errors"])
