"""
RAG服务 - 数据模型模块
响应数据类定义
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class RAGResponse:
    """RAG查询响应"""
    answer: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def has_sources(self) -> bool:
        """是否有引用来源"""
        return bool(self.sources)


@dataclass
class IndexResult:
    """索引构建结果"""
    success: bool
    collection_name: str
    doc_count: int
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatResponse:
    """对话响应"""
    answer: str
    sources: List[Dict[str, Any]]
    session_id: str
    turn_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)

