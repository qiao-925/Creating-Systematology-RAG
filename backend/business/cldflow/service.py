"""CLDFlow MVP service."""

from __future__ import annotations

from backend.business.cldflow.guardrails import (
    ensure_budget_remaining,
    ensure_cld_ready,
    ensure_question_is_valid,
)
from backend.business.cldflow.models import (
    CLDFlowFailureReport,
    CLDFlowReport,
    CLDFlowRunContext,
)
from backend.business.cldflow.modules.cld.module import CLDModule
from backend.business.cldflow.modules.cld.schema import CLDAnalysisInput


class CLDFlowService:
    def __init__(self, cld_module: CLDModule | None = None):
        self._cld_module = cld_module or CLDModule()

    def run(self, question: str) -> CLDFlowReport | CLDFlowFailureReport:
        normalized_question = ensure_question_is_valid(question)
        context = CLDFlowRunContext(question=normalized_question)

        try:
            ensure_budget_remaining(context)
            cld_output = self._cld_module.run(
                CLDAnalysisInput(
                    research_question=normalized_question,
                    documents=[],
                    max_perspectives=3,
                )
            )
            context.shared_cld = cld_output.shared_cld
            ensure_cld_ready(context)
            return CLDFlowReport(
                question=normalized_question,
                shared_cld=context.shared_cld,
                synthesized_insights="CLDFlow MVP 已完成：CLD 前置链路已跑通，后续可接 FCM / D2D。",
                evidence_refs=["question", "mvp"],
                metadata={
                    "run_id": str(context.run_id),
                    "confidence": cld_output.confidence,
                    "diagnostics": cld_output.diagnostics,
                },
            )
        except Exception as exc:
            return CLDFlowFailureReport(
                question=normalized_question,
                reason=str(exc),
                diagnostics={"run_id": str(context.run_id)},
            )
