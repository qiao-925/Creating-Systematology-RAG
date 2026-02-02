"""
RAG API - 数据模型模块

统一管理所有数据模型，包括响应模型和请求模型
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator

# 导入 RAG 引擎模型
from backend.business.rag_engine.models import SourceModel


# ========== 响应模型（Pydantic BaseModel） ==========

class RAGResponse(BaseModel):
    """RAG查询响应模型"""
    answer: str = Field(..., min_length=1, description="生成的答案")
    sources: List[SourceModel] = Field(default_factory=list, description="引用来源列表")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    @property
    def has_sources(self) -> bool:
        """是否有引用来源"""
        return bool(self.sources)
    
    @field_validator('answer')
    def validate_answer(cls, v: str) -> str:
        """验证答案"""
        v = v.strip()
        if not v:
            raise ValueError('答案不能为空')
        return v


class IndexResult(BaseModel):
    """索引构建结果模型"""
    success: bool = Field(..., description="是否成功")
    collection_name: str = Field(..., min_length=1, description="集合名称")
    doc_count: int = Field(..., ge=0, description="文档数量")
    message: str = Field(..., description="结果消息")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")


class ChatResponse(BaseModel):
    """对话响应模型"""
    answer: str = Field(..., min_length=1, description="生成的答案")
    sources: List[SourceModel] = Field(default_factory=list, description="引用来源列表")
    session_id: str = Field(..., min_length=1, description="会话ID")
    turn_count: int = Field(..., ge=1, description="对话轮次")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")
    
    @field_validator('answer')
    def validate_answer(cls, v: str) -> str:
        """验证答案"""
        v = v.strip()
        if not v:
            raise ValueError('答案不能为空')
        return v


# ========== 请求模型（Pydantic） ==========
# 注意：认证相关模型（LoginRequest, RegisterRequest, TokenResponse, UserInfo）已移除
# 单用户模式下不再需要用户认证功能

class QueryRequest(BaseModel):
    """查询请求模型"""
    question: str = Field(..., min_length=1, max_length=2000, description="查询问题")
    session_id: Optional[str] = Field(None, description="会话ID")
    top_k: Optional[int] = Field(None, ge=1, le=50, description="检索数量")
    strategy: Optional[str] = Field(None, description="检索策略（vector/bm25/hybrid/grep/multi）")
    
    @field_validator('question')
    def validate_question(cls, v: str) -> str:
        """验证查询问题"""
        v = v.strip()
        if not v:
            raise ValueError('查询问题不能为空')
        return v
    
    @field_validator('strategy')
    def validate_strategy(cls, v: Optional[str]) -> Optional[str]:
        """验证检索策略"""
        if v is None:
            return v
        valid_strategies = ["vector", "bm25", "hybrid", "grep", "multi"]
        if v not in valid_strategies:
            raise ValueError(f"无效的检索策略: {v}。有效值: {valid_strategies}")
        return v


class ChatRequest(BaseModel):
    """对话请求模型"""
    message: str = Field(..., min_length=1, max_length=2000, description="对话消息")
    session_id: Optional[str] = Field(None, description="会话ID")
    
    @field_validator('message')
    def validate_message(cls, v: str) -> str:
        """验证对话消息"""
        v = v.strip()
        if not v:
            raise ValueError('对话消息不能为空')
        return v


