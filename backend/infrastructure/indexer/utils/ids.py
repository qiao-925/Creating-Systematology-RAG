"""
向量ID管理模块：向量ID查询和删除
"""

import time
from typing import List, Dict, TYPE_CHECKING

from backend.infrastructure.logger import get_logger

if TYPE_CHECKING:
    from backend.infrastructure.indexer.core.manager import IndexManager

logger = get_logger('indexer')


def get_vector_ids_by_metadata(index_manager: "IndexManager", file_path: str) -> List[str]:
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
        logger.debug(f"查询向量ID: {file_path}")
        results = index_manager.chroma_collection.get(
            where={"file_path": file_path}
        )
        vector_ids = results.get('ids', []) if results else []
        if vector_ids:
            logger.debug(f"找到 {len(vector_ids)} 个向量ID: {file_path}")
        return vector_ids
    except Exception as e:
        logger.warning(f"查询向量ID失败 [{file_path}]: {e}")
        return []


def get_vector_ids_batch(index_manager: "IndexManager", file_paths: List[str]) -> Dict[str, List[str]]:
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


def get_vector_ids_with_retry(
    index_manager: "IndexManager",
    file_path: str,
    max_retries: int = 3,
    retry_delay: float = 0.1
) -> List[str]:
    """查询向量ID（带重试机制）
    
    Args:
        index_manager: IndexManager实例
        file_path: 文件路径
        max_retries: 最大重试次数
        retry_delay: 重试延迟（秒）
        
    Returns:
        向量ID列表
    """
    if not file_path:
        return []
    
    for attempt in range(max_retries):
        try:
            vector_ids = get_vector_ids_by_metadata(index_manager, file_path)
            if vector_ids:
                if attempt > 0:
                    logger.info(f"查询向量ID成功 [{file_path}] (重试 {attempt} 次后)")
                return vector_ids
            # 如果查询成功但结果为空，等待后重试
            if attempt < max_retries - 1:
                delay = retry_delay * (attempt + 1)  # 递增延迟
                logger.debug(f"查询向量ID结果为空 [{file_path}]，等待 {delay:.2f}s 后重试 (尝试 {attempt + 1}/{max_retries})")
                time.sleep(delay)
        except Exception as e:
            logger.warning(f"查询向量ID失败 [{file_path}] (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                delay = retry_delay * (attempt + 1)  # 递增延迟
                time.sleep(delay)
    
    logger.warning(f"查询向量ID最终失败 [{file_path}]，返回空列表")
    return []


def delete_vectors_by_ids(index_manager: "IndexManager", vector_ids: List[str]) -> None:
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
        logger.warning(f"⚠️  删除向量失败: {e}")
        raise
