"""CLDFlow MVP CLD schemas."""

from __future__ import annotations

from typing import Any

from llama_index.core import Document
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.core.models import SharedCLD


class CLDAnalysisInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_question: str = Field(..., min_length=1)
    documents: list[Document] = Field(default_factory=list)
    perspective_hints: list[str] | None = None
    max_perspectives: int = Field(default=3, ge=1, le=5)

    @field_validator("documents", mode="before")
    @classmethod
    def coerce_documents(cls, v: Any) -> list[Document]:
        """Accept strings, dicts, or Document objects."""
        if not v:
            return []
        result = []
        for item in v:
            if isinstance(item, Document):
                result.append(item)
            elif isinstance(item, str):
                result.append(Document(text=item))
            elif isinstance(item, dict):
                result.append(Document(text=item.get("text", str(item))))
            else:
                result.append(Document(text=str(item)))
        return result


class CLDAnalysisOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shared_cld: SharedCLD
    perspectives_used: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    diagnostics: dict[str, Any] = Field(default_factory=dict)
