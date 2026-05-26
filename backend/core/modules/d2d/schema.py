"""Systematology MVP D2D schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.core.models import LeverageAnalysis, SharedCLD


class D2DAnalysisInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shared_cld: SharedCLD
    variable_types: dict[str, Literal["stock", "flow", "auxiliary", "constant"]] = Field(default_factory=dict)
    perturbation_pct: float = Field(default=0.1, gt=0, le=1)


class D2DAnalysisOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    leverage_analysis: LeverageAnalysis
    diagnostics: dict[str, Any] = Field(default_factory=dict)
