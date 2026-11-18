"""Tests for the LlamaIndex Instrumentation-based observability."""

import time
from unittest.mock import patch

import pytest
from llama_index.core.instrumentation import get_dispatcher
from llama_index.core.instrumentation.events.llm import (
    LLMChatEndEvent,
    LLMChatStartEvent,
)
from llama_index.core.instrumentation.events.retrieval import (
    RetrievalEndEvent,
    RetrievalStartEvent,
)

from backend.infrastructure.observers.instrumentation import (
    ObservabilityEventHandler,
    ObservabilitySpanHandler,
)


class TestObservabilityEventHandler:
    """Test event handler dispatches correctly."""

    def setup_method(self):
        self.handler = ObservabilityEventHandler()

    def test_class_name(self):
        assert self.handler.class_name() == "ObservabilityEventHandler"

    def test_handle_llm_start_event(self):
        event = LLMChatStartEvent(
            messages=[],
            additional_kwargs={},
            model_dict={"model": "deepseek-chat"},
        )
        with patch("backend.infrastructure.observers.instrumentation.logger") as mock_log:
            self.handler.handle(event)
            mock_log.info.assert_called_once()
            call_args = mock_log.info.call_args
            assert call_args[0][0] == "llm_call_start"
            assert call_args[1]["model"] == "deepseek-chat"

    def test_handle_retrieval_start_event(self):
        event = RetrievalStartEvent(str_or_query_bundle="test query")
        with patch("backend.infrastructure.observers.instrumentation.logger") as mock_log:
            self.handler.handle(event)
            mock_log.info.assert_called_once()
            call_args = mock_log.info.call_args
            assert call_args[0][0] == "retrieval_start"
            assert "test query" in call_args[1]["query"]

    def test_handle_retrieval_end_event(self):
        event = RetrievalEndEvent(str_or_query_bundle="test query", nodes=[])
        with patch("backend.infrastructure.observers.instrumentation.logger") as mock_log:
            self.handler.handle(event)
            mock_log.info.assert_called_once()
            call_args = mock_log.info.call_args
            assert call_args[0][0] == "retrieval_end"
            assert call_args[1]["node_count"] == 0


class TestObservabilitySpanHandler:
    """Test span lifecycle tracking."""

    def setup_method(self):
        self.handler = ObservabilitySpanHandler()

    def test_class_name(self):
        assert self.handler.class_name() == "ObservabilitySpanHandler"

    def test_span_lifecycle(self):
        """Test span enter → exit logs duration."""
        import inspect
        dummy_args = inspect.signature(lambda: None).bind()

        span = self.handler.new_span(id_="s1", bound_args=dummy_args, parent_span_id=None)
        assert span is not None

        self.handler.span_enter(id_="s1", bound_args=dummy_args)
        assert "s1" in self.handler._open_spans

        time.sleep(0.01)

        with patch("backend.infrastructure.observers.instrumentation.logger") as mock_log:
            self.handler.prepare_to_exit_span(id_="s1", bound_args=dummy_args)
            mock_log.debug.assert_called_once()
            call_args = mock_log.debug.call_args
            assert call_args[0][0] == "span_exit"
            assert call_args[1]["duration_ms"] >= 5  # at least some time passed

        assert "s1" not in self.handler._open_spans

    def test_span_drop_on_error(self):
        """Test span drop logs warning with error."""
        import inspect
        dummy_args = inspect.signature(lambda: None).bind()

        self.handler.span_enter(id_="s2", bound_args=dummy_args)

        with patch("backend.infrastructure.observers.instrumentation.logger") as mock_log:
            self.handler.prepare_to_drop_span(
                id_="s2", bound_args=dummy_args, err=ValueError("test error")
            )
            mock_log.warning.assert_called_once()
            call_args = mock_log.warning.call_args
            assert call_args[0][0] == "span_drop"
            assert "test error" in call_args[1]["error"]


class TestEnableInstrumentation:
    """Test the setup function."""

    def test_enable_is_idempotent(self):
        from backend.infrastructure.observers import setup
        # Reset state for clean test
        setup._initialized = False
        result1 = setup.enable_instrumentation()
        assert result1 is True
        result2 = setup.enable_instrumentation()
        assert result2 is False
        # Cleanup
        setup._initialized = False
