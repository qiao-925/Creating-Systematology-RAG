"""Unit tests: service.py — SystematologyAppService deterministic MVP logic."""

from __future__ import annotations

import pytest

from backend.core.models import (
    CausalLink,
    CLDNode,
    LeverageAnalysis,
    ParsedQuery,
    RunContext,
    SharedCLD,
    StructuredFailureReport,
    StructuredReport,
    WeightedFCM,
)
from backend.core.service import SystematologyAppService


# =====================================================================
# parse_query Tests
# =====================================================================

class TestParseQuery:
    def test_valid_question(self):
        service = SystematologyAppService()
        result = service.parse_query("How does fiscal subsidy affect housing?")
        assert isinstance(result, ParsedQuery)
        assert result.query_text == "How does fiscal subsidy affect housing?"
        assert result.documents == []

    def test_trims_whitespace(self):
        service = SystematologyAppService()
        result = service.parse_query("   padded question   ")
        assert result.query_text == "padded question"

    def test_empty_string_raises(self):
        service = SystematologyAppService()
        with pytest.raises(ValueError, match="研究问题不能为空"):
            service.parse_query("")

    def test_whitespace_only_raises(self):
        service = SystematologyAppService()
        with pytest.raises(ValueError, match="研究问题不能为空"):
            service.parse_query("   ")

    def test_with_context(self):
        service = SystematologyAppService()
        result = service.parse_query("test", context={"source": "api"})
        assert result.context == {"source": "api"}


# =====================================================================
# create_run_context Tests
# =====================================================================

class TestCreateRunContext:
    def test_default_budget(self):
        service = SystematologyAppService()
        ctx = service.create_run_context()
        assert isinstance(ctx, RunContext)
        assert ctx.budget_turns == 10

    def test_custom_budget(self):
        service = SystematologyAppService(budget_turns=5)
        ctx = service.create_run_context()
        assert ctx.budget_turns == 5

    def test_run_context_has_run_id(self):
        service = SystematologyAppService()
        ctx = service.create_run_context()
        assert ctx.run_id


# =====================================================================
# build_shared_cld Tests
# =====================================================================

class TestBuildSharedCLD:
    def test_returns_cld_with_two_nodes(self):
        service = SystematologyAppService()
        query = service.parse_query("test question")
        cld = service.build_shared_cld(query)
        assert len(cld.nodes) == 2
        assert len(cld.edges) == 1

    def test_nodes_have_ids_and_labels(self):
        service = SystematologyAppService()
        query = service.parse_query("test question")
        cld = service.build_shared_cld(query)
        assert cld.nodes[0].id == "n1"
        assert cld.nodes[0].label == "test question"
        assert cld.nodes[1].id == "n2"

    def test_edge_connects_nodes(self):
        service = SystematologyAppService()
        query = service.parse_query("test")
        cld = service.build_shared_cld(query)
        assert cld.edges[0].source == "n1"
        assert cld.edges[0].target == "n2"

    def test_metadata_includes_document_count(self):
        service = SystematologyAppService()
        query = service.parse_query("test")
        cld = service.build_shared_cld(query)
        assert cld.metadata["source_count"] == 0

    def test_long_question_truncated_in_label(self):
        service = SystematologyAppService()
        long_q = "A" * 100
        query = service.parse_query(long_q)
        cld = service.build_shared_cld(query)
        assert len(cld.nodes[0].label) == 32


# =====================================================================
# build_weighted_fcm Tests
# =====================================================================

