"""CLDFlow MVP CLD schemas."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from backend.business.cldflow.models import SharedCLD


class CLDAnalysisInput(BaseModel):
    research_question: str = Field(..., min_length=1)
    documents: List[str] = Field(default_factory=list)
    perspective_hints: Optional[List[str]] = None
    max_perspectives: int = Field(default=3, ge=1, le=5)


class CLDAnalysisOutput(BaseModel):
    shared_cld: SharedCLD
    perspectives_used: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    diagnostics: dict = Field(default_factory=dict)
