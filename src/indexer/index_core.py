"""
索引核心功能模块
包含索引获取、数据库信息打印、维度检查等核心功能
"""

from pathlib import Path
from typing import Optional

from llama_index.core import VectorStoreIndex

from src.logger import setup_logger

logger = setup_logger('indexer')


def get_index(index_manager) -> VectorStoreIndex:
    """获取现有索引"""
    if index_manager._index is None:
        try:
            index_manager._index = VectorStoreIndex.from_vector_store(
                vector_store=index_manager.vector_store,
                storage_context=index_manager.storage_context,
            )
            logger.info("✅ 从向量存储加载索引成功")
        except Exception as e:
            logger.info("ℹ️  没有找到现有索引，将在添加文档后创建")
            index_manager._index = VectorStoreIndex.from_documents(
                [],
                storage_context=index_manager.storage_context,
            )
    
    return index_manager._index


def print_database_info(index_manager):
    """打印数据库和collection的详细信息"""
    try:
        # 1. 列出所有collections
        try:
            all_collections = index_manager.chroma_client.list_collections()
            logger.info("📋 数据库中的Collections列表:")
            if all_collections:
                for idx, coll in enumerate(all_collections, 1):
                    try:
                        coll_count = coll.count() if hasattr(coll, 'count') else 0
                        coll_name = coll.name if hasattr(coll, 'name') else str(coll)
                        logger.info(f"   {idx}. {coll_name} - {coll_count} 个向量")
                    except Exception as e:
                        coll_name = coll.name if hasattr(coll, 'name') else str(coll)
                        logger.warning(f"   {idx}. {coll_name} - 无法获取统计信息: {e}")
            else:
                logger.info("   (无collections)")
        except Exception as e:
            logger.warning(f"获取collections列表失败: {e}")
        
        # 2. 检查当前collection是否存在
        logger.info(f"🔍 检查目标Collection: {index_manager.collection_name}")
        try:
            existing_collection = index_manager.chroma_client.get_collection(name=index_manager.collection_name)
            collection_count = existing_collection.count()
            
            logger.info(f"   ✅ Collection存在")
            logger.info(f"   📊 向量总数: {collection_count}")
            
            # 3. 获取collection的详细信息
            if collection_count > 0:
                sample_limit = min(10, collection_count)
                try:
                    sample_data = existing_collection.peek(limit=sample_limit)
                    
                    file_paths = set()
                    repositories = set()
                    file_types = {}
                    
                    if sample_data and 'metadatas' in sample_data:
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
                    if sample_data and 'metadatas' in sample_data and sample_data['metadatas']:
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
                    logger.warning(f"获取collection样本数据失败: {e}")
                
                # 获取维度信息
                try:
                    if existing_collection.metadata and 'embedding_dimension' in existing_collection.metadata:
                        dim = existing_collection.metadata['embedding_dimension']
                        logger.info(f"   📏 Embedding维度: {dim}")
                    elif sample_data and 'embeddings' in sample_data and sample_data['embeddings']:
                        dim = len(sample_data['embeddings'][0])
                        logger.info(f"   📏 Embedding维度: {dim} (从样本数据检测)")
                except Exception as e:
                    logger.debug(f"获取维度信息失败: {e}")
            else:
                logger.info(f"   ℹ️  Collection为空")
            
        except Exception as e:
            if "does not exist" in str(e) or "not found" in str(e).lower():
                logger.info(f"   ℹ️  Collection不存在，将创建新collection")
            else:
                logger.warning(f"   ⚠️  检查collection时出错: {e}")
        
    except Exception as e:
        logger.error(f"打印数据库信息失败: {e}")

