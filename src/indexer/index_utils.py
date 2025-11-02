"""
索引工具方法模块
包含文档添加、删除、文档过滤等工具方法
"""

from typing import List, Dict, Tuple

from llama_index.core.schema import Document as LlamaDocument

from src.logger import setup_logger
from src.indexer.index_vector_ids import (
    get_vector_ids_by_metadata,
    get_vector_ids_batch,
    delete_vectors_by_ids
)

logger = setup_logger('indexer')


def add_documents(index_manager, documents: List[LlamaDocument]) -> Tuple[int, Dict[str, List[str]]]:
    """批量添加文档到索引（优化：使用批量插入）
    
    Args:
        documents: 文档列表
        
    Returns:
        (成功添加的文档数量, 文件路径到向量ID的映射)
    """
    if not documents:
        return 0, {}
    
    try:
        # 优先尝试使用insert_ref_docs批量插入
        try:
            index_manager._index.insert_ref_docs(documents, show_progress=False)
            count = len(documents)
        except AttributeError:
            # 使用节点批量插入
            from llama_index.core.node_parser import SentenceSplitter
            node_parser = SentenceSplitter(
                chunk_size=index_manager.chunk_size,
                chunk_overlap=index_manager.chunk_overlap
            )
            all_nodes = node_parser.get_nodes_from_documents(documents)
            for node in all_nodes:
                index_manager._index.insert(node)
            count = len(documents)
        except Exception as e:
            logger.warning(f"批量插入失败，回退到逐个插入: {e}")
            count = 0
            for doc in documents:
                try:
                    index_manager._index.insert(doc)
                    count += 1
                except Exception as insert_error:
                    logger.warning(f"⚠️  添加文档失败 [{doc.metadata.get('file_path', 'unknown')}]: {insert_error}")
    except Exception as e:
        logger.error(f"❌ 批量添加文档失败: {e}")
        return 0, {}
    
    # 批量查询向量ID映射
    file_paths = [doc.metadata.get("file_path", "") for doc in documents 
                 if doc.metadata.get("file_path")]
    vector_ids_map = get_vector_ids_batch(index_manager, file_paths)
    
    return count, vector_ids_map


def delete_documents(index_manager, file_paths: List[str], metadata_manager) -> int:
    """批量删除文档
    
    Args:
        file_paths: 文件路径列表
        metadata_manager: 元数据管理器实例
        
    Returns:
        成功删除的文档数量
    """
    deleted_count = 0
    
    for file_path in file_paths:
        # 需要从文档元数据中提取仓库信息
        # 暂时跳过，因为我们需要更多上下文信息
        pass
    
    return deleted_count


# 向量ID查询功能已移至 index_vector_ids.py


def compute_documents_hash(documents: List[LlamaDocument]) -> str:
    """计算文档列表的哈希值
    
    Args:
        documents: 文档列表
        
    Returns:
        MD5哈希值
    """
    import hashlib
    import json
    
    docs_data = []
    for doc in documents:
        docs_data.append({
            "text": doc.text[:1000],  # 只使用前1000字符以提高性能
            "file_path": doc.metadata.get("file_path", ""),
            "file_name": doc.metadata.get("file_name", "")
        })
    
    docs_str = json.dumps(docs_data, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(docs_str.encode('utf-8')).hexdigest()


def check_vectors_exist(index_manager, documents: List[LlamaDocument]) -> bool:
    """检查文档对应的向量是否已存在于 Chroma 中
    
    Args:
        index_manager: IndexManager实例
        documents: 文档列表
        
    Returns:
        如果所有文档的向量都存在返回True，否则返回False
    """
    try:
        if not hasattr(index_manager, 'chroma_collection'):
            return False
        
        collection_count = index_manager.chroma_collection.count()
        if collection_count == 0:
            return False
        
        file_paths = [doc.metadata.get("file_path", "") for doc in documents if doc.metadata.get("file_path")]
        if not file_paths:
            return False
        
        sample_paths = file_paths[:min(5, len(file_paths))]
        existing_count = 0
        for file_path in sample_paths:
            vector_ids = get_vector_ids_by_metadata(index_manager, file_path)
            if vector_ids:
                existing_count += 1
        
        return existing_count == len(sample_paths)
        
    except Exception as e:
        logger.warning(f"检查向量存在性失败: {e}")
        return False


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
    
    if index_manager._index is None:
        index_manager.get_index()
    
    if not hasattr(index_manager, 'chroma_collection'):
        return documents, 0
    
    try:
        collection_count = index_manager.chroma_collection.count()
        if collection_count == 0:
            return documents, 0
        
        documents_to_process = []
        already_vectorized_count = 0
        
        for doc in documents:
            file_path = doc.metadata.get("file_path", "")
            if not file_path:
                documents_to_process.append(doc)
                continue
            
            vector_ids = get_vector_ids_by_metadata(index_manager, file_path)
            if vector_ids:
                already_vectorized_count += 1
                logger.debug(f"文档已向量化，跳过: {file_path}")
            else:
                documents_to_process.append(doc)
        
        if already_vectorized_count > 0:
            logger.info(
                f"文档级断点续传: "
                f"总文档数={len(documents)}, "
                f"已向量化={already_vectorized_count}, "
                f"待处理={len(documents_to_process)}"
            )
        
        return documents_to_process, already_vectorized_count
        
    except Exception as e:
        logger.warning(f"过滤已向量化文档失败: {e}，将处理所有文档")
        return documents, 0

