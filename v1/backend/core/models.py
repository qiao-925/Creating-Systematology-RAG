"""Core Systematology MVP models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from llama_index.core import Document
from pydantic import BaseModel, ConfigDict, Field


class ParsedQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_text: str
    documents: list[Document] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)


class CLDNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    label: str
    description: str | None = None


class CausalLink(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    target: str
    relation: Literal["influences", "causes", "enables", "inhibits", "supports", "requires"] = "influences"


class SharedCLD(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[CLDNode]
    edges: list[CausalLink]
    metadata: dict[str, Any] = Field(default_factory=dict)


class WeightedFCM(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weight_matrix: list[list[float]]
    confidence_matrix: list[list[float]]
    baseline_state: list[float]
    intervention_states: dict[str, list[float]] = Field(default_factory=dict)


class NodeImpact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node: str
    impact_score: float
    confidence: Literal["high", "medium", "low"]
    affected_nodes: list[str] = Field(default_factory=list)


class LeverageAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    leverage_points: list[NodeImpact]
    uncertainty_ranges: dict[str, tuple[float, float]] = Field(default_factory=dict)


class StructuredReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cld_visualization: dict[str, Any]
    scenario_comparison: dict[str, Any] | None = None
    leverage_ranking: list[dict[str, Any]] | None = None
    synthesized_insights: str
    evidence_tracing: dict[str, Any] = Field(default_factory=dict)


class StructuredFailureReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    stage: str
    reason: str
    details: dict[str, Any] = Field(default_factory=dict)


@dataclass(slots=True)
class FailureRecord:
    stage: str
    reason: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RunContext:
    run_id: str = field(default_factory=lambda: str(uuid4()))
    budget_turns: int = 10
    current_turn: int = 0
    budget_tokens: int = 100_000
    tokens_used: int = 0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tool_calls: list[str] = field(default_factory=list)
    failures: list[FailureRecord] = field(default_factory=list)
    self_review_passed: bool = False
    # Intermediate results cache — avoids relying on LLM to pass large JSON
    cached_cld: SharedCLD | None = None
    cached_fcm: WeightedFCM | None = None
    cached_leverage: LeverageAnalysis | None = None


class Scenario(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    interventions: dict[str, float] = Field(default_factory=dict)


class SimConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_iterations: int = 100
    convergence_threshold: float = 1e-6
