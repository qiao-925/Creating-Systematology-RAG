"""CLDFlow MVP FCM schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from backend.core.models import Scenario, SharedCLD, SimConfig, WeightedFCM


class FCMAnalysisInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shared_cld: SharedCLD
    intervention_scenarios: list[Scenario] | None = None
    simulation_config: SimConfig | None = None


class FCMAnalysisOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weighted_fcm: WeightedFCM
    diagnostics: dict[str, Any] = Field(default_factory=dict)
