"""Pydantic request/response models for the API layer."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Config ────────────────────────────────────────────

class AppConfigResponse(BaseModel):
    selected_model: str
    llm_preset: str
    retrieval_strategy: str
    similarity_top_k: int
    similarity_threshold: float
    enable_rerank: bool
    show_reasoning: bool


class ModelInfo(BaseModel):
    id: str
    name: str
    supports_reasoning: bool = False


# ── Health ────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str  # "ready" | "initializing" | "error"
    message: str = ""
    progress: Optional[dict[str, Any]] = None
