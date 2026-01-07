"""
RAG API模块

提供RAG服务的统一接口，包括查询、索引构建、对话等功能
同时支持 Streamlit 和 FastAPI 两种使用方式
"""

from .rag_service import RAGService
from .models import RAGResponse, IndexResult, ChatResponse
from .fastapi_app import app

__version__ = "0.1.0"

__all__ = [
    'RAGService',
    'RAGResponse',
    'IndexResult',
    'ChatResponse',
    'app',  # FastAPI 应用实例
]
