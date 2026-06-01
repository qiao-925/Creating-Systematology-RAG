"""Unit tests: cld/module.py — CLDModule in placeholder (no-LLM) mode."""

from __future__ import annotations

import pytest

from backend.core.models import CausalLink, CLDNode, SharedCLD
from backend.core.modules.cld.schema import CLDAnalysisInput, CLDAnalysisOutput


# Most tests use CLDModule directly, but since it imports LLM types,
# we test placeholder behavior via the schema-level contracts.
# Full module tests (with mock LLM) are in integration tests.

class TestCLDAnalysisInput:
    def test_minimal_input(self):
        inp = CLDAnalysisInput(research_question="How does fiscal subsidy affect housing?")
        assert inp.research_question == "How does fiscal subsidy affect housing?"
        assert inp.documents == []
        assert inp.max_perspectives == 3
        assert inp.perspective_hints is None

    def test_empty_question_raises(self):
        with pytest.raises(Exception):  # ValidationError or ValueError
            CLDAnalysisInput(research_question="")

    def test_custom_max_perspectives(self):
        inp = CLDAnalysisInput(research_question="test", max_perspectives=5)
        assert inp.max_perspectives == 5

    def test_max_perspectives_above_5_raises(self):
        with pytest.raises(Exception):
            CLDAnalysisInput(research_question="test", max_perspectives=6)

    def test_max_perspectives_below_1_raises(self):
        with pytest.raises(Exception):
            CLDAnalysisInput(research_question="test", max_perspectives=0)

    def test_with_perspective_hints(self):
        inp = CLDAnalysisInput(
            research_question="test",
            perspective_hints=["economic", "social"],
        )
        assert inp.perspective_hints == ["economic", "social"]


class TestCLDAnalysisOutput:
    def test_minimal_output(self):
        cld = SharedCLD(
            nodes=[CLDNode(id="a", label="A")],
            edges=[],
        )
        output = CLDAnalysisOutput(shared_cld=cld)
        assert output.shared_cld.nodes[0].label == "A"
        assert output.perspectives_used == []
        assert output.confidence == 0.0
        assert output.diagnostics == {}

    def test_full_output(self):
        cld = SharedCLD(
            nodes=[CLDNode(id="a", label="A"), CLDNode(id="b", label="B")],
            edges=[CausalLink(source="a", target="b")],
        )
        output = CLDAnalysisOutput(
            shared_cld=cld,
            perspectives_used=["econ"],
            confidence=0.85,
            diagnostics={"placeholder": True},
        )
        assert output.confidence == 0.85
        assert "econ" in output.perspectives_used

    def test_confidence_below_zero_raises(self):
        cld = SharedCLD(nodes=[], edges=[])
        with pytest.raises(Exception):
            CLDAnalysisOutput(shared_cld=cld, confidence=-0.1)

    def test_confidence_above_one_raises(self):
        cld = SharedCLD(nodes=[], edges=[])
        with pytest.raises(Exception):
            CLDAnalysisOutput(shared_cld=cld, confidence=1.1)
