"""
RAG 服务模块

提供 RAG 服务的统一接口，包括查询、索引构建、对话等功能。
"""

from .rag_service import RAGService
from .models import RAGResponse, IndexResult, ChatResponse

__version__ = "0.1.0"


__all__ = [
    'RAGService',
    'RAGResponse',
    'IndexResult',
    'ChatResponse',
]
