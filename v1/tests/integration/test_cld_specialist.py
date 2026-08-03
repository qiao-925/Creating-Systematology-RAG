"""Integration tests: cld/specialist.py — Specialist causal link extraction with mock LLM."""

from __future__ import annotations

import pytest

from backend.core.modules.cld.perspectives.generator import Perspective as CLDPerspective
from backend.core.modules.cld.specialist import (
    SpecialistLink,
    SpecialistNode,
    _parse_and_validate,
    extract_causal_links,
    run_specialists_parallel,
)
from tests.fixtures.systematology_fixtures import MockLLM, MockCompletion


# =====================================================================
# SpecialistLink.coerce_relation Tests
# =====================================================================

class TestCoerceRelation:
    def test_maps_increases_to_causes(self):
        assert SpecialistLink.coerce_relation("increases") == "causes"

    def test_maps_decreases_to_inhibits(self):
        assert SpecialistLink.coerce_relation("decreases") == "inhibits"

    def test_maps_weakens_to_inhibits(self):
        assert SpecialistLink.coerce_relation("weakens") == "inhibits"

    def test_preserves_unknown(self):
        assert SpecialistLink.coerce_relation("unknown_term") == "unknown_term"

    def test_case_insensitive(self):
        assert SpecialistLink.coerce_relation("  REDUCES  ") == "inhibits"


# =====================================================================
# _parse_and_validate Tests
# =====================================================================

VALID_SPECIALIST_JSON = '''{
  "nodes": [
    {"id": "n1", "label": "fiscal subsidy", "description": "Government subsidy policy"},
    {"id": "n2", "label": "demand", "description": "Consumer demand for housing"}
  ],
  "links": [
    {"source": "n1", "target": "n2", "relation": "causes"}
  ]
}'''


class TestParseAndValidate:
    def test_valid_json(self):
        result = _parse_and_validate(VALID_SPECIALIST_JSON)
        assert len(result["nodes"]) == 2
        assert len(result["links"]) == 1
        assert result["links"][0]["relation"] == "causes"

    def test_json_in_code_block(self):
        text = f'```json\n{VALID_SPECIALIST_JSON}\n```'
        result = _parse_and_validate(text)
        assert len(result["nodes"]) == 2

    def test_malformed_json_returns_empty(self):
        result = _parse_and_validate("This is not JSON at all")
        assert result["nodes"] == []
        assert "error" in result

    def test_missing_required_fields_filtered(self):
        data = {
            "nodes": [
                {"id": "n1", "label": "valid"},
                {"id": "n2"},  # missing 'label'
            ],
            "links": [],
        }
        import json
        result = _parse_and_validate(json.dumps(data))
        # Only the valid node should survive
        assert len(result["nodes"]) == 1

    def test_coerces_invalid_relations(self):
        data = {
            "nodes": [{"id": "n1", "label": "A"}],
            "links": [{"source": "n1", "target": "n1", "relation": "increases"}],
        }
        import json
        result = _parse_and_validate(json.dumps(data))
        assert len(result["links"]) == 1
        assert result["links"][0]["relation"] == "causes"


# =====================================================================
# extract_causal_links Tests
# =====================================================================

class TestExtractCausalLinks:
    @pytest.mark.asyncio
    async def test_happy_path(self):
        perspective = CLDPerspective(
            id="test_001",
            name="Tester",
            role_definition={"title": "Test Analyst"},
            extraction_preferences={},
            search_strategy={},
            ddc_class="test",
            template_source="unit_test",
        )
        llm = MockLLM(responses={"nodes": VALID_SPECIALIST_JSON})

        result = await extract_causal_links(perspective, "What causes inflation?", [], llm)
        assert result["perspective_id"] == "test_001"
        assert result["perspective_name"] == "Tester"
        assert len(result["nodes"]) >= 1
        assert len(result["links"]) >= 1

    @pytest.mark.asyncio
    async def test_with_documents(self):
        from llama_index.core import Document

        perspective = CLDPerspective(
            id="doc_test",
            name="DocTester",
            role_definition={"title": "Test"},
            extraction_preferences={},
            search_strategy={},
            ddc_class="test",
            template_source="unit_test",
        )
        docs = [
            Document(text="Government subsidies increase housing demand."),
            Document(text="Higher demand drives up prices."),
        ]
        llm = MockLLM(responses={"links": VALID_SPECIALIST_JSON})

        result = await extract_causal_links(perspective, "What affects housing?", docs, llm)
        assert result["perspective_id"] == "doc_test"

    @pytest.mark.asyncio
    async def test_empty_question_still_works(self):
        perspective = CLDPerspective(
            id="t", name="T", role_definition={},
            extraction_preferences={}, search_strategy={},
            ddc_class="test", template_source="test",
        )
        llm = MockLLM(responses={"nodes": VALID_SPECIALIST_JSON})

        result = await extract_causal_links(perspective, "", [], llm)
        assert result["perspective_id"] == "t"


# =====================================================================
# run_specialists_parallel Tests
# =====================================================================

class TestRunSpecialistsParallel:
    @pytest.mark.asyncio
    async def test_multiple_perspectives(self):
        perspectives = [
            CLDPerspective(
                id=f"p_{i}", name=f"Perspective_{i}",
                role_definition={}, extraction_preferences={},
                search_strategy={}, ddc_class="test", template_source="test",
            )
            for i in range(2)
        ]
        llm = MockLLM(responses={"nodes": VALID_SPECIALIST_JSON})

        results = await run_specialists_parallel(perspectives, "test question", [], llm)
        assert len(results) == 2
        for r in results:
            assert "perspective_id" in r

    @pytest.mark.asyncio
    async def test_one_specialist_fails_others_succeed(self):
        class PartialFailingLLM:
            """Fails on first call, succeeds on subsequent calls."""
            def __init__(self):
                self.call_count = 0

            async def acomplete(self, prompt, **kwargs):
                self.call_count += 1
                if self.call_count == 1:
                    raise RuntimeError("simulated failure")
                return MockCompletion(text=VALID_SPECIALIST_JSON)

        perspectives = [
            CLDPerspective(
                id="fail", name="Failer", role_definition={},
                extraction_preferences={}, search_strategy={},
                ddc_class="test", template_source="test",
            ),
            CLDPerspective(
                id="ok", name="OK", role_definition={},
                extraction_preferences={}, search_strategy={},
                ddc_class="test", template_source="test",
            ),
        ]
        llm = PartialFailingLLM()
        results = await run_specialists_parallel(perspectives, "test", [], llm)
        assert len(results) == 2
        # First specialist should have error
        assert results[0].get("nodes") == []
        assert "error" in results[0]
        # Second should succeed
        assert len(results[1].get("nodes", [])) > 0
