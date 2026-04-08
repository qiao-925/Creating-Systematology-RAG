"""Research kernel business package.

新 API（推荐）:
    from backend.business.research_kernel import ResearchAgent, ResearchOutput

旧 API（已废弃，仅兼容）:
    from backend.business.research_kernel import ResearchKernel, ResearchResult
"""

from backend.business.research_kernel.agent import ResearchAgent
from backend.business.research_kernel.state import ResearchOutput

# [DEPRECATED] 旧 API，保留仅为向后兼容
from backend.business.research_kernel.kernel import ResearchKernel, ResearchResult

__all__ = [
    "ResearchAgent",
    "ResearchOutput",
    # deprecated
    "ResearchKernel",
    "ResearchResult",
]
