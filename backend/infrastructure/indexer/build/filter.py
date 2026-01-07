"""
文档过滤模块：过滤已向量化的文档，实现文档级断点续传
"""

from typing import List, Tuple

from llama_index.core.schema import Document as LlamaDocument

from backend.infrastructure.indexer.utils.ids import get_vector_ids_by_metadata
from backend.infrastructure.logger import get_logger

logger = get_logger('indexer')


def filter_vectorized_documents(index_manager, documents: List[LlamaDocument]) -> Tuple[List[LlamaDocument], int]:
    """过滤已向量化的文档，实现文档级断点续传
    
    Args:
        index_manager: IndexManager实例
        documents: 文档列表
        
    Returns:
        (待处理的文档列表, 已向量化的文档数量)
    """
    if not documents:
        return [], 0
    
    logger.info(f"🔍 开始过滤已向量化文档，总文档数: {len(documents)}")
    
    if index_manager._index is None:
        logger.debug("   _index 为 None，调用 get_index()...")
        index_manager.get_index()
        logger.debug("   get_index() 调用完成")
    
    if not hasattr(index_manager, 'chroma_collection'):
        logger.info("ℹ️  IndexManager 没有 chroma_collection，所有文档都需要处理")
        return documents, 0
    
    logger.debug(f"   检查 chroma_collection 属性: {hasattr(index_manager, 'chroma_collection')}")
    logger.debug(f"   chroma_collection 值: {index_manager.chroma_collection}")
    
    try:
        logger.info("📊 准备查询 Collection 向量数量...")
        logger.debug(f"    Collection名称: {index_manager.collection_name}")
        logger.debug(f"    chroma_collection对象: {type(index_manager.chroma_collection).__name__}")
        
        logger.info("📊 正在调用 chroma_collection.count()...")
        collection_count = index_manager.chroma_collection.count()
        logger.info(f"📊 Collection 向量数量查询完成: {collection_count}")
        
        if collection_count == 0:
            logger.info("ℹ️  Collection为空，所有文档都需要处理")
            return documents, 0
        
        documents_to_process = []
        already_vectorized_count = 0
        
        logger.info(f"🔍 开始检查 {len(documents)} 个文档的向量化状态...")
        for idx, doc in enumerate(documents, 1):
            file_path = doc.metadata.get("file_path", "")
            if not file_path:
                documents_to_process.append(doc)
                continue
            
            # 添加进度日志（每10个文档或最后一个文档）
            if idx % 10 == 0 or idx == len(documents):
                logger.info(f"   检查进度: {idx}/{len(documents)}")
            
            try:
                vector_ids = get_vector_ids_by_metadata(index_manager, file_path)
                if vector_ids:
                    already_vectorized_count += 1
                    logger.debug(f"文档已向量化，跳过: {file_path}")
                else:
                    documents_to_process.append(doc)
            except Exception as check_error:
                logger.warning(f"检查文档向量化状态失败 [{file_path}]: {check_error}，将处理该文档")
                documents_to_process.append(doc)
        
        logger.info(
            f"✅ 文档过滤完成: "
            f"总文档数={len(documents)}, "
            f"已向量化={already_vectorized_count}, "
            f"待处理={len(documents_to_process)}"
        )
        
        return documents_to_process, already_vectorized_count
        
    except Exception as e:
        logger.error(f"❌ 过滤已向量化文档失败: {e}", exc_info=True)
        logger.error(f"   异常类型: {type(e).__name__}")
        logger.error(f"   异常详情: {str(e)}")
        logger.warning("⚠️  将处理所有文档（跳过过滤）")
        return documents, 0
