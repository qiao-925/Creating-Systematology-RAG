"""
索引操作功能模块
包含搜索、统计、清空等操作
"""

from typing import List, Optional

from llama_index.core import VectorStoreIndex

from src.logger import setup_logger

logger = setup_logger('indexer')


def search(index_manager, query: str, top_k: int = 5) -> List[dict]:
    """搜索相似文档（用于测试）
    
    Args:
        query: 查询文本
        top_k: 返回结果数量
        
    Returns:
        搜索结果列表
    """
    if index_manager._index is None:
        index_manager.get_index()
    
    retriever = index_manager._index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(query)
    
    results = []
    for node in nodes:
        results.append({
            "text": node.node.text,
            "score": node.score,
            "metadata": node.node.metadata,
        })
    
    return results


def get_stats(index_manager) -> dict:
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


def clear_index(index_manager):
    """清空索引"""
    try:
        # 删除集合
        index_manager.chroma_client.delete_collection(name=index_manager.collection_name)
        logger.info(f"✅ 已删除集合: {index_manager.collection_name}")
        
        # 重新创建集合
        index_manager.chroma_collection = index_manager.chroma_client.get_or_create_collection(
            name=index_manager.collection_name
        )
        from llama_index.vector_stores.chroma import ChromaVectorStore
        from llama_index.core import StorageContext
        
        index_manager.vector_store = ChromaVectorStore(chroma_collection=index_manager.chroma_collection)
        index_manager.storage_context = StorageContext.from_defaults(
            vector_store=index_manager.vector_store
        )
        
        # 重置索引
        index_manager._index = None
        logger.info("✅ 索引已清空")
        
    except Exception as e:
        logger.error(f"❌ 清空索引失败: {e}")
        raise

