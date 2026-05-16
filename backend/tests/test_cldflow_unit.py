"""CLDFlow unit tests: models, mapper, merge, conflict, simulator, sensitivity, ranking, guardrails."""

from __future__ import annotations

import pytest

from backend.core.models import (
    CausalLink,
    CLDNode,
    LeverageAnalysis,
    NodeImpact,
    ParsedQuery,
    RunContext,
    Scenario,
    SharedCLD,
    SimConfig,
    StructuredFailureReport,
    StructuredReport,
    WeightedFCM,
)
from backend.core.modules.fcm.mapper import map_relation_to_weight, map_weights
from backend.core.modules.fcm.simulator import run_simulation, run_scenario_comparison
from backend.core.modules.d2d.sensitivity import compute_sensitivity
from backend.core.modules.d2d.ranking import rank_leverage_points
from backend.core.modules.d2d.uncertainty import compute_uncertainty_ranges
from backend.core.modules.cld.merge import merge_nodes, _string_similarity
from backend.core.modules.cld.conflict import detect_conflicts, resolve_conflicts_by_arbitration
from backend.core.orchestration.guardrails import (
    check_budget,
    check_isolation,
    check_pipeline_rail,
    check_schema,
    check_self_review,
)
from backend.core.reporting.reporting import synthesize_report
from tests.fixtures.cldflow_fixtures import (
    make_golden_leverage_analysis,
    make_golden_shared_cld,
    make_golden_weighted_fcm,
    make_run_context,
    make_specialist_outputs,
)


# =====================================================================
# Model Tests
# =====================================================================

class TestModels:
    def test_cldnode_strict(self):
        node = CLDNode(id="n1", label="test")
        assert node.id == "n1"
        assert node.label == "test"
        assert node.description is None

    def test_cldnode_extra_forbidden(self):
        with pytest.raises(Exception):
            CLDNode(id="n1", label="test", extra_field="bad")

    def test_causal_link_literal(self):
        link = CausalLink(source="a", target="b", relation="causes")
        assert link.relation == "causes"

    def test_causal_link_invalid_relation(self):
        with pytest.raises(Exception):
            CausalLink(source="a", target="b", relation="invalid")

    def test_shared_cld_validation(self):
        cld = SharedCLD(
            nodes=[CLDNode(id="a", label="A"), CLDNode(id="b", label="B")],
            edges=[CausalLink(source="a", target="b")],
        )
        assert len(cld.nodes) == 2
        assert len(cld.edges) == 1

    def test_scenario_model(self):
        s = Scenario(name="test", interventions={"a": 0.5})
        assert s.name == "test"

    def test_sim_config_defaults(self):
        cfg = SimConfig()
        assert cfg.max_iterations == 100
        assert cfg.convergence_threshold == 1e-6

    def test_weighted_fcm_structure(self):
        w = WeightedFCM(
            weight_matrix=[[0.0, 0.5], [-0.3, 0.0]],
            confidence_matrix=[[0.0, 0.6], [0.7, 0.0]],
            baseline_state=[0.5, 0.3],
        )
        assert len(w.weight_matrix) == 2

    def test_run_context_defaults(self):
        ctx = RunContext()
        assert ctx.budget_turns == 10
        assert ctx.budget_tokens == 100_000
        assert ctx.tokens_used == 0
        assert ctx.tool_calls == []

    def test_structured_report(self):
        r = StructuredReport(
            cld_visualization={"nodes": [], "edges": []},
            synthesized_insights="test",
        )
        assert r.synthesized_insights == "test"

    def test_structured_failure_report(self):
        r = StructuredFailureReport(run_id="r1", stage="test", reason="fail")
        assert r.run_id == "r1"


# =====================================================================
# FCM Mapper Tests
# =====================================================================

class TestFCMMapper:
    def test_relation_weights(self):
        assert map_relation_to_weight("causes") == 0.7
        assert map_relation_to_weight("inhibits") == -0.7
        assert map_relation_to_weight("supports") == 0.5
        assert map_relation_to_weight("unknown") == 0.5

    def test_map_weights_golden(self):
        cld = make_golden_shared_cld()
        w = map_weights(cld)
        assert len(w.weight_matrix) == 6
        assert len(w.confidence_matrix) == 6
        assert len(w.baseline_state) == 6
        # Check a known edge: subsidy→demand = causes = 0.7
        assert w.weight_matrix[0][1] == 0.7
        # Check inhibits: inflation→demand = inhibits = -0.7
        assert w.weight_matrix[5][1] == -0.7

    def test_map_weights_empty(self):
        cld = SharedCLD(nodes=[], edges=[])
        w = map_weights(cld)
        assert w.weight_matrix == []


# =====================================================================
# FCM Simulator Tests
# =====================================================================

