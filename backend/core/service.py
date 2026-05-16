"""CLDFlow MVP service orchestration."""

from __future__ import annotations

from typing import Any

from backend.core.models import (
    CausalLink,
    CLDNode,
    FailureRecord,
    LeverageAnalysis,
    NodeImpact,
    ParsedQuery,
    RunContext,
    SharedCLD,
    StructuredFailureReport,
    StructuredReport,
    WeightedFCM,
)
from backend.infrastructure.logger import get_logger

logger = get_logger("cldflow.service")


class CLDFlowAppService:
    """Minimal CLDFlow MVP application service."""

    def __init__(self, budget_turns: int = 10):
        self._budget_turns = budget_turns

    def parse_query(self, question: str, context: dict[str, Any] | None = None) -> ParsedQuery:
        question = question.strip()
        if not question:
            raise ValueError("研究问题不能为空")
        return ParsedQuery(query_text=question, documents=[], context=context or {})

    def create_run_context(self) -> RunContext:
        return RunContext(budget_turns=self._budget_turns)

    def build_shared_cld(self, parsed_query: ParsedQuery) -> SharedCLD:
        nodes = [
            CLDNode(id="n1", label=parsed_query.query_text[:32] or "root"),
            CLDNode(id="n2", label="evidence"),
        ]
        edges = [CausalLink(source="n1", target="n2")]
        return SharedCLD(nodes=nodes, edges=edges, metadata={"source_count": len(parsed_query.documents)})

    def build_weighted_fcm(self, shared_cld: SharedCLD) -> WeightedFCM:
        size = max(len(shared_cld.nodes), 1)
        matrix = [[0.0 for _ in range(size)] for _ in range(size)]
        confidence = [[0.5 for _ in range(size)] for _ in range(size)]
        baseline = [0.0 for _ in range(size)]
        return WeightedFCM(
            weight_matrix=matrix,
            confidence_matrix=confidence,
            baseline_state=baseline,
            intervention_states={"baseline": baseline},
        )

    def build_leverage_analysis(self, shared_cld: SharedCLD) -> LeverageAnalysis:
        impacts = [
            NodeImpact(
                node=node.label,
                impact_score=1.0 / (index + 1),
                confidence="medium",
                affected_nodes=[edge.target for edge in shared_cld.edges if edge.source == node.id],
            )
            for index, node in enumerate(shared_cld.nodes)
        ]
        ranges = {node.label: (0.0, 1.0) for node in shared_cld.nodes}
        return LeverageAnalysis(leverage_points=impacts, uncertainty_ranges=ranges)

    def synthesize_report(
        self,
        run_context: RunContext,
        shared_cld: SharedCLD,
        weighted_fcm: WeightedFCM | None = None,
        leverage_analysis: LeverageAnalysis | None = None,
    ) -> StructuredReport:
        return StructuredReport(
            cld_visualization={"nodes": shared_cld.model_dump()["nodes"], "edges": shared_cld.model_dump()["edges"]},
            scenario_comparison=weighted_fcm.model_dump() if weighted_fcm else None,
            leverage_ranking=[item.model_dump() for item in leverage_analysis.leverage_points] if leverage_analysis else None,
            synthesized_insights="MVP pipeline completed with deterministic placeholder outputs.",
            evidence_tracing={"run_id": run_context.run_id, "tool_calls": run_context.tool_calls},
        )

    def fail(self, run_context: RunContext, stage: str, reason: str, **details: Any) -> StructuredFailureReport:
        run_context.failures.append(FailureRecord(stage=stage, reason=reason, details=details))
        logger.warning("CLDFlow failure", stage=stage, reason=reason, details=details)
        return StructuredFailureReport(run_id=run_context.run_id, stage=stage, reason=reason, details=details)
