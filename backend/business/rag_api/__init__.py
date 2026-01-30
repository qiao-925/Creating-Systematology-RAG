"""
RAG API模块

提供RAG服务的统一接口，包括查询、索引构建、对话等功能
同时支持 Streamlit 和 FastAPI 两种使用方式
"""

from .rag_service import RAGService
from .models import RAGResponse, IndexResult, ChatResponse

__version__ = "0.1.0"


def get_fastapi_app():
    """延迟加载 FastAPI 应用（避免 Streamlit 启动时不必要的开销）"""
    from .fastapi_app import app
    return app


__all__ = [
    'RAGService',
    'RAGResponse',
    'IndexResult',
    'ChatResponse',
    'get_fastapi_app',  # FastAPI 应用获取函数（延迟加载）
]
