"""
索引向量ID查询模块
包含向量ID查询相关功能
"""

from typing import List, Dict

from src.logger import setup_logger

logger = setup_logger('indexer')


def get_vector_ids_by_metadata(index_manager, file_path: str) -> List[str]:
    """通过文件路径查询对应的向量ID列表
    
    Args:
        index_manager: IndexManager实例
        file_path: 文件路径
        
    Returns:
        向量ID列表
    """
    if not file_path:
        return []
    
    try:
        results = index_manager.chroma_collection.get(
            where={"file_path": file_path}
        )
        return results.get('ids', []) if results else []
    except Exception as e:
        logger.warning(f"查询向量ID失败 [{file_path}]: {e}")
        return []


def get_vector_ids_batch(index_manager, file_paths: List[str]) -> Dict[str, List[str]]:
    """批量查询向量ID映射（优化：减少查询次数）
    
    Args:
        index_manager: IndexManager实例
        file_paths: 文件路径列表
        
    Returns:
        文件路径到向量ID列表的映射字典
    """
    if not file_paths:
        return {}
    
    # 去重
    unique_paths = list(set(file_paths))
    vector_ids_map = {}
    
    try:
        batch_size = 50  # 每批查询50个文件路径
        total_results = 0
        
        for i in range(0, len(unique_paths), batch_size):
            batch_paths = unique_paths[i:i+batch_size]
            for file_path in batch_paths:
                vector_ids = get_vector_ids_by_metadata(index_manager, file_path)
                if vector_ids:
                    vector_ids_map[file_path] = vector_ids
                    total_results += len(vector_ids)
        
        logger.debug(
            f"批量查询向量ID: "
            f"输入{len(file_paths)}个路径(去重后{len(unique_paths)}个), "
            f"找到{len(vector_ids_map)}个文件, "
            f"共{total_results}个向量"
        )
    except Exception as e:
        logger.error(f"批量查询向量ID失败: {e}")
        for file_path in unique_paths:
            try:
                vector_ids = get_vector_ids_by_metadata(index_manager, file_path)
                if vector_ids:
                    vector_ids_map[file_path] = vector_ids
            except Exception as query_error:
                logger.warning(f"查询单个向量ID失败 [{file_path}]: {query_error}")
    
    return vector_ids_map


def delete_vectors_by_ids(index_manager, vector_ids: List[str]):
    """根据向量ID删除向量
    
    Args:
        index_manager: IndexManager实例
        vector_ids: 向量ID列表
    """
    if not vector_ids:
        return
    
    try:
        index_manager.chroma_collection.delete(ids=vector_ids)
    except Exception as e:
        print(f"⚠️  删除向量失败: {e}")
        raise


def get_node_ids_for_document(index_manager, doc_id: str) -> List[str]:
    """获取文档对应的所有节点ID
    
    Args:
        index_manager: IndexManager实例
        doc_id: 文档ID
        
    Returns:
        节点ID列表
    """
    try:
        result = index_manager.chroma_collection.get()
        if not result or 'ids' not in result:
            return []
        return result['ids']
    except Exception as e:
        print(f"⚠️  查询节点ID失败: {e}")
        return []

