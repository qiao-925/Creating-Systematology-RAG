"""CLDFlow test fixtures: golden examples and mock helpers.

Golden example: Fiscal subsidy policy analysis (D12 decision).
"""

from __future__ import annotations

from typing import Any

from backend.core.models import (
    CausalLink,
    CLDNode,
    LeverageAnalysis,
    NodeImpact,
    RunContext,
    SharedCLD,
    WeightedFCM,
)


# === Golden Example: Fiscal Subsidy Policy ===

def make_golden_shared_cld() -> SharedCLD:
    """Golden SharedCLD: fiscal subsidy → housing market → economic growth."""
    return SharedCLD(
        nodes=[
            CLDNode(id="n_subsidy", label="fiscal subsidy", description="Government fiscal subsidy policy"),
            CLDNode(id="n_demand", label="housing demand", description="Consumer demand for housing"),
            CLDNode(id="n_price", label="housing price", description="Average housing market price"),
            CLDNode(id="n_supply", label="housing supply", description="New housing construction"),
            CLDNode(id="n_growth", label="economic growth", description="GDP growth rate"),
            CLDNode(id="n_inflation", label="inflation", description="Consumer price index change"),
        ],
        edges=[
            CausalLink(source="n_subsidy", target="n_demand", relation="causes"),
            CausalLink(source="n_demand", target="n_price", relation="causes"),
            CausalLink(source="n_price", target="n_supply", relation="enables"),
            CausalLink(source="n_supply", target="n_growth", relation="supports"),
            CausalLink(source="n_growth", target="n_inflation", relation="influences"),
            CausalLink(source="n_subsidy", target="n_growth", relation="supports"),
            CausalLink(source="n_inflation", target="n_demand", relation="inhibits"),
        ],
        metadata={"scenario": "fiscal_subsidy", "source": "golden_example"},
    )


def make_golden_weighted_fcm() -> WeightedFCM:
    """Golden WeightedFCM matching the fiscal subsidy CLD."""
    return WeightedFCM(
        weight_matrix=[
            #  subsidy  demand  price  supply  growth  inflation
            [0.0,  0.7,  0.0,  0.0,  0.5,  0.0],   # subsidy
            [0.0,  0.0,  0.7,  0.0,  0.0,  0.0],   # demand
            [0.0,  0.0,  0.0,  0.5,  0.0,  0.0],   # price
            [0.0,  0.0,  0.0,  0.0,  0.5,  0.0],   # supply
            [0.0,  0.0,  0.0,  0.0,  0.0,  0.5],   # growth
            [0.0, -0.7,  0.0,  0.0,  0.0,  0.0],   # inflation
        ],
        confidence_matrix=[
            [0.0, 0.7, 0.0, 0.0, 0.6, 0.0],
            [0.0, 0.0, 0.7, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.6, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.6, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.6],
            [0.0, 0.7, 0.0, 0.0, 0.0, 0.0],
        ],
        baseline_state=[0.5, 0.3, 0.4, 0.2, 0.3, 0.1],
    )


def make_golden_leverage_analysis() -> LeverageAnalysis:
    """Golden LeverageAnalysis for the fiscal subsidy scenario."""
    return LeverageAnalysis(
        leverage_points=[
            NodeImpact(node="fiscal subsidy", impact_score=0.85, confidence="high", affected_nodes=["housing demand", "economic growth"]),
            NodeImpact(node="housing demand", impact_score=0.72, confidence="medium", affected_nodes=["housing price"]),
            NodeImpact(node="housing price", impact_score=0.55, confidence="medium", affected_nodes=["housing supply"]),
            NodeImpact(node="economic growth", impact_score=0.45, confidence="medium", affected_nodes=["inflation"]),
            NodeImpact(node="housing supply", impact_score=0.38, confidence="low", affected_nodes=["economic growth"]),
            NodeImpact(node="inflation", impact_score=0.32, confidence="low", affected_nodes=["housing demand"]),
        ],
        uncertainty_ranges={
            "fiscal subsidy": (0.76, 0.94),
            "housing demand": (0.50, 0.94),
            "housing price": (0.38, 0.72),
            "economic growth": (0.31, 0.59),
            "housing supply": (0.27, 0.49),
            "inflation": (0.22, 0.42),
        },
    )


def make_run_context() -> RunContext:
    """Create a test RunContext."""
    return RunContext(
        run_id="test-run-001",
        budget_turns=10,
        budget_tokens=100_000,
    )


# === Mock LLM ===

class MockLLM:
    """Mock LLM that returns predefined responses."""

    def __init__(self, responses: dict[str, str] | None = None):
        self.responses = responses or {}
        self.default_response = '{"approved": true, "quality_score": 0.7, "issues": [], "suggestions": [], "reasoning": "mock"}'
        self._calls: list[str] = []

    async def acomplete(self, prompt: str, **kwargs: Any) -> Any:
        self._calls.append(prompt[:100])
        response_text = self.default_response
        for key, val in self.responses.items():
            if key in prompt:
                response_text = val
                break
        return MockCompletion(text=response_text)

    def complete(self, prompt: str, **kwargs: Any) -> Any:
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self.acomplete(prompt, **kwargs))


class MockCompletion:
    """Mock LLM completion response."""
    def __init__(self, text: str):
        self.text = text


# === Specialist Output Fixtures ===

def make_specialist_outputs() -> list[dict[str, Any]]:
    """Mock specialist outputs for testing merge/conflict."""
    return [
        {
            "perspective_id": "econ_001",
            "perspective_name": "Economist",
            "nodes": [
                {"id": "n1", "label": "subsidy", "description": "fiscal subsidy"},
                {"id": "n2", "label": "demand", "description": "consumer demand"},
                {"id": "n3", "label": "price", "description": "market price"},
            ],
            "links": [
                {"source": "n1", "target": "n2", "relation": "causes"},
                {"source": "n2", "target": "n3", "relation": "causes"},
            ],
        },
        {
            "perspective_id": "social_001",
            "perspective_name": "Sociologist",
            "nodes": [
                {"id": "n1", "label": "government_subsidy", "description": "gov fiscal policy"},
                {"id": "n2", "label": "market_demand", "description": "aggregate demand"},
                {"id": "n4", "label": "equity", "description": "social equity"},
            ],
            "links": [
                {"source": "n1", "target": "n2", "relation": "influences"},
                {"source": "n2", "target": "n4", "relation": "supports"},
            ],
        },
    ]
