"""Pydantic request/response models for the API layer."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Chat ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None


# ── Research ──────────────────────────────────────────

class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=1)


class ResearchResponse(BaseModel):
    judgment: str = ""
    evidence: list[dict[str, Any]] = []
    confidence: str = "low"
    tensions: list[str] = []
    next_questions: list[str] = []


# ── Config ────────────────────────────────────────────

class AppConfigResponse(BaseModel):
    selected_model: str
    llm_preset: str
    retrieval_strategy: str
    use_agentic_rag: bool
    similarity_top_k: int
    similarity_threshold: float
    enable_rerank: bool
    show_reasoning: bool
    research_mode: bool


class AppConfigUpdate(BaseModel):
    selected_model: Optional[str] = None
    llm_preset: Optional[str] = None
    retrieval_strategy: Optional[str] = None
    use_agentic_rag: Optional[bool] = None
    similarity_top_k: Optional[int] = None
    similarity_threshold: Optional[float] = None
    enable_rerank: Optional[bool] = None
    show_reasoning: Optional[bool] = None
    research_mode: Optional[bool] = None


class ModelInfo(BaseModel):
    id: str
    name: str
    supports_reasoning: bool = False


# ── Health ────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str  # "ready" | "initializing" | "error"
    message: str = ""
    progress: Optional[dict[str, Any]] = None
