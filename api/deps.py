"""Dependency injection for FastAPI routes.

Manages the lifecycle of RAGService, ChatManager and runtime config.
Initialised once during FastAPI lifespan; routes obtain singletons via
``get_rag_service()`` / ``get_app_state()``.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Optional

from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger("api.deps")


@dataclass
class RuntimeConfig:
    """Mutable runtime configuration (mirrors the old Streamlit session_state)."""

    selected_model: str = ""
    llm_preset: str = "balanced"
    retrieval_strategy: str = "vector"
    use_agentic_rag: bool = False
    similarity_top_k: int = 5
    similarity_threshold: float = 0.3
    enable_rerank: bool = False
    show_reasoning: bool = True
    research_mode: bool = False

    def apply_defaults(self) -> None:
        self.selected_model = self.selected_model or config.get_default_llm_id()
        self.retrieval_strategy = self.retrieval_strategy or config.RETRIEVAL_STRATEGY
        self.similarity_top_k = self.similarity_top_k or config.SIMILARITY_TOP_K
        self.similarity_threshold = self.similarity_threshold or config.SIMILARITY_THRESHOLD
        self.enable_rerank = config.ENABLE_RERANK
        self.show_reasoning = config.DEEPSEEK_ENABLE_REASONING_DISPLAY


@dataclass
class AppState:
    """Application-wide singleton state, populated during lifespan startup."""

    init_result: Optional[Any] = None
    rag_service: Optional[Any] = None
    chat_manager: Optional[Any] = None
    runtime_config: RuntimeConfig = field(default_factory=RuntimeConfig)
    ready: bool = False
    error: Optional[str] = None
    _lock: threading.Lock = field(default_factory=threading.Lock)

    # ── service rebuild ──────────────────────────────

    def rebuild_services(self) -> bool:
        """Rebuild RAGService + ChatManager from current runtime_config."""
        with self._lock:
            return self._rebuild_services_inner()

    def _rebuild_services_inner(self) -> bool:
        if self.init_result is None:
            logger.warning("init_result is None, cannot rebuild services")
            return False

        rc = self.runtime_config

        from frontend.components.config_panel.models import LLM_PRESETS

        preset = LLM_PRESETS.get(rc.llm_preset, LLM_PRESETS["balanced"])
        temperature = preset["temperature"]
        max_tokens = preset["max_tokens"]

        # Check if reasoning model → temperature fixed
        model_config = config.get_llm_model_config(rc.selected_model)
        if model_config and model_config.supports_reasoning:
            temperature = None  # reasoning models don't support temperature

        index_manager = self.init_result.instances.get("index_manager")

        def _get_shared_index_manager():
            existing = self.init_result.instances.get("index_manager")
            if existing is not None:
                return existing
            manager = getattr(self.init_result, "manager", None)
            if manager and manager.execute_init("index_manager"):
                shared = manager.instances.get("index_manager")
                if shared is not None:
                    self.init_result.instances["index_manager"] = shared
                return shared
            return None

        try:
            from backend.business.rag_api import RAGService
            from backend.business.chat import ChatManager

            collection_name = config.CHROMA_COLLECTION_NAME

            chat_manager = ChatManager(
                index_manager=index_manager,
                index_manager_provider=_get_shared_index_manager,
                user_email=None,
                enable_debug=False,
                enable_markdown_formatting=True,
                use_agentic_rag=rc.use_agentic_rag,
                model_id=rc.selected_model,
                retrieval_strategy=rc.retrieval_strategy,
                similarity_top_k=rc.similarity_top_k,
                similarity_threshold=rc.similarity_threshold,
                enable_rerank=rc.enable_rerank,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            rag_service = RAGService(
                collection_name=collection_name,
                enable_debug=False,
                enable_markdown_formatting=True,
                use_agentic_rag=rc.use_agentic_rag,
                model_id=rc.selected_model,
                retrieval_strategy=rc.retrieval_strategy,
                similarity_top_k=rc.similarity_top_k,
                similarity_threshold=rc.similarity_threshold,
                enable_rerank=rc.enable_rerank,
                index_manager=index_manager,
                chat_manager=chat_manager,
                index_manager_provider=_get_shared_index_manager,
            )

            self.rag_service = rag_service
            self.chat_manager = chat_manager
            logger.info("✅ Services rebuilt", model=rc.selected_model, strategy=rc.retrieval_strategy)
            return True

        except Exception as e:
            logger.error("❌ Service rebuild failed", error=str(e), exc_info=True)
            return False


# ── module-level singleton ───────────────────────────

_app_state: Optional[AppState] = None


def get_app_state() -> AppState:
    global _app_state
    if _app_state is None:
        _app_state = AppState()
    return _app_state


def get_rag_service():
    """Return the current RAGService or raise if not ready."""
    state = get_app_state()
    if not state.ready or state.rag_service is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Service not ready")
    return state.rag_service
