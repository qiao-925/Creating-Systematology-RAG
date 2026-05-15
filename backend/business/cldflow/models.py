"""CLDFlow MVP shared models.

These models intentionally keep the MVP narrow:
- one mandatory CLD step
- optional report synthesis
- explicit failure reporting
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class CLDNode(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(default="")
    source_refs: List[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def _strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("node name cannot be empty")
        return value


class SharedCLD(BaseModel):
    nodes: List[CLDNode] = Field(default_factory=list)
    edges: List[Dict[str, str]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CLDFlowRunContext(BaseModel):
    run_id: UUID = Field(default_factory=uuid4)
    question: str = Field(..., min_length=1)
    budget_turns: int = Field(default=5, ge=1, le=20)
    current_turn: int = Field(default=0, ge=0)
    shared_cld: Optional[SharedCLD] = None
    failures: List[str] = Field(default_factory=list)

    @field_validator("question")
    @classmethod
    def _strip_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question cannot be empty")
        return value

    @property
    def budget_remaining(self) -> int:
        return max(0, self.budget_turns - self.current_turn)


class CLDFlowReport(BaseModel):
    question: str
    shared_cld: SharedCLD
    synthesized_insights: str
    evidence_refs: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CLDFlowFailureReport(BaseModel):
    question: str
    reason: str
    diagnostics: Dict[str, Any] = Field(default_factory=dict)