class TestFCMSimulator:
    def test_convergence(self):
        w = make_golden_weighted_fcm()
        result = run_simulation(w)
        assert len(result) == 6
        assert all(0.0 <= v <= 1.0 for v in result)

    def test_custom_initial_state(self):
        w = make_golden_weighted_fcm()
        result = run_simulation(w, initial_state=[1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        assert len(result) == 6
        # Subsidy set to 1.0 should propagate through the graph
        assert result[0] > 0.4

    def test_scenario_comparison(self):
        w = make_golden_weighted_fcm()
        scenarios = {
            "high_subsidy": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "no_subsidy": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        }
        results = run_scenario_comparison(w, scenarios)
        assert "baseline" in results
        assert "high_subsidy" in results
        assert "no_subsidy" in results

    def test_simple_convergence(self):
        # Simple 2-node system
        w = WeightedFCM(
            weight_matrix=[[0.0, 0.8], [0.0, 0.0]],
            confidence_matrix=[[0.0, 0.7], [0.0, 0.0]],
            baseline_state=[0.5, 0.0],
        )
        result = run_simulation(w)
        assert len(result) == 2
        assert result[1] > 0.0  # Node 2 should be activated


# =====================================================================
# D2D Sensitivity Tests
# =====================================================================

class TestD2DSensitivity:
    def test_sensitivity_golden(self):
        cld = make_golden_shared_cld()
        results = compute_sensitivity(cld)
        assert len(results) == 6
        # Each result should have node, total_impact, impacts
        for r in results:
            assert "node" in r
            assert "total_impact" in r
            assert "impacts" in r

    def test_sensitivity_single_node(self):
        cld = SharedCLD(
            nodes=[CLDNode(id="a", label="A"), CLDNode(id="b", label="B")],
            edges=[CausalLink(source="a", target="b", relation="causes")],
        )
        results = compute_sensitivity(cld)
        assert len(results) == 2
        # Node A should have impact on B
        a_result = next(r for r in results if r["node"] == "a")
        assert a_result["total_impact"] > 0


# =====================================================================
# D2D Ranking Tests
# =====================================================================

class TestD2DRanking:
    def test_ranking_golden(self):
        cld = make_golden_shared_cld()
        sensitivity = compute_sensitivity(cld)
        leverage = rank_leverage_points(sensitivity, cld)
        assert isinstance(leverage, LeverageAnalysis)
        assert len(leverage.leverage_points) == 6
        # Should be sorted by impact descending
        for i in range(len(leverage.leverage_points) - 1):
            assert leverage.leverage_points[i].impact_score >= leverage.leverage_points[i + 1].impact_score

    def test_ranking_with_uncertainty(self):
        cld = make_golden_shared_cld()
        fcm = make_golden_weighted_fcm()
        sensitivity = compute_sensitivity(cld)
        ranges = compute_uncertainty_ranges(cld, fcm, sensitivity)
        leverage = rank_leverage_points(sensitivity, cld, ranges)
        assert len(leverage.uncertainty_ranges) == 6


# =====================================================================
# D2D Uncertainty Tests
# =====================================================================

class TestD2DUncertainty:
    def test_uncertainty_ranges(self):
        cld = make_golden_shared_cld()
        fcm = make_golden_weighted_fcm()
        sensitivity = compute_sensitivity(cld)
        ranges = compute_uncertainty_ranges(cld, fcm, sensitivity)
        assert len(ranges) == 6
        for node_id, (lower, upper) in ranges.items():
            assert lower >= 0.0
            assert upper >= lower


# =====================================================================
# CLD Merge Tests
# =====================================================================

class TestCLDMerge:
    def test_string_similarity_identical(self):
        assert _string_similarity("test", "test") == 1.0

    def test_string_similarity_different(self):
        assert _string_similarity("hello", "world") < 0.5

    def test_string_similarity_similar(self):
        sim = _string_similarity("housing demand", "housing_demands")
        assert sim > 0.5

    def test_merge_no_duplicates(self):
        nodes = [
            CLDNode(id="a", label="apple"),
            CLDNode(id="b", label="banana"),
        ]
        edges = [CausalLink(source="a", target="b")]
        merged_nodes, merged_edges, merge_map = merge_nodes(nodes, edges)
        assert len(merged_nodes) == 2
        assert len(merged_edges) == 1

    def test_merge_similar_nodes(self):
        nodes = [
            CLDNode(id="a", label="housing demand"),
            CLDNode(id="b", label="housing_demands"),
            CLDNode(id="c", label="inflation"),
        ]
        edges = [
            CausalLink(source="a", target="c"),
            CausalLink(source="b", target="c"),
        ]
        merged_nodes, merged_edges, merge_map = merge_nodes(nodes, edges, threshold=0.5)
        # "housing demand" and "housing_demands" should merge
        assert len(merged_nodes) <= 3

    def test_merge_preserves_edges(self):
        nodes = [
            CLDNode(id="a", label="A"),
            CLDNode(id="b", label="B"),
            CLDNode(id="c", label="C"),
        ]
        edges = [
            CausalLink(source="a", target="b", relation="causes"),
            CausalLink(source="b", target="c", relation="supports"),
        ]
        merged_nodes, merged_edges, _ = merge_nodes(nodes, edges)
        assert len(merged_edges) == 2


# =====================================================================
# CLD Conflict Tests
# =====================================================================

class TestCLDConflict:
    def test_no_conflict(self):
        outputs = [
            {"perspective_id": "p1", "links": [{"source": "a", "target": "b", "relation": "causes"}]},
            {"perspective_id": "p2", "links": [{"source": "c", "target": "d", "relation": "supports"}]},
        ]
        conflicts = detect_conflicts(outputs)
        assert len(conflicts) == 0

    def test_detect_conflict(self):
        outputs = [
            {"perspective_id": "p1", "links": [{"source": "a", "target": "b", "relation": "causes"}]},
            {"perspective_id": "p2", "links": [{"source": "a", "target": "b", "relation": "inhibits"}]},
        ]
        conflicts = detect_conflicts(outputs)
        assert len(conflicts) == 1
        assert conflicts[0]["severity"] == "high"  # causes vs inhibits

    def test_resolve_by_majority(self):
        conflicts = [{
            "source": "a", "target": "b",
            "perspectives": {"p1": "causes", "p2": "inhibits", "p3": "causes"},
            "severity": "high",
        }]
        all_links = [
            {"source": "a", "target": "b", "relation": "causes"},
            {"source": "a", "target": "b", "relation": "inhibits"},
            {"source": "a", "target": "b", "relation": "causes"},
        ]
        resolved = resolve_conflicts_by_arbitration(conflicts, all_links)
        assert len(resolved) == 1
        assert resolved[0]["relation"] == "causes"  # majority


# =====================================================================
# Guardrail Tests
# =====================================================================

class TestGuardrails:
    def test_pipeline_rail(self):
        ctx = RunContext()
        with pytest.raises(RuntimeError, match="Pipeline rail"):
            check_pipeline_rail(ctx, "run_cld_analysis")
        ctx.tool_calls.append("run_cld_analysis")
        check_pipeline_rail(ctx, "run_cld_analysis")

    def test_budget_guard(self):
        ctx = RunContext(budget_turns=5, budget_tokens=1000)
        check_budget(ctx, estimated_tokens=500)
        ctx.tokens_used = 1000
        with pytest.raises(RuntimeError, match="budget exhausted"):
            check_budget(ctx)

    def test_schema_guard(self):
        result = check_schema({"id": "n1", "label": "test"}, CLDNode)
        assert isinstance(result, CLDNode)

    def test_schema_guard_failure(self):
        with pytest.raises(RuntimeError, match="Schema guard"):
            check_schema({"id": "n1"}, CLDNode)  # missing 'label'

    def test_isolation_guard_no_cross_ref(self):
        outputs = [
            {"perspective_id": "p1", "links": [{"source": "n1", "target": "n2"}]},
            {"perspective_id": "p2", "links": [{"source": "n3", "target": "n4"}]},
        ]
        check_isolation(outputs)

    def test_self_review_gate_pass(self):
        cld = make_golden_shared_cld()
        check_self_review(cld)

    def test_self_review_gate_too_few_nodes(self):
        cld = SharedCLD(
            nodes=[CLDNode(id="a", label="A")],
            edges=[CausalLink(source="a", target="a")],
        )
        with pytest.raises(RuntimeError, match=">=2 nodes"):
            check_self_review(cld)

    def test_self_review_gate_orphan(self):
        cld = SharedCLD(
            nodes=[
                CLDNode(id="a", label="A"),
                CLDNode(id="b", label="B"),
                CLDNode(id="c", label="C"),
            ],
            edges=[CausalLink(source="a", target="b")],
        )
        with pytest.raises(RuntimeError, match="orphan"):
            check_self_review(cld)


# =====================================================================
# Reporting Tests
# =====================================================================

class TestReporting:
    def test_synthesize_report(self):
        ctx = make_run_context()
        cld = make_golden_shared_cld()
        report = synthesize_report(ctx, cld)
        assert isinstance(report, StructuredReport)
        assert "nodes" in report.cld_visualization
        assert report.synthesized_insights

    def test_synthesize_report_with_fcm(self):
        ctx = make_run_context()
        cld = make_golden_shared_cld()
        fcm = make_golden_weighted_fcm()
        report = synthesize_report(ctx, cld, weighted_fcm=fcm)
        assert report.scenario_comparison is not None

    def test_synthesize_report_with_leverage(self):
        ctx = make_run_context()
        cld = make_golden_shared_cld()
        leverage = make_golden_leverage_analysis()
        report = synthesize_report(ctx, cld, leverage_analysis=leverage)
        assert report.leverage_ranking is not None
