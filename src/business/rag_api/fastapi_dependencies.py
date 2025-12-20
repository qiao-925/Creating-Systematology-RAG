"""
RAG API - FastAPI依赖注入模块

提供依赖注入函数
"""

from src.business.rag_api.rag_service import RAGService
from src.infrastructure.config import config
from src.infrastructure.logger import get_logger

logger = get_logger('rag_api_dependencies')

# 全局单例缓存（避免每次请求都创建新实例）
_rag_service_singleton: RAGService | None = None


def get_rag_service() -> RAGService:
    """获取 RAGService 实例（单例模式，使用默认collection）
    
    使用单例模式避免每次请求都创建新实例，提升性能。
    首次调用时会预加载关键组件（index_manager 和 modular_query_engine）。
    
    Returns:
        RAGService 实例（使用配置中的默认collection_name）
    """
    global _rag_service_singleton
    
    if _rag_service_singleton is None:
        logger.info("创建 RAGService 单例实例")
        _rag_service_singleton = RAGService(collection_name=config.CHROMA_COLLECTION_NAME)
        # 预加载关键组件，避免首次请求时的延迟
        logger.info("预加载 RAGService 关键组件")
        _rag_service_singleton.index_manager  # 触发初始化
        _rag_service_singleton.modular_query_engine  # 触发初始化
        logger.info("RAGService 关键组件预加载完成")
    
    return _rag_service_singleton
