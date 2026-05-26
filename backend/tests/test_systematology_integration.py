"""Systematology integration tests: end-to-end pipeline verification."""

from __future__ import annotations

import pytest

from backend.core.models import (
    CausalLink,
    CLDNode,
    RunContext,
    SharedCLD,
    WeightedFCM,
)
from backend.core.modules.fcm.mapper import map_weights
from backend.core.modules.fcm.simulator import run_simulation, run_scenario_comparison
from backend.core.modules.d2d.sensitivity import compute_sensitivity
from backend.core.modules.d2d.ranking import rank_leverage_points
from backend.core.modules.d2d.uncertainty import compute_uncertainty_ranges
from backend.core.reporting.reporting import synthesize_report
from backend.core.service import SystematologyAppService
from tests.fixtures.systematology_fixtures import (
    make_golden_shared_cld,
    make_golden_weighted_fcm,
    make_run_context,
)


# =====================================================================
# Pipeline Integration Tests
# =====================================================================

class TestSystematologyPipeline:
    """Test the full CLD → FCM → D2D → Report pipeline."""

    def test_full_pipeline_with_golden_cld(self):
        """End-to-end: CLD → FCM → D2D → Report."""
        cld = make_golden_shared_cld()
        ctx = make_run_context()

        # FCM
        weighted_fcm = map_weights(cld)
        assert len(weighted_fcm.weight_matrix) == 6
        final_state = run_simulation(weighted_fcm)
        assert len(final_state) == 6

        # D2D
        sensitivity = compute_sensitivity(cld)
        ranges = compute_uncertainty_ranges(cld, weighted_fcm, sensitivity)
        leverage = rank_leverage_points(sensitivity, cld, ranges)

        # Report
        report = synthesize_report(ctx, cld, weighted_fcm, leverage)
        assert report.cld_visualization
        assert report.scenario_comparison
        assert report.leverage_ranking
        assert report.synthesized_insights
        assert report.evidence_tracing["run_id"] == ctx.run_id

    def test_service_happy_path(self):
        """SystematologyAppService happy path still works after refactor."""
        service = SystematologyAppService()
        parsed = service.parse_query("How does fiscal subsidy affect housing?")
        ctx = service.create_run_context()
        cld = service.build_shared_cld(parsed)
        fcm = service.build_weighted_fcm(cld)
        leverage = service.build_leverage_analysis(cld)
        report = synthesize_report(ctx, cld, fcm, leverage)
        assert report.synthesized_insights

    def test_pipeline_with_empty_cld(self):
        """Pipeline handles minimal CLD gracefully."""
        cld = SharedCLD(
            nodes=[CLDNode(id="a", label="A"), CLDNode(id="b", label="B")],
            edges=[CausalLink(source="a", target="b")],
        )
        ctx = RunContext()

        fcm = map_weights(cld)
        state = run_simulation(fcm)
        assert len(state) == 2

        sensitivity = compute_sensitivity(cld)
        leverage = rank_leverage_points(sensitivity, cld)
        report = synthesize_report(ctx, cld, fcm, leverage)
        assert report

    def test_pipeline_failure_report(self):
        """Failure report generation works."""
        from backend.core.models import StructuredFailureReport

        service = SystematologyAppService()
        ctx = service.create_run_context()
        failure = service.fail(ctx, "test_stage", "test_reason", detail="test")
        assert isinstance(failure, StructuredFailureReport)
        assert failure.stage == "test_stage"
        assert len(ctx.failures) == 1


# =====================================================================
# FCM Simulation Integration
# =====================================================================

class TestFCMIntegration:
    def test_simulation_propagation(self):
        """Verify signal propagates through the graph."""
        cld = make_golden_shared_cld()
        fcm = map_weights(cld)

        # Set subsidy to maximum
        initial = [0.0] * 6
        initial[0] = 1.0  # subsidy
        result = run_simulation(fcm, initial_state=initial)

        # Subsidy is connected to demand and growth, so they should be activated
        assert result[1] > 0.0  # demand
        assert result[4] > 0.0  # growth

    def test_scenario_comparison_produces_valid_results(self):
        """Scenario comparison produces valid, bounded results."""
        cld = make_golden_shared_cld()
        fcm = map_weights(cld)

        scenarios = {
            "high_subsidy": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "no_subsidy": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        }
        results = run_scenario_comparison(fcm, scenarios)
        assert len(results) == 3  # baseline + 2 scenarios
        for name, state in results.items():
            assert len(state) == 6
            assert all(0.0 <= v <= 1.0 for v in state), f"Scenario {name} out of bounds"


# =====================================================================
# D2D Integration
# =====================================================================

class TestD2DIntegration:
    def test_leverage_ranking_consistency(self):
        """Top leverage point should match highest sensitivity."""
        cld = make_golden_shared_cld()
        fcm = map_weights(cld)
        sensitivity = compute_sensitivity(cld)
        ranges = compute_uncertainty_ranges(cld, fcm, sensitivity)
        leverage = rank_leverage_points(sensitivity, cld, ranges)

        # Fiscal subsidy should be a top leverage point (it has most outgoing edges)
        top_labels = [lp.node for lp in leverage.leverage_points[:3]]
        assert "fiscal subsidy" in top_labels

    def test_uncertainty_ranges_valid(self):
        """All uncertainty ranges should be valid (lower <= upper)."""
        cld = make_golden_shared_cld()
        fcm = map_weights(cld)
        sensitivity = compute_sensitivity(cld)
        ranges = compute_uncertainty_ranges(cld, fcm, sensitivity)

        for node_id, (lower, upper) in ranges.items():
            assert lower <= upper, f"Invalid range for {node_id}: ({lower}, {upper})"
            assert lower >= 0.0, f"Negative lower bound for {node_id}: {lower}"


# =====================================================================
# LLM-Dependent Tests (require mock or network)
# =====================================================================

class TestCLDModulePlaceholder:
    """Test CLD module in placeholder (no-LLM) mode."""

    @pytest.mark.asyncio
    async def test_placeholder_mode(self):
        from backend.core.modules.cld.module import CLDModule
        from backend.core.modules.cld.schema import CLDAnalysisInput

        module = CLDModule()  # No LLM = placeholder mode
        input_data = CLDAnalysisInput(research_question="test question")
        output = await module.run(input_data)
        assert output.shared_cld.nodes
        assert output.diagnostics.get("placeholder") is True

    @pytest.mark.asyncio
    async def test_placeholder_preserves_edges(self):
        from backend.core.modules.cld.module import CLDModule
        from backend.core.modules.cld.schema import CLDAnalysisInput

        module = CLDModule()
        input_data = CLDAnalysisInput(research_question="test question")
        output = await module.run(input_data)
        assert len(output.shared_cld.edges) == 2
