"""Agent infrastructure: reusable research agent primitives.

Usage:
    from backend.infrastructure.agent import ResearchAgent, ResearchOutput
    from backend.infrastructure.agent.state import ResearchState, EvidenceItem
"""

from backend.infrastructure.agent.agent import ResearchAgent
from backend.infrastructure.agent.state import ResearchOutput, ResearchState, EvidenceItem

__all__ = [
    "ResearchAgent",
    "ResearchOutput",
    "ResearchState",
    "EvidenceItem",
]
