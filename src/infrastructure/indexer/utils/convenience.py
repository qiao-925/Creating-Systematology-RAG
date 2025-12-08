"""
便捷函数模块：提供从目录创建索引的便捷函数
"""

from pathlib import Path
from typing import Optional, TYPE_CHECKING

from src.infrastructure.logger import get_logger

if TYPE_CHECKING:
    from src.infrastructure.indexer.core.manager import IndexManager

logger = get_logger('indexer')


def create_index_from_directory(
    directory_path: str | Path,
    collection_name: Optional[str] = None,
    recursive: bool = True
) -> "IndexManager":
    """从目录创建索引（便捷函数）
    
    Args:
        directory_path: 文档目录路径
        collection_name: 集合名称
        recursive: 是否递归加载
        
    Returns:
        IndexManager对象
    """
    # 延迟导入以避免循环导入
    from src.infrastructure.indexer.core.manager import IndexManager
    from src.infrastructure.data_loader import DataImportService
    
    # 使用统一服务加载文档
    logger.info(f"📂 从目录加载文档: {directory_path}")
    service = DataImportService(show_progress=False)
    result = service.import_from_directory(directory_path, recursive=recursive)
    
    if not result.success or not result.documents:
        logger.warning("⚠️  未找到任何文档")
        if result.errors:
            logger.error(f"错误: {result.errors}")
        return IndexManager(collection_name=collection_name)
    
    documents = result.documents
    
    # 创建索引管理器
    index_manager = IndexManager(collection_name=collection_name)
    
    # 构建索引
    index_manager.build_index(documents)
    
    return index_manager
