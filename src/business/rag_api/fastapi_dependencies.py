"""
RAG API - FastAPI依赖注入模块

提供依赖注入函数
"""

from src.business.rag_api.rag_service import RAGService
from src.infrastructure.config import config
from src.infrastructure.logger import get_logger

logger = get_logger('rag_api_dependencies')


def get_rag_service() -> RAGService:
    """获取 RAGService 实例（使用默认collection）
    
    Returns:
        RAGService 实例（使用配置中的默认collection_name）
    """
    return RAGService(collection_name=config.CHROMA_COLLECTION_NAME)
