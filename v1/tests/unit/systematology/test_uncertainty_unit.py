"""Unit tests: uncertainty.py — D2D uncertainty range computation."""

from __future__ import annotations

import pytest

from backend.core.models import CausalLink, CLDNode, SharedCLD, WeightedFCM
from backend.core.modules.d2d.uncertainty import compute_uncertainty_ranges


# =====================================================================
# Golden Data Helpers
# =====================================================================

def _make_minimal_cld() -> SharedCLD:
    return SharedCLD(
        nodes=[
            CLDNode(id="a", label="A"),
            CLDNode(id="b", label="B"),
        ],
        edges=[CausalLink(source="a", target="b", relation="causes")],
    )


def _make_minimal_fcm(n: int = 2, confidence: float = 0.7) -> WeightedFCM:
    return WeightedFCM(
        weight_matrix=[[0.0] * n for _ in range(n)],
        confidence_matrix=[[confidence if i != j else 0.0 for j in range(n)] for i in range(n)],
        baseline_state=[0.0] * n,
    )


def _make_sensitivity(node_id: str, total_impact: float) -> dict:
    return {"node": node_id, "total_impact": total_impact, "impacts": []}


# =====================================================================
# compute_uncertainty_ranges Tests
# =====================================================================

class TestComputeUncertaintyRanges:
    def test_happy_path_two_nodes(self):
        cld = _make_minimal_cld()
        fcm = _make_minimal_fcm(confidence=0.7)
        sensitivity = [
            _make_sensitivity("a", 0.5),
            _make_sensitivity("b", 0.3),
        ]
        ranges = compute_uncertainty_ranges(cld, fcm, sensitivity)
        assert len(ranges) == 2
        assert "a" in ranges
        assert "b" in ranges

    def test_lower_bound_non_negative(self):
        cld = _make_minimal_cld()
        fcm = _make_minimal_fcm(confidence=0.5)
        sensitivity = [_make_sensitivity("a", 0.1), _make_sensitivity("b", 0.05)]
        ranges = compute_uncertainty_ranges(cld, fcm, sensitivity)
        for lower, _ in ranges.values():
            assert lower >= 0.0

    def test_upper_geq_lower(self):
        cld = _make_minimal_cld()
        fcm = _make_minimal_fcm()
        sensitivity = [_make_sensitivity("a", 0.5), _make_sensitivity("b", 0.3)]
        ranges = compute_uncertainty_ranges(cld, fcm, sensitivity)
        for lower, upper in ranges.values():
            assert upper >= lower

    def test_high_confidence_narrow_range(self):
        cld = _make_minimal_cld()
        fcm = _make_minimal_fcm(confidence=0.9)  # high confidence
        sensitivity = [_make_sensitivity("a", 0.5)]
        ranges = compute_uncertainty_ranges(cld, fcm, sensitivity)
        lower, upper = ranges["a"]
        width = upper - lower
        assert width < 0.1  # narrow range for high confidence

    def test_low_confidence_wide_range(self):
        cld = _make_minimal_cld()
        fcm = _make_minimal_fcm(confidence=0.2)  # low confidence
        sensitivity = [_make_sensitivity("a", 0.5)]
        ranges = compute_uncertainty_ranges(cld, fcm, sensitivity)
        lower, upper = ranges["a"]
        width = upper - lower
        assert width > 0.1  # wider range for low confidence

    def test_no_outgoing_edges_defaults_confidence(self):
        cld = _make_minimal_cld()
        fcm = WeightedFCM(
            weight_matrix=[[0.0, 0.0], [0.0, 0.0]],
            confidence_matrix=[[0.0, 0.0], [0.0, 0.0]],  # node B has no outgoing edges
            baseline_state=[0.0, 0.0],
        )
        sensitivity = [_make_sensitivity("b", 0.3)]
        ranges = compute_uncertainty_ranges(cld, fcm, sensitivity)
        assert "b" in ranges
        # Confidence defaults to 0.5 when no outgoing edges
        lower, upper = ranges["b"]
        # margin = 0.3 * (1-0.5) * 0.5 = 0.075
        assert abs(upper - lower - 0.15) < 0.01

    def test_empty_sensitivity_results(self):
        cld = _make_minimal_cld()
        fcm = _make_minimal_fcm()
        ranges = compute_uncertainty_ranges(cld, fcm, [])
        assert ranges == {}

    def test_single_node_cld(self):
        cld = SharedCLD(nodes=[CLDNode(id="solo", label="Solo")], edges=[])
        fcm = WeightedFCM(
            weight_matrix=[[0.0]],
            confidence_matrix=[[0.0]],
            baseline_state=[0.0],
        )
        sensitivity = [_make_sensitivity("solo", 0.42)]
        ranges = compute_uncertainty_ranges(cld, fcm, sensitivity)
        assert "solo" in ranges
        lower, upper = ranges["solo"]
        assert 0.0 <= lower <= upper

    def test_zero_impact_produces_zero_centered_range(self):
        cld = _make_minimal_cld()
        fcm = _make_minimal_fcm(confidence=0.5)
        sensitivity = [_make_sensitivity("a", 0.0)]
        ranges = compute_uncertainty_ranges(cld, fcm, sensitivity)
        lower, upper = ranges["a"]
        assert lower == 0.0
        assert upper == 0.0

    def test_uncertainty_factor_formula(self):
        """Verify margin = impact * (1-conf) * 0.5."""
        cld = _make_minimal_cld()
        fcm = _make_minimal_fcm(confidence=0.4)
        sensitivity = [_make_sensitivity("a", 1.0)]
        ranges = compute_uncertainty_ranges(cld, fcm, sensitivity)
        lower, upper = ranges["a"]
        # Conf=0.4, uncertainty_factor=0.6, margin=1.0*0.6*0.5=0.3
        assert round(lower, 4) == 0.7
        assert round(upper, 4) == 1.3

    def test_mismatched_matrix_dimensions_dont_crash(self):
        """If confidence_matrix is smaller than cld.nodes, we should handle gracefully."""
        cld = SharedCLD(
            nodes=[CLDNode(id="a", label="A"), CLDNode(id="b", label="B"), CLDNode(id="c", label="C")],
            edges=[],
        )
        fcm = WeightedFCM(
            weight_matrix=[[0.0, 0.0], [0.0, 0.0]],  # 2x2, but CLD has 3 nodes
            confidence_matrix=[[0.5, 0.5], [0.5, 0.5]],
            baseline_state=[0.0, 0.0],
        )
        sensitivity = [
            _make_sensitivity("a", 0.5),
            _make_sensitivity("b", 0.3),
            _make_sensitivity("c", 0.2),
        ]
        ranges = compute_uncertainty_ranges(cld, fcm, sensitivity)
        assert len(ranges) == 3
        # Node 'c' has no row in confidence matrix → defaults to 0.5
        assert "c" in ranges
