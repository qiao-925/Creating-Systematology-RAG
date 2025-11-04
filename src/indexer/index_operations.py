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


def clear_collection_cache(index_manager):
    """清除collection中的所有向量数据（保留collection结构）
    
    与clear_index的区别：
    - clear_index: 删除整个collection并重新创建
    - clear_collection_cache: 只删除所有向量数据，保留collection结构
    
    Args:
        index_manager: IndexManager实例
    """
    try:
        if not hasattr(index_manager, 'chroma_collection') or index_manager.chroma_collection is None:
            logger.warning("⚠️  chroma_collection未初始化，无需清除")
            return
        
        # 获取collection中的向量数量
        vector_count = index_manager.chroma_collection.count()
        
        if vector_count == 0:
            logger.info(f"✅ Collection '{index_manager.collection_name}' 已经为空，无需清除")
            return
        
        logger.info(f"🔄 开始清除collection '{index_manager.collection_name}' 中的 {vector_count} 个向量...")
        
        # 方法1: 尝试一次性获取所有向量ID并删除（适用于数据量不大的情况）
        # 如果数据量很大，使用分批删除策略
        batch_size = 1000  # 每批处理1000个向量
        deleted_count = 0
        
        # 循环删除，直到collection为空
        while True:
            try:
                # 获取当前的向量数量
                current_count = index_manager.chroma_collection.count()
                
                if current_count == 0:
                    break
                
                # 获取一批向量ID（不带where条件，获取所有）
                # 使用limit限制每批处理的數量，避免一次性加载过多数据
                result = index_manager.chroma_collection.get(limit=batch_size)
                
                if not result or not result.get('ids') or len(result['ids']) == 0:
                    # 如果没有获取到任何向量，说明已经清空
                    break
                
                vector_ids = result['ids']
                
                # 批量删除这一批向量
                index_manager.chroma_collection.delete(ids=vector_ids)
                deleted_count += len(vector_ids)
                logger.debug(f"已删除 {deleted_count} 个向量（剩余约 {current_count - len(vector_ids)} 个）...")
                
            except Exception as batch_error:
                logger.error(f"批量删除向量时出错: {batch_error}")
                raise
        
        # 验证是否全部清除
        remaining_count = index_manager.chroma_collection.count()
        
        if remaining_count == 0:
            logger.info(f"✅ 成功清除collection '{index_manager.collection_name}' 中的所有 {deleted_count} 个向量")
            
            # 重置索引对象（因为向量数据已清空）
            index_manager._index = None
            logger.info("✅ 索引对象已重置")
        else:
            error_msg = f"清除collection失败，仍有 {remaining_count} 个向量未被清除"
            logger.warning(f"⚠️  {error_msg}")
            raise RuntimeError(error_msg)
        
    except Exception as e:
        logger.error(f"❌ 清除collection缓存失败: {e}")
        raise

