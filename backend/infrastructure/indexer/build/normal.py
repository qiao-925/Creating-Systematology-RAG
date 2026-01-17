"""
正常模式构建模块：正常模式构建索引
"""

import time
from typing import List, Tuple, Dict, Optional, TYPE_CHECKING

from tqdm import tqdm
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import Document as LlamaDocument

from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger
from backend.infrastructure.indexer.utils.ids import get_vector_ids_with_retry

if TYPE_CHECKING:
    from backend.infrastructure.data_loader.github_sync.manager import GitHubSyncManager

logger = get_logger('indexer')


def build_index_normal_mode(
    index_manager,
    documents: List[LlamaDocument],
    show_progress: bool = True,
    github_sync_manager: Optional["GitHubSyncManager"] = None
) -> Tuple[VectorStoreIndex, Dict[str, List[str]], Dict[str, Dict]]:
    """按文档逐个处理，返回向量ID映射和文档元数据映射
    
    Args:
        index_manager: IndexManager实例
        documents: 文档列表（已过滤，只包含未向量化的文档）
        show_progress: 是否显示进度
        github_sync_manager: GitHub同步管理器实例（可选）
        
    Returns:
        (索引, 向量ID映射, 文档元数据映射)
    """
    if not documents:
        index = index_manager.get_index()
        return index, {}, {}
    
    # 检查是否需要创建新索引（_index 为 None 或 collection 为空）
    need_create_new = (
        index_manager._index is None or 
        getattr(index_manager, '_collection_is_empty', False)
    )
    
    # 如果 collection 为空，检查是否真的为空
    if not need_create_new and hasattr(index_manager, 'chroma_collection') and index_manager.chroma_collection:
        try:
            count = index_manager.chroma_collection.count()
            if count == 0:
                need_create_new = True
                logger.info("[阶段2.1] ℹ️  检测到 Collection 为空，将创建新索引")
        except Exception:
            pass
    
    vector_ids_map = {}
    metadata_map = {}  # 文档元数据映射
    
    # 初始化分块器
    from llama_index.core.node_parser import SentenceSplitter
    node_parser = SentenceSplitter(
        chunk_size=index_manager.chunk_size,
        chunk_overlap=index_manager.chunk_overlap
    )
    
    batch_size = config.EMBED_BATCH_SIZE
    
    if need_create_new:
        logger.info(f"[阶段2.1] 🔨 开始创建索引，文档数: {len(documents)}")
        logger.info(f"[阶段2.1]    分块参数: size={index_manager.chunk_size}, overlap={index_manager.chunk_overlap}")
        logger.info("[阶段2.1]    按文档逐个处理模式")
        
        index_start_time = time.time()
        try:
            # 获取LlamaIndex兼容的embedding实例
            llama_embed_model = index_manager._get_llama_index_compatible_embedding()
            
            # 按文档逐个处理，收集元数据
            for doc_idx, doc in enumerate(documents, 1):
                file_path = doc.metadata.get("file_path", "")
                
                # 保存文档元数据（用于中间层提取owner/repo/branch）
                if file_path:
                    metadata_map[file_path] = {
                        "repository": doc.metadata.get("repository", ""),
                        "branch": doc.metadata.get("branch", "main"),
                        "owner": doc.metadata.get("owner", ""),
                        "repo": doc.metadata.get("repo", "")
                    }
                
                if show_progress and (doc_idx % 10 == 0 or doc_idx == len(documents)):
                    logger.info(f"[阶段2.1]    处理进度: {doc_idx}/{len(documents)}")
            
            # 创建索引（使用所有文档）
            index_manager._index = VectorStoreIndex.from_documents(
                documents,
                storage_context=index_manager.storage_context,
                embed_model=llama_embed_model,
            )
            
            # 清除空标记
            if hasattr(index_manager, '_collection_is_empty'):
                delattr(index_manager, '_collection_is_empty')
            
            # 查询向量ID（带重试）
            for doc in documents:
                file_path = doc.metadata.get("file_path", "")
                if file_path:
                    vector_ids = get_vector_ids_with_retry(index_manager, file_path)
                    vector_ids_map[file_path] = vector_ids
            
            index_elapsed = time.time() - index_start_time
            logger.info(f"[阶段2.3] ✅ 索引创建成功 (耗时: {index_elapsed:.2f}s)")
        except Exception as e:
            logger.error(f"[阶段2.1/2.2/2.3] ❌ 索引创建失败: {e}", exc_info=True)
            raise
    else:
        # 增量添加文档 - 按文档逐个处理
        logger.info(f"[阶段2.1] 📝 开始增量添加文档，文档数: {len(documents)}")
        logger.info("[阶段2.1]    按文档逐个处理模式")
        insert_start_time = time.time()
        
        try:
            # 确保索引存在
            if index_manager._index is None:
                index_manager.get_index()
            
            # 按文档逐个处理
            doc_progress = tqdm(documents, desc="处理文档", disable=not show_progress, unit="doc") if show_progress else documents
            
            for doc in doc_progress:
                file_path = doc.metadata.get("file_path", "")
                
                # 保存文档元数据（用于中间层提取owner/repo/branch）
                if file_path:
                    metadata_map[file_path] = {
                        "repository": doc.metadata.get("repository", ""),
                        "branch": doc.metadata.get("branch", "main"),
                        "owner": doc.metadata.get("owner", ""),
                        "repo": doc.metadata.get("repo", "")
                    }
                
                # 分块（不再检查是否已向量化，因为已由filter过滤）
                nodes = node_parser.get_nodes_from_documents([doc])
                
                # 批量上传（每10个chunks一批）
                for i in range(0, len(nodes), batch_size):
                    batch_nodes = nodes[i:i+batch_size]
                    try:
                        if hasattr(index_manager._index, 'insert_nodes'):
                            index_manager._index.insert_nodes(batch_nodes)
                        else:
                            for node in batch_nodes:
                                index_manager._index.insert(node)
                    except Exception as insert_error:
                        logger.warning(f"插入节点失败 [{file_path}] (批次 {i//batch_size + 1}): {insert_error}")
                        # 继续处理其他节点
                        continue
                
                # 查询向量ID（带重试）
                if file_path:
                    vector_ids = get_vector_ids_with_retry(index_manager, file_path)
                    vector_ids_map[file_path] = vector_ids
            
            if show_progress and hasattr(doc_progress, 'close'):
                doc_progress.close()
            
            insert_elapsed = time.time() - insert_start_time
            logger.info(f"[阶段2.3] ✅ 文档已按文档逐个添加到现有索引 (耗时: {insert_elapsed:.2f}s)")
        except Exception as e:
            logger.error(f"[阶段2.1/2.2/2.3] ❌ 增量添加文档失败: {e}", exc_info=True)
            raise
    
    return index_manager._index, vector_ids_map, metadata_map
