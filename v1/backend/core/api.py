"""Systematology API endpoints.

FastAPI router for Systematology analysis pipeline.
Provides POST /analyze and GET /health endpoints.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.core.models import RunContext, StructuredFailureReport, StructuredReport
from backend.core.orchestration.lead_agent import LeadAgent
from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger("systematology.api")

router = APIRouter(prefix="/api/systematology", tags=["systematology"])


class AnalyzeRequest(BaseModel):
    """Request body for Systematology analysis."""
    question: str = Field(..., min_length=1, description="Research question to analyze")
    documents: list[str] | None = Field(default=None, description="Optional document texts")


class AnalyzeResponse(BaseModel):
    """Response body for Systematology analysis."""
    success: bool
    report: dict[str, Any]


def _create_lead_agent() -> LeadAgent:
    """Create a LeadAgent from config."""
    from backend.infrastructure.llms.factory import create_llm

    systematology_config = config.get_systematology_config()
    llm = create_llm(model_id=systematology_config.specialist_model)
    return LeadAgent(
        llm=llm,
        max_iterations=systematology_config.budget_turns,
        timeout_seconds=float(systematology_config.timeout_seconds),
        judge_model=systematology_config.judge_model,
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """Run Systematology analysis pipeline.

    Accepts a research question and optional documents,
    returns a structured analysis report.
    """
    logger.info("Systematology analysis requested", question=request.question[:80])

    try:
        agent = _create_lead_agent()
        run_context = RunContext()

        docs = request.documents or []
        result = await agent.run(
            question=request.question,
            documents=docs,
            run_context=run_context,
        )

        if isinstance(result, StructuredFailureReport):
            return AnalyzeResponse(
                success=False,
                report=result.model_dump(),
            )

        return AnalyzeResponse(
            success=True,
            report=result.model_dump(),
        )

    except Exception as exc:
        logger.error("Systematology analysis failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Analysis failed. Check server logs for details.")


@router.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "systematology"}
