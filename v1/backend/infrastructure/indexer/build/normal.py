"""
正常模式构建模块：批量优化的索引构建

优化点：
1. 批量分块：一次性处理所有文档
2. 批量插入：使用 insert_nodes() 批量插入
3. 批量查询：合并向量ID查询减少网络请求
"""

import time
from typing import List, Tuple, Dict, Optional, Callable, TYPE_CHECKING

from tqdm import tqdm
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import Document as LlamaDocument

from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger
from backend.infrastructure.indexer.utils.ids import get_vector_ids_with_retry

if TYPE_CHECKING:
    from backend.infrastructure.data_loader.github_sync.manager import GitHubSyncManager

logger = get_logger('indexer')


def _collect_metadata(documents: List[LlamaDocument]) -> Dict[str, Dict]:
    """批量收集文档元数据
    
    Args:
        documents: 文档列表
        
    Returns:
        文件路径到元数据的映射
    """
    metadata_map = {}
    for doc in documents:
        file_path = doc.metadata.get("file_path", "")
        if file_path:
            metadata_map[file_path] = {
                "repository": doc.metadata.get("repository", ""),
                "branch": doc.metadata.get("branch", "main"),
                "owner": doc.metadata.get("owner", ""),
                "repo": doc.metadata.get("repo", "")
            }
    return metadata_map


def _batch_query_vector_ids(
    index_manager,
    documents: List[LlamaDocument],
    show_progress: bool = True
) -> Dict[str, List[str]]:
    """批量查询向量ID
    
    Args:
        index_manager: IndexManager实例
        documents: 文档列表
        show_progress: 是否显示进度
        
    Returns:
        文件路径到向量ID列表的映射
    """
    vector_ids_map = {}
    file_paths = [doc.metadata.get("file_path", "") for doc in documents if doc.metadata.get("file_path")]
    
    if not file_paths:
        return vector_ids_map
    
    total = len(file_paths)
    logger.info(f"[阶段2.3] 🔍 批量查询向量ID: {total} 个文件")
    
    # 批量查询，每 20 个一组
    batch_size = 20
    for i in range(0, total, batch_size):
        batch_paths = file_paths[i:i + batch_size]
        
        for file_path in batch_paths:
            try:
                vector_ids = get_vector_ids_with_retry(index_manager, file_path)
                vector_ids_map[file_path] = vector_ids
            except Exception as e:
                logger.warning(f"查询向量ID失败 [{file_path}]: {e}")
                vector_ids_map[file_path] = []
        
        if show_progress and (i + batch_size) < total:
            logger.debug(f"   向量ID查询进度: {min(i + batch_size, total)}/{total}")
    
    return vector_ids_map


