"""CLDFlow CLD module: orchestrates perspectives → specialist → merge → conflict → judge.

Replaces the MVP placeholder with the full multi-agent CLD pipeline.
"""

from __future__ import annotations

from typing import Any

from llama_index.core.llms import LLM

from backend.core.models import CausalLink, CLDNode, SharedCLD
from backend.core.modules.cld.conflict import detect_conflicts, resolve_conflicts_by_arbitration
from backend.core.modules.cld.merge import merge_nodes
from backend.core.modules.cld.perspectives import generate_perspectives, CLDPerspective
from backend.core.modules.cld.schema import CLDAnalysisInput, CLDAnalysisOutput
from backend.core.modules.cld.specialist import run_specialists_parallel
from backend.core.modules.cld.judge import self_review_gate, get_judge_llm
from backend.infrastructure.logger import get_logger

logger = get_logger("cldflow.cld_module")


class CLDModule:
    """Full CLD analysis module: multi-perspective extraction → merge → conflict → judge."""

    def __init__(self, llm: LLM | None = None, judge_model: str = "deepseek-chat"):
        """Initialize CLD module.

        Args:
            llm: LLM for specialist extraction.
                 If None, falls back to deterministic placeholder (MVP mode).
            judge_model: Default model for judge evaluation (G6 fallback).
        """
        self._llm = llm
        self._judge_model = judge_model

    async def run(self, input_data: CLDAnalysisInput) -> CLDAnalysisOutput:
        """Run full CLD analysis pipeline.

        Args:
            input_data: CLDAnalysisInput with research question, documents, etc.

        Returns:
            CLDAnalysisOutput with SharedCLD and diagnostics.

        Raises:
            RuntimeError: If self-review gate fails.
        """
        question = input_data.research_question.strip()

        # MVP fallback if no LLM provided
        if self._llm is None:
            return self._run_placeholder(input_data)  # type: ignore[return-value]

        logger.info("CLD analysis starting", question=question[:80])

        # Step 1: Generate perspectives
        perspectives = generate_perspectives(
            question,
            max_perspectives=input_data.max_perspectives,
        )
        if input_data.perspective_hints:
            # Add user-provided hints as additional perspectives
            for i, hint in enumerate(input_data.perspective_hints):
                perspectives.append(CLDPerspective(
                    id=f"hint_{i}",
                    name=hint,
                    role_definition={"title": hint},
                    extraction_preferences={},
                    ddc_class="custom",
                ))

        logger.info("Perspectives generated", count=len(perspectives))

        # Step 2: Run specialists in parallel
        specialist_outputs = await run_specialists_parallel(
            perspectives=perspectives,
            question=question,
            documents=input_data.documents,
            llm=self._llm,
        )

        logger.info("Specialists complete", count=len(specialist_outputs))

        # Step 3: Collect all nodes and links
        all_nodes: list[CLDNode] = []
        all_links: list[CausalLink] = []
        seen_node_ids: set[str] = set()

        for output in specialist_outputs:
            pid = output.get("perspective_id", "unknown")
            for node_data in output.get("nodes", []):
                node_id = f"{pid}_{node_data['id']}"
                if node_id not in seen_node_ids:
                    seen_node_ids.add(node_id)
                    all_nodes.append(CLDNode(
                        id=node_id,
                        label=node_data["label"],
                        description=node_data.get("description"),
                    ))
            for link_data in output.get("links", []):
                src_id = f"{pid}_{link_data['source']}"
                tgt_id = f"{pid}_{link_data['target']}"
                all_links.append(CausalLink(
                    source=src_id,
                    target=tgt_id,
                    relation=link_data["relation"],
                ))

        # Step 4: Detect conflicts
        conflicts = detect_conflicts(specialist_outputs)

        # Step 5: Merge nodes
        merged_nodes, merged_edges, merge_map = merge_nodes(all_nodes, all_links)

        # Step 6: Resolve conflicts
        if conflicts:
            # Remap conflict edges through merge map
            resolved_links = []
            for edge in merged_edges:
                resolved_links.append({
                    "source": edge.source,
                    "target": edge.target,
                    "relation": edge.relation,
                })
            resolved_links = resolve_conflicts_by_arbitration(conflicts, resolved_links)
            merged_edges = [
                CausalLink(source=l["source"], target=l["target"], relation=l["relation"])
                for l in resolved_links
            ]

        # Step 7: Build SharedCLD
        shared_cld = SharedCLD(
            nodes=merged_nodes,
            edges=merged_edges,
            metadata={
                "perspectives_used": [p.name for p in perspectives],
                "conflict_count": len(conflicts),
                "merge_map": merge_map,
            },
        )

        # Step 8: Self-review gate (uses judge LLM with G6 fallback)
        judge_llm = get_judge_llm(default_model=self._judge_model)
        passed, review = await self_review_gate(
            shared_cld=shared_cld,
            specialist_outputs=specialist_outputs,
            conflicts=conflicts,
            llm=judge_llm,
        )

        if not passed:
            raise RuntimeError(
                f"CLD self-review failed: {review.get('reasoning', 'quality check failed')}"
            )

        logger.info(
            "CLD analysis complete",
            nodes=len(merged_nodes),
            edges=len(merged_edges),
            conflicts=len(conflicts),
            quality_score=review.get("quality_score"),
        )

        return CLDAnalysisOutput(
            shared_cld=shared_cld,
            perspectives_used=[p.name for p in perspectives],
            confidence=review.get("quality_score", 0.5),
            diagnostics={
                "conflicts": conflicts,
                "review": review,
                "specialist_count": len(specialist_outputs),
            },
        )

    def _run_placeholder(self, input_data: CLDAnalysisInput) -> CLDAnalysisOutput:
        """Deterministic placeholder for MVP testing without LLM."""
        question = input_data.research_question.strip()
        root = CLDNode(
            id="n_root",
            label=question[:64] or "root",
            description="MVP root research question",
        )
        node_a = CLDNode(
            id="n_evidence",
            label="evidence",
            description="Evidence collection and traceability",
        )
        node_b = CLDNode(
            id="n_guardrails",
            label="guardrails",
            description="Budget, schema and self-review constraints",
        )
        shared_cld = SharedCLD(
            nodes=[root, node_a, node_b],
            edges=[
                CausalLink(source="n_root", target="n_evidence", relation="supports"),
                CausalLink(source="n_root", target="n_guardrails", relation="requires"),
            ],
            metadata={
                "max_perspectives": input_data.max_perspectives,
                "perspective_hints": input_data.perspective_hints or [],
                "placeholder": True,
            },
        )
        return CLDAnalysisOutput(
            shared_cld=shared_cld,
            perspectives_used=input_data.perspective_hints or ["default"],
            confidence=0.6,
            diagnostics={"mvp": True, "placeholder": True},
        )
