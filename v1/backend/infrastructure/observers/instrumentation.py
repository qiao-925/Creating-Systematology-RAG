"""
LlamaIndex Instrumentation-based observability.

Replaces the old LlamaDebugHandler callback approach with the modern
Instrumentation API (llama-index-instrumentation 0.4+).

Captures:
  - LLM calls (model, messages, tokens, duration)
  - Retrieval operations (query, node count, duration)
  - Synthesis operations (query, response length, duration)
  - Query lifecycle (full end-to-end)
  - Span hierarchy (parent-child timing)
"""

import time
from typing import Any, Dict, Optional

from llama_index.core.instrumentation.event_handlers import BaseEventHandler
from llama_index.core.instrumentation.events import BaseEvent
from llama_index.core.instrumentation.events.llm import (
    LLMChatEndEvent,
    LLMChatStartEvent,
)
from llama_index.core.instrumentation.events.query import (
    QueryEndEvent,
    QueryStartEvent,
)
from llama_index.core.instrumentation.events.retrieval import (
    RetrievalEndEvent,
    RetrievalStartEvent,
)
from llama_index.core.instrumentation.events.synthesis import (
    SynthesizeEndEvent,
    SynthesizeStartEvent,
)
from llama_index.core.instrumentation.span.base import BaseSpan
from llama_index.core.instrumentation.span_handlers import BaseSpanHandler

from backend.infrastructure.logger import get_logger

logger = get_logger("instrumentation")


class ObservabilityEventHandler(BaseEventHandler):
    """Structured event handler for all LlamaIndex operations."""

    @classmethod
    def class_name(cls) -> str:
        return "ObservabilityEventHandler"

    def handle(self, event: BaseEvent, **kwargs: Any) -> None:
        """Route events to type-specific handlers."""
        # LLM events
        if isinstance(event, LLMChatStartEvent):
            self._on_llm_start(event)
        elif isinstance(event, LLMChatEndEvent):
            self._on_llm_end(event)
        # Retrieval events
        elif isinstance(event, RetrievalStartEvent):
            self._on_retrieval_start(event)
        elif isinstance(event, RetrievalEndEvent):
            self._on_retrieval_end(event)
        # Synthesis events
        elif isinstance(event, SynthesizeStartEvent):
            self._on_synthesis_start(event)
        elif isinstance(event, SynthesizeEndEvent):
            self._on_synthesis_end(event)
        # Query events
        elif isinstance(event, QueryStartEvent):
            self._on_query_start(event)
        elif isinstance(event, QueryEndEvent):
            self._on_query_end(event)

    def _on_llm_start(self, event: LLMChatStartEvent) -> None:
        model = event.model_dict.get("model", "unknown") if event.model_dict else "unknown"
        msg_count = len(event.messages) if event.messages else 0
        logger.info(
            "llm_call_start",
            span_id=event.span_id,
            model=model,
            message_count=msg_count,
        )

    def _on_llm_end(self, event: LLMChatEndEvent) -> None:
        resp = event.response
        token_info = {}
        if hasattr(resp, "raw") and resp.raw:
            usage = getattr(resp.raw, "usage", None)
            if usage:
                token_info = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", None),
                    "completion_tokens": getattr(usage, "completion_tokens", None),
                    "total_tokens": getattr(usage, "total_tokens", None),
                }
        logger.info(
            "llm_call_end",
            span_id=event.span_id,
            **token_info,
        )

    def _on_retrieval_start(self, event: RetrievalStartEvent) -> None:
        query = str(event.str_or_query_bundle)[:200]
        logger.info("retrieval_start", span_id=event.span_id, query=query)

    def _on_retrieval_end(self, event: RetrievalEndEvent) -> None:
        node_count = len(event.nodes) if event.nodes else 0
        scores = []
        if event.nodes:
            scores = [round(n.score, 4) for n in event.nodes[:5] if n.score is not None]
        logger.info(
            "retrieval_end",
            span_id=event.span_id,
            node_count=node_count,
            top_scores=scores,
        )

    def _on_synthesis_start(self, event: SynthesizeStartEvent) -> None:
        query = str(event.query)[:200] if event.query else ""
        logger.info("synthesis_start", span_id=event.span_id, query=query)

    def _on_synthesis_end(self, event: SynthesizeEndEvent) -> None:
        resp_len = len(str(event.response)) if event.response else 0
        logger.info("synthesis_end", span_id=event.span_id, response_length=resp_len)

    def _on_query_start(self, event: QueryStartEvent) -> None:
        query = str(event.query)[:200] if event.query else ""
        logger.info("query_start", span_id=event.span_id, query=query)

    def _on_query_end(self, event: QueryEndEvent) -> None:
        resp_len = len(str(event.response)) if event.response else 0
        logger.info("query_end", span_id=event.span_id, response_length=resp_len)


class ObservabilitySpanHandler(BaseSpanHandler[BaseSpan]):
    """Tracks span timing and hierarchy."""

    _open_spans: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def class_name(cls) -> str:
        return "ObservabilitySpanHandler"

    def new_span(
        self,
        id_: str,
        bound_args: Any,
        instance: Optional[Any] = None,
        parent_span_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Optional[BaseSpan]:
        return BaseSpan(id_=id_, parent_id=parent_span_id)

    def span_enter(
        self,
        id_: str,
        bound_args: Any,
        instance: Optional[Any] = None,
        parent_id: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        self._open_spans[id_] = {
            "start": time.monotonic(),
            "parent_id": parent_id,
            "instance_type": type(instance).__name__ if instance else None,
        }

    def prepare_to_exit_span(
        self,
        id_: str,
        bound_args: Any,
        instance: Optional[Any] = None,
        result: Optional[Any] = None,
        **kwargs: Any,
    ) -> Optional[BaseSpan]:
        span_data = self._open_spans.pop(id_, None)
        if span_data:
            duration_ms = round((time.monotonic() - span_data["start"]) * 1000, 1)
            logger.debug(
                "span_exit",
                span_id=id_,
                parent_id=span_data.get("parent_id"),
                instance_type=span_data.get("instance_type"),
                duration_ms=duration_ms,
            )
        return None

    def prepare_to_drop_span(
        self,
        id_: str,
        bound_args: Any,
        instance: Optional[Any] = None,
        err: Optional[BaseException] = None,
        **kwargs: Any,
    ) -> Optional[BaseSpan]:
        span_data = self._open_spans.pop(id_, None)
        if span_data:
            duration_ms = round((time.monotonic() - span_data["start"]) * 1000, 1)
            logger.warning(
                "span_drop",
                span_id=id_,
                error=str(err) if err else None,
                duration_ms=duration_ms,
            )
        return None
