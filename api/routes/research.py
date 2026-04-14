"""Research mode endpoint — synchronous structured output."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.deps import get_rag_service
from api.schemas import ResearchRequest, ResearchResponse
from backend.infrastructure.logger import get_logger

logger = get_logger("api.research")
router = APIRouter(tags=["research"])


@router.post("/research", response_model=ResearchResponse)
async def research(body: ResearchRequest):
    svc = get_rag_service()

    try:
        result = svc.research(body.question)
    except Exception as e:
        logger.error("Research failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    return ResearchResponse(
        judgment=result.judgment,
        evidence=[
            {
                "query": item.query,
                "text": item.text,
                "source_ref": item.source_ref,
                "score": item.score,
            }
            for item in result.evidence
        ],
        confidence=result.confidence.value if hasattr(result.confidence, "value") else str(result.confidence),
        tensions=result.tensions,
        next_questions=result.next_questions,
    )
