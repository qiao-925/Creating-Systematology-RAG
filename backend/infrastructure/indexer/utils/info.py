"""
信息打印模块：打印数据库和collection的详细信息
"""

from pathlib import Path
from typing import TYPE_CHECKING, Optional, Any

from backend.infrastructure.logger import get_logger

if TYPE_CHECKING:
    from backend.infrastructure.indexer.core.manager import IndexManager

logger = get_logger('indexer')


def print_database_info(
    index_manager: "IndexManager",
    collection_count: Optional[int] = None,
    sample_data: Optional[Any] = None,
    detailed: bool = False
) -> None:
    """打印数据库和collection的详细信息
    
    Args:
        index_manager: 索引管理器实例
        collection_count: collection的向量数量（如果已获取，避免重复查询）
        sample_data: collection的样本数据（如果已获取，避免重复查询）
        detailed: 是否打印详细信息（默认False，加快初始化）
    """
    try:
        # 直接使用已有的 chroma_collection，不重新获取
        chroma_collection = index_manager.chroma_collection
        
        # 如果未提供 collection_count，则查询（向后兼容）
        if collection_count is None:
            try:
                collection_count = chroma_collection.count()
            except Exception as e:
                logger.warning(f"获取collection数量失败: {e}")
                collection_count = 0
        
        # 获取维度信息
        dim = None
        try:
            if chroma_collection.metadata and 'embedding_dimension' in chroma_collection.metadata:
                dim = chroma_collection.metadata['embedding_dimension']
            elif sample_data and 'embeddings' in sample_data and sample_data['embeddings']:
                dim = len(sample_data['embeddings'][0])
        except Exception as e:
            logger.debug(f"获取维度信息失败: {e}")
        
        # 合并为单行摘要
        dim_str = f", {dim}维" if dim else ""
        logger.info(f"🔍 Collection: {index_manager.collection_name}, 向量数={collection_count}{dim_str}")
        
        # 详细信息（仅在 detailed=True 时执行，避免初始化时不必要的查询）
        if detailed and collection_count > 0:
            # 如果未提供 sample_data，则查询（向后兼容）
            if sample_data is None:
                try:
                    sample_limit = min(10, collection_count)
                    sample_data = chroma_collection.peek(limit=sample_limit)
                except Exception as e:
                    logger.warning(f"获取collection样本数据失败: {e}")
                    sample_data = None
            
            if sample_data:
                try:
                    file_paths = set()
                    repositories = set()
                    file_types = {}
                    
                    if 'metadatas' in sample_data:
                        for metadata in sample_data['metadatas']:
                            if metadata:
                                if 'file_path' in metadata:
                                    file_paths.add(metadata['file_path'])
                                if 'repository' in metadata:
                                    repositories.add(metadata['repository'])
                                if 'file_name' in metadata:
                                    file_name = metadata['file_name']
                                    file_ext = Path(file_name).suffix.lower() if file_name else ''
                                    file_types[file_ext] = file_types.get(file_ext, 0) + 1
                    
                    logger.info(f"   📈 Collection统计信息:")
                    logger.info(f"      • 向量数量: {collection_count}")
                    
                    if file_paths:
                        logger.info(f"      • 唯一文件路径数: {len(file_paths)}")
                        for fp in sorted(list(file_paths))[:20]:
                            logger.debug(f"        - {fp}")
                        if len(file_paths) > 20:
                            logger.debug(f"        ... 还有 {len(file_paths) - 20} 个文件")
                    
                    if repositories:
                        logger.info(f"      • 仓库列表:")
                        for repo in sorted(list(repositories)):
                            logger.debug(f"        - {repo}")
                    
                    if file_types:
                        logger.info(f"      • 文件类型分布:")
                        for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
                            ext_display = ext if ext else "(无扩展名)"
                            logger.info(f"        {ext_display}: {count} 个")
                    
                    # 打印样本metadata（前5条）
                    if 'metadatas' in sample_data and sample_data['metadatas']:
                        logger.debug(f"   📄 样本数据（前5条）:")
                        for idx, metadata in enumerate(sample_data['metadatas'][:5], 1):
                            if metadata:
                                logger.debug(f"      {idx}. Metadata:")
                                for key, value in metadata.items():
                                    value_str = str(value)
                                    if len(value_str) > 100:
                                        value_str = value_str[:100] + "..."
                                    logger.debug(f"         {key}: {value_str}")
                                
                                if 'ids' in sample_data and idx <= len(sample_data['ids']):
                                    doc_id = sample_data['ids'][idx - 1]
                                    logger.debug(f"         id: {doc_id}")
                    
                    logger.info(
                        f"Collection详情: 向量数={collection_count}, "
                        f"文件数={len(file_paths)}, "
                        f"仓库数={len(repositories)}, "
                        f"文件类型={len(file_types)}"
                    )
                except Exception as e:
                    logger.warning(f"分析collection样本数据失败: {e}")
        elif collection_count == 0:
            logger.info(f"   ℹ️  Collection为空")
        
    except Exception as e:
        logger.error(f"打印数据库信息失败: {e}")