def build_index_normal_mode(
    index_manager,
    documents: List[LlamaDocument],
    show_progress: bool = True,
    github_sync_manager: Optional["GitHubSyncManager"] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> Tuple[VectorStoreIndex, Dict[str, List[str]], Dict[str, Dict]]:
    """批量处理模式构建索引
    
    优化后的流程：
    1. 批量收集元数据
    2. 批量分块所有文档
    3. 批量插入节点
    4. 批量查询向量ID
    
    Args:
        index_manager: IndexManager实例
        documents: 文档列表（已过滤，只包含未向量化的文档）
        show_progress: 是否显示进度
        github_sync_manager: GitHub同步管理器实例（可选）
        progress_callback: 进度回调函数，签名 (current, total) -> None
        
    Returns:
        (索引, 向量ID映射, 文档元数据映射)
    """
    if not documents:
        index = index_manager.get_index()
        return index, {}, {}
    
    total_docs = len(documents)
    logger.info(f"[阶段2.1] 🔨 开始批量构建索引，文档数: {total_docs}")
    
    # 检查是否需要创建新索引
    need_create_new = (
        index_manager._index is None or 
        getattr(index_manager, '_collection_is_empty', False)
    )
    
    if not need_create_new and hasattr(index_manager, 'chroma_collection') and index_manager.chroma_collection:
        try:
            count = index_manager.chroma_collection.count()
            if count == 0:
                need_create_new = True
                logger.info("[阶段2.1] ℹ️  检测到 Collection 为空，将创建新索引")
        except Exception:
            pass
    
    # 阶段1: 批量收集元数据
    metadata_start = time.time()
    metadata_map = _collect_metadata(documents)
    logger.debug(f"[阶段2.1] 元数据收集完成: {len(metadata_map)} 个文件 ({time.time() - metadata_start:.2f}s)")
    
    # 初始化分块器
    from llama_index.core.node_parser import SentenceSplitter
    node_parser = SentenceSplitter(
        chunk_size=index_manager.chunk_size,
        chunk_overlap=index_manager.chunk_overlap
    )
    
    logger.info(f"[阶段2.1]    分块参数: size={index_manager.chunk_size}, overlap={index_manager.chunk_overlap}")
    
    if need_create_new:
        # 创建新索引
        logger.info("[阶段2.1]    模式: 创建新索引（批量处理）")
        index_start_time = time.time()
        
        try:
            llama_embed_model = index_manager._get_llama_index_compatible_embedding()
            
            if progress_callback:
                # 有进度回调时：先分块再逐批插入（支持进度反馈）
                from llama_index.core.node_parser import SentenceSplitter
                node_parser_new = SentenceSplitter(
                    chunk_size=index_manager.chunk_size,
                    chunk_overlap=index_manager.chunk_overlap
                )
                all_nodes = node_parser_new.get_nodes_from_documents(documents, show_progress=show_progress)
                total_nodes = len(all_nodes)
                
                logger.info(f"[阶段2.1] ✅ 分块完成: {total_nodes} 个节点")
                
                # 使用第一批节点创建索引
                batch_size = config.EMBED_BATCH_SIZE * 5
                first_batch = all_nodes[:batch_size]
                remaining_nodes = all_nodes[batch_size:]
                
                # 用第一批节点创建索引（避免空索引问题）
                index_manager._index = VectorStoreIndex(
                    nodes=first_batch,
                    storage_context=index_manager.storage_context,
                    embed_model=llama_embed_model,
                    show_progress=show_progress,
                )
                
                processed_nodes = len(first_batch)
                progress_callback(processed_nodes, total_nodes)
                
                if show_progress:
                    pbar = tqdm(total=total_nodes, initial=processed_nodes, desc="插入节点", unit="node")
                
                # 插入剩余节点
                for i in range(0, len(remaining_nodes), batch_size):
                    batch_nodes = remaining_nodes[i:i + batch_size]
                    if hasattr(index_manager._index, 'insert_nodes'):
                        index_manager._index.insert_nodes(batch_nodes)
                    else:
                        for node in batch_nodes:
                            index_manager._index.insert(node)
                    
                    processed_nodes += len(batch_nodes)
                    
                    if show_progress:
                        pbar.update(len(batch_nodes))
                    
                    progress_callback(processed_nodes, total_nodes)
                
                if show_progress:
                    pbar.close()
                
                # 最终回调确保 100%
                progress_callback(total_nodes, total_nodes)
            else:
                # 无进度回调时：使用原始方式（LlamaIndex 内部批量处理）
                index_manager._index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=index_manager.storage_context,
                    embed_model=llama_embed_model,
                    show_progress=show_progress,
                )
            
            if hasattr(index_manager, '_collection_is_empty'):
                delattr(index_manager, '_collection_is_empty')
            
            index_elapsed = time.time() - index_start_time
            logger.info(f"[阶段2.2] ✅ 索引创建成功 (耗时: {index_elapsed:.2f}s)")
            
        except Exception as e:
            logger.error(f"[阶段2.1/2.2] ❌ 索引创建失败: {e}", exc_info=True)
            raise
    else:
        # 增量添加 - 批量分块和插入
        logger.info("[阶段2.1]    模式: 增量添加（批量优化）")
        insert_start_time = time.time()
        
        try:
            if index_manager._index is None:
                index_manager.get_index()
            
            # 阶段2: 批量分块所有文档
            chunk_start = time.time()
            logger.info(f"[阶段2.1] 📄 批量分块 {total_docs} 个文档...")
            
            all_nodes = node_parser.get_nodes_from_documents(documents, show_progress=show_progress)
            
            chunk_elapsed = time.time() - chunk_start
            logger.info(f"[阶段2.1] ✅ 分块完成: {len(all_nodes)} 个节点 (耗时: {chunk_elapsed:.2f}s)")
            
            # 阶段3: 批量插入节点
            insert_start = time.time()
            batch_size = config.EMBED_BATCH_SIZE * 5  # 增大批次大小
            total_nodes = len(all_nodes)
            
            logger.info(f"[阶段2.2] 📤 批量插入 {total_nodes} 个节点...")
            
            # 使用 tqdm 显示进度
            if show_progress:
                pbar = tqdm(total=total_nodes, desc="插入节点", unit="node")
            
            # 进度回调更新间隔（每 10 个节点）
            callback_interval = 10
            processed_nodes = 0
            
            for i in range(0, total_nodes, batch_size):
                batch_nodes = all_nodes[i:i + batch_size]
                try:
                    if hasattr(index_manager._index, 'insert_nodes'):
                        index_manager._index.insert_nodes(batch_nodes)
                    else:
                        for node in batch_nodes:
                            index_manager._index.insert(node)
                    
                    processed_nodes += len(batch_nodes)
                    
                    if show_progress:
                        pbar.update(len(batch_nodes))
                    
                    # 调用进度回调
                    if progress_callback:
                        progress_callback(processed_nodes, total_nodes)
                        
                except Exception as insert_error:
                    logger.warning(f"批次插入失败 (批次 {i//batch_size + 1}): {insert_error}")
                    # 单个节点重试
                    for node in batch_nodes:
                        try:
                            index_manager._index.insert(node)
                            processed_nodes += 1
                            if show_progress:
                                pbar.update(1)
                            # 单节点模式下，每 callback_interval 个节点回调一次
                            if progress_callback and processed_nodes % callback_interval == 0:
                                progress_callback(processed_nodes, total_nodes)
                        except Exception:
                            pass
            
            if show_progress:
                pbar.close()
            
            # 最终回调确保 100%
            if progress_callback:
                progress_callback(total_nodes, total_nodes)
            
            insert_elapsed = time.time() - insert_start
            logger.info(f"[阶段2.2] ✅ 插入完成 (耗时: {insert_elapsed:.2f}s)")
            
            total_elapsed = time.time() - insert_start_time
            logger.info(f"[阶段2.2] ✅ 增量添加完成，共 {total_nodes} 个节点 (总耗时: {total_elapsed:.2f}s)")
            
        except Exception as e:
            logger.error(f"[阶段2.1/2.2] ❌ 增量添加失败: {e}", exc_info=True)
            raise
    
    # 阶段4: 批量查询向量ID
    vector_ids_map = _batch_query_vector_ids(index_manager, documents, show_progress)
    
    return index_manager._index, vector_ids_map, metadata_map