class TestBuildWeightedFCM:
    def test_matrix_dimensions_match_node_count(self):
        service = SystematologyAppService()
        query = service.parse_query("test")
        cld = service.build_shared_cld(query)
        fcm = service.build_weighted_fcm(cld)
        assert len(fcm.weight_matrix) == 2
        assert len(fcm.confidence_matrix) == 2
        assert len(fcm.baseline_state) == 2

    def test_empty_cld_handles_minimum(self):
        service = SystematologyAppService()
        cld = SharedCLD(nodes=[], edges=[])
        fcm = service.build_weighted_fcm(cld)
        assert len(fcm.weight_matrix) == 1  # max(len(nodes), 1)

    def test_confidence_defaults_to_0_5(self):
        service = SystematologyAppService()
        query = service.parse_query("test")
        cld = service.build_shared_cld(query)
        fcm = service.build_weighted_fcm(cld)
        assert fcm.confidence_matrix[0][1] == 0.5


# =====================================================================
# build_leverage_analysis Tests
# =====================================================================

class TestBuildLeverageAnalysis:
    def test_returns_correct_count(self):
        service = SystematologyAppService()
        query = service.parse_query("test")
        cld = service.build_shared_cld(query)
        analysis = service.build_leverage_analysis(cld)
        assert len(analysis.leverage_points) == 2

    def test_impact_scores_are_descending(self):
        service = SystematologyAppService()
        query = service.parse_query("test")
        cld = service.build_shared_cld(query)
        analysis = service.build_leverage_analysis(cld)
        scores = [lp.impact_score for lp in analysis.leverage_points]
        assert scores[0] >= scores[1]  # descending

    def test_first_node_impact_is_1_0(self):
        service = SystematologyAppService()
        query = service.parse_query("test")
        cld = service.build_shared_cld(query)
        analysis = service.build_leverage_analysis(cld)
        assert analysis.leverage_points[0].impact_score == 1.0

    def test_uncertainty_ranges_cover_all_nodes(self):
        service = SystematologyAppService()
        query = service.parse_query("test")
        cld = service.build_shared_cld(query)
        analysis = service.build_leverage_analysis(cld)
        assert len(analysis.uncertainty_ranges) == 2


# =====================================================================
# synthesize_report Tests
# =====================================================================

class TestSynthesizeReport:
    def test_returns_structured_report(self):
        service = SystematologyAppService()
        query = service.parse_query("test")
        ctx = service.create_run_context()
        cld = service.build_shared_cld(query)
        report = service.synthesize_report(ctx, cld)
        assert isinstance(report, StructuredReport)
        assert report.synthesized_insights

    def test_includes_evidence_tracing(self):
        service = SystematologyAppService()
        query = service.parse_query("test")
        ctx = service.create_run_context()
        cld = service.build_shared_cld(query)
        report = service.synthesize_report(ctx, cld)
        assert report.evidence_tracing["run_id"] == ctx.run_id

    def test_report_with_fcm_and_leverage(self):
        service = SystematologyAppService()
        query = service.parse_query("test")
        ctx = service.create_run_context()
        cld = service.build_shared_cld(query)
        fcm = service.build_weighted_fcm(cld)
        leverage = service.build_leverage_analysis(cld)
        report = service.synthesize_report(ctx, cld, fcm, leverage)
        assert report.scenario_comparison is not None
        assert report.leverage_ranking is not None


# =====================================================================
# fail Tests
# =====================================================================

class TestFail:
    def test_returns_failure_report(self):
        service = SystematologyAppService()
        ctx = service.create_run_context()
        failure = service.fail(ctx, "test_stage", "test_reason")
        assert isinstance(failure, StructuredFailureReport)
        assert failure.stage == "test_stage"
        assert failure.reason == "test_reason"

    def test_appends_to_run_context_failures(self):
        service = SystematologyAppService()
        ctx = service.create_run_context()
        assert len(ctx.failures) == 0
        service.fail(ctx, "stage1", "reason1")
        assert len(ctx.failures) == 1
        assert ctx.failures[0].stage == "stage1"

    def test_passes_details(self):
        service = SystematologyAppService()
        ctx = service.create_run_context()
        failure = service.fail(ctx, "stage", "reason", detail="extra info")
        assert failure.details.get("detail") == "extra info"
