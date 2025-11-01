"""
业务服务层

统一的服务接口，解耦前端与业务逻辑
"""

from .rag_service import RAGService, RAGResponse, IndexResult, ChatResponse

__all__ = [
    'RAGService',
    'RAGResponse',
    'IndexResult',
    'ChatResponse',
]
