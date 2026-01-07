"""
清理功能模块：清空索引和collection缓存
"""

from typing import TYPE_CHECKING

from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext

from backend.infrastructure.logger import get_logger

if TYPE_CHECKING:
    from backend.infrastructure.indexer.core.manager import IndexManager

logger = get_logger('indexer')


def clear_index(index_manager: "IndexManager") -> None:
    """清空索引"""
    try:
        # 删除集合
        index_manager.chroma_client.delete_collection(name=index_manager.collection_name)
        logger.info(f"✅ 已删除集合: {index_manager.collection_name}")
        
        # 重新创建集合
        index_manager.chroma_collection = index_manager.chroma_client.get_or_create_collection(
            name=index_manager.collection_name
        )
        
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


def clear_collection_cache(index_manager: "IndexManager") -> None:
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
        
        batch_size = 1000  # 每批处理1000个向量
        deleted_count = 0
        
        # 循环删除，直到collection为空
        while True:
            try:
                current_count = index_manager.chroma_collection.count()
                
                if current_count == 0:
                    break
                
                result = index_manager.chroma_collection.get(limit=batch_size)
                
                if not result or not result.get('ids') or len(result['ids']) == 0:
                    break
                
                vector_ids = result['ids']
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
            index_manager._index = None
            logger.info("✅ 索引对象已重置")
        else:
            error_msg = f"清除collection失败，仍有 {remaining_count} 个向量未被清除"
            logger.warning(f"⚠️  {error_msg}")
            raise RuntimeError(error_msg)
        
    except Exception as e:
        logger.error(f"❌ 清除collection缓存失败: {e}")
        raise
