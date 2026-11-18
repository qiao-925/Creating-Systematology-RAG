"""
统计功能模块：获取索引统计信息
"""

from typing import Dict, Any, TYPE_CHECKING

from backend.infrastructure.logger import get_logger

if TYPE_CHECKING:
    from backend.infrastructure.indexer.core.manager import IndexManager

logger = get_logger('indexer')


def get_stats(index_manager: "IndexManager") -> Dict[str, Any]:
    """获取索引统计信息
    
    Returns:
        包含统计信息的字典
    """
    try:
        if not hasattr(index_manager, 'chroma_collection') or index_manager.chroma_collection is None:
            logger.warning("⚠️  chroma_collection未初始化，无法获取统计信息")
            return {
                "collection_name": index_manager.collection_name,
                "document_count": 0,
                "embedding_model": index_manager.embedding_model_name,
                "chunk_size": index_manager.chunk_size,
                "chunk_overlap": index_manager.chunk_overlap,
                "error": "chroma_collection未初始化"
            }
        
        count = index_manager.chroma_collection.count()
        logger.debug(f"Collection '{index_manager.collection_name}' 向量数量: {count}")
        
        return {
            "collection_name": index_manager.collection_name,
            "document_count": count,
            "embedding_model": index_manager.embedding_model_name,
            "chunk_size": index_manager.chunk_size,
            "chunk_overlap": index_manager.chunk_overlap,
        }
    except AttributeError as e:
        error_msg = f"chroma_collection属性访问失败: {e}"
        logger.error(error_msg)
        return {
            "collection_name": index_manager.collection_name,
            "document_count": 0,
            "embedding_model": index_manager.embedding_model_name,
            "chunk_size": index_manager.chunk_size,
            "chunk_overlap": index_manager.chunk_overlap,
            "error": str(e)
        }
    except Exception as e:
        # 处理 ChromaDB 集合被软删除的情况
        error_str = str(e).lower()
        if "not found" in error_str or "soft deleted" in error_str or "collection" in error_str:
            error_msg = f"集合 '{index_manager.collection_name}' 不存在或已被删除"
            logger.warning(f"⚠️  {error_msg}")
            return {
                "collection_name": index_manager.collection_name,
                "document_count": 0,
                "embedding_model": index_manager.embedding_model_name,
                "chunk_size": index_manager.chunk_size,
                "chunk_overlap": index_manager.chunk_overlap,
                "error": "集合不存在或已被删除"
            }
        
        error_msg = f"获取统计信息失败: {e}"
        logger.error(error_msg, exc_info=True)
        return {
            "collection_name": index_manager.collection_name,
            "document_count": 0,
            "embedding_model": index_manager.embedding_model_name,
            "chunk_size": index_manager.chunk_size,
            "chunk_overlap": index_manager.chunk_overlap,
            "error": str(e)
        }
