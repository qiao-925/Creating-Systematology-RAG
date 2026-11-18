"""
研究内核状态与输出模型

核心职责：
- ResearchState：Agent 研究过程中的可变状态（证据账本、研究进度、预算控制）
- ResearchOutput：研究完成后的结构化输出（判断、证据、张力、下一步问题）
- EvidenceItem：单条证据的结构化表示（来源、文本、相关度）

不负责：Agent 编排逻辑、工具实现、prompt 设计
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ========== 枚举 ==========


class Confidence(str, Enum):
    """判断置信度等级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StopReason(str, Enum):
    """研究停止原因"""
    NOT_STOPPED = ""
    CONVERGED = "converged"
    BUDGET_EXHAUSTED = "budget_exhausted"
    TIMEOUT = "timeout"
    ERROR = "error"


# ========== 证据模型 ==========


class EvidenceItem(BaseModel):
    """单条证据的结构化表示"""
    query: str = Field(..., min_length=1, description="获取该证据使用的查询")
    text: str = Field(..., min_length=1, description="证据文本内容")
    source_ref: str = Field(default="", description="来源标注（文件名、路径或节点ID）")
    score: float = Field(default=0.0, ge=0.0, le=1.0, description="相关度分数")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="原始元数据")

    @field_validator("query", "text")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("不能为空")
        return v


# ========== 研究状态 ==========


class ResearchState(BaseModel):
    """Agent 研究过程中的可变状态

    由 AgentWorkflow 的 Context 承载，工具读写此状态推进研究。
    """
    # 问题与边界
    original_question: str = Field(..., min_length=1, description="用户原始问题")
    focused_question: str = Field(default="", description="定焦后的可研究问题")
    research_boundary: str = Field(default="", description="研究边界说明")

    # 证据
    evidence_plan: List[str] = Field(default_factory=list, description="证据获取计划")
    evidence_ledger: List[EvidenceItem] = Field(default_factory=list, description="证据账本")

    # 判断
    current_judgment: str = Field(default="", description="当前阶段性判断")
    confidence: Confidence = Field(default=Confidence.LOW, description="判断置信度")
    unresolved_tensions: List[str] = Field(default_factory=list, description="未解决的关键张力")

    # 控制
    budget_turns: int = Field(default=10, ge=1, le=50, description="预算上限（工具调用轮次）")
    current_turn: int = Field(default=0, ge=0, description="当前轮次")
    stop_reason: StopReason = Field(default=StopReason.NOT_STOPPED, description="停止原因")

    # 交付
    next_questions: List[str] = Field(default_factory=list, description="值得继续追问的方向")

    @field_validator("original_question")
    @classmethod
    def validate_original_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("原始问题不能为空")
        return v

    @property
    def is_stopped(self) -> bool:
        return self.stop_reason != StopReason.NOT_STOPPED

    @property
    def budget_remaining(self) -> int:
        return max(0, self.budget_turns - self.current_turn)

    @property
    def evidence_count(self) -> int:
        return len(self.evidence_ledger)

    @property
    def has_evidence(self) -> bool:
        return self.evidence_count > 0

    def record_evidence(self, item: EvidenceItem) -> None:
        """追加一条证据到账本"""
        self.evidence_ledger.append(item)

    def increment_turn(self) -> None:
        """推进一轮"""
        self.current_turn += 1
        if self.current_turn >= self.budget_turns:
            self.stop_reason = StopReason.BUDGET_EXHAUSTED


# ========== 研究输出 ==========


class ResearchOutput(BaseModel):
    """研究完成后的结构化输出

    对齐 README 架构图：ResearchOutput { judgment, evidence, confidence, tensions, next_questions }
    """
    judgment: str = Field(..., min_length=1, description="研究判断（非摘要）")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="支撑判断的证据列表")
    confidence: Confidence = Field(default=Confidence.LOW, description="判断置信度")
    tensions: List[str] = Field(default_factory=list, description="未解决的关键张力或矛盾")
    next_questions: List[str] = Field(default_factory=list, description="值得继续追问的方向")
    turns_used: int = Field(default=0, ge=0, description="实际使用的轮次数")
    stop_reason: StopReason = Field(default=StopReason.CONVERGED, description="停止原因")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    @field_validator("judgment")
    @classmethod
    def validate_judgment(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("判断不能为空")
        return v

    @property
    def has_evidence(self) -> bool:
        return len(self.evidence) > 0

    @property
    def evidence_refs(self) -> List[str]:
        """兼容旧 ResearchResult 的 evidence_refs 字段"""
        return [item.source_ref for item in self.evidence if item.source_ref]

    @classmethod
    def from_state(cls, state: ResearchState) -> ResearchOutput:
        """从 ResearchState 构造最终输出"""
        judgment = state.current_judgment
        if not judgment:
            judgment = f'围绕"{state.original_question}"尚未形成可靠判断。'

        return cls(
            judgment=judgment,
            evidence=list(state.evidence_ledger),
            confidence=state.confidence,
            tensions=list(state.unresolved_tensions),
            next_questions=list(state.next_questions),
            turns_used=state.current_turn,
            stop_reason=state.stop_reason if state.is_stopped else StopReason.CONVERGED,
        )
