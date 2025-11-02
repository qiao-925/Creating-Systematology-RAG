"""
索引便捷函数模块
提供从目录、URL等创建索引的便捷函数
"""

from pathlib import Path
from typing import List, Optional

from src.indexer.index_manager import IndexManager
from src.logger import setup_logger

logger = setup_logger('indexer')


def create_index_from_directory(
    directory_path: str | Path,
    collection_name: Optional[str] = None,
    recursive: bool = True
) -> IndexManager:
    """从目录创建索引（便捷函数）
    
    Args:
        directory_path: 文档目录路径
        collection_name: 集合名称
        recursive: 是否递归加载
        
    Returns:
        IndexManager对象
    """
    from src.data_loader import load_documents_from_directory
    
    # 加载文档
    logger.info(f"📂 从目录加载文档: {directory_path}")
    documents = load_documents_from_directory(directory_path, recursive=recursive)
    
    if not documents:
        logger.warning("⚠️  未找到任何文档")
        return IndexManager(collection_name=collection_name)
    
    # 创建索引管理器
    index_manager = IndexManager(collection_name=collection_name)
    
    # 构建索引
    index_manager.build_index(documents)
    
    return index_manager


def create_index_from_urls(
    urls: List[str],
    collection_name: Optional[str] = None
) -> IndexManager:
    """从URL列表创建索引（便捷函数）
    
    Args:
        urls: URL列表
        collection_name: 集合名称
        
    Returns:
        IndexManager对象
    """
    from src.data_loader import load_documents_from_urls
    
    # 加载文档
    logger.info(f"🌐 从 {len(urls)} 个URL加载文档")
    documents = load_documents_from_urls(urls)
    
    if not documents:
        logger.warning("⚠️  未成功加载任何网页")
        return IndexManager(collection_name=collection_name)
    
    # 创建索引管理器
    index_manager = IndexManager(collection_name=collection_name)
    
    # 构建索引
    index_manager.build_index(documents)
    
    return index_manager

