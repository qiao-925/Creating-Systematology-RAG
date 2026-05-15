"""CLDFlow MVP CLD module.

This is intentionally minimal: a deterministic placeholder that turns the
question into a small, inspectable SharedCLD so the test-first MVP can land
before the richer multi-agent CLD implementation.
"""

from __future__ import annotations

from backend.business.cldflow.models import CLDNode, SharedCLD
from backend.business.cldflow.modules.cld.schema import CLDAnalysisInput, CLDAnalysisOutput


class CLDModule:
    def run(self, input_data: CLDAnalysisInput) -> CLDAnalysisOutput:
        question = input_data.research_question.strip()
        root = CLDNode(
            name=question,
            description="MVP root research question",
            source_refs=["question"],
        )
        node_a = CLDNode(
            name="evidence",
            description="Evidence collection and traceability",
            source_refs=["mvp"],
        )
        node_b = CLDNode(
            name="guardrails",
            description="Budget, schema and self-review constraints",
            source_refs=["mvp"],
        )
        shared_cld = SharedCLD(
            nodes=[root, node_a, node_b],
            edges=[
                {"source": root.name, "target": node_a.name, "relation": "supports"},
                {"source": root.name, "target": node_b.name, "relation": "requires"},
            ],
            metadata={
                "max_perspectives": input_data.max_perspectives,
                "perspective_hints": input_data.perspective_hints or [],
            },
        )
        return CLDAnalysisOutput(
            shared_cld=shared_cld,
            perspectives_used=input_data.perspective_hints or ["default"],
            confidence=0.6,
            diagnostics={"mvp": True},
        )
