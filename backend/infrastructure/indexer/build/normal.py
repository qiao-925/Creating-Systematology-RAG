"""
正常模式构建模块：正常模式构建索引
"""

import time
from typing import List, Tuple, Dict

from tqdm import tqdm
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import Document as LlamaDocument

from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger('indexer')


def build_index_normal_mode(
    index_manager,
    documents: List[LlamaDocument],
    show_progress: bool = True
) -> Tuple[VectorStoreIndex, Dict[str, List[str]]]:
    """正常模式构建索引"""
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
    
    if need_create_new:
        logger.info(f"[阶段2.1] 🔨 开始创建索引，文档数: {len(documents)}")
        logger.info(f"[阶段2.1]    分块参数: size={index_manager.chunk_size}, overlap={index_manager.chunk_overlap}")
        
        index_start_time = time.time()
        try:
            logger.info("[阶段2.1/2.2/2.3] 📝 步骤1: 文档分块和向量化中...")
            # 获取LlamaIndex兼容的embedding实例
            llama_embed_model = index_manager._get_llama_index_compatible_embedding()
            index_manager._index = VectorStoreIndex.from_documents(
                documents,
                storage_context=index_manager.storage_context,
                embed_model=llama_embed_model,
            )
            # 清除空标记
            if hasattr(index_manager, '_collection_is_empty'):
                delattr(index_manager, '_collection_is_empty')
            index_elapsed = time.time() - index_start_time
            logger.info(f"[阶段2.3] ✅ 索引创建成功 (耗时: {index_elapsed:.2f}s)")
        except Exception as e:
            logger.error(f"[阶段2.1/2.2/2.3] ❌ 索引创建失败: {e}", exc_info=True)
            raise
    else:
        # 增量添加文档
        logger.info(f"[阶段2.1] 📝 开始增量添加文档，文档数: {len(documents)}")
        insert_start_time = time.time()
        try:
            logger.info("[阶段2.1/2.2/2.3] 📝 步骤1: 文档分块和向量化中...")
            # 尝试使用 insert_ref_docs，如果失败则回退到节点批量插入
            try:
                index_manager._index.insert_ref_docs(documents, show_progress=show_progress)
            except TypeError:
                # 如果 insert_ref_docs 不支持 show_progress 参数，则不带参数调用
                index_manager._index.insert_ref_docs(documents)
            insert_elapsed = time.time() - insert_start_time
            logger.info(f"[阶段2.3] ✅ 文档已批量添加到现有索引 (耗时: {insert_elapsed:.2f}s)")
        except AttributeError:
            # 回退到节点批量插入
            from llama_index.core.node_parser import SentenceSplitter
            node_parser = SentenceSplitter(
                chunk_size=index_manager.chunk_size,
                chunk_overlap=index_manager.chunk_overlap
            )
            
            all_nodes = []
            if show_progress:
                logger.debug("[阶段2.1]    正在分块文档...")
            for doc in tqdm(documents, desc="分块", disable=not show_progress, unit="doc"):
                nodes = node_parser.get_nodes_from_documents([doc])
                all_nodes.extend(nodes)
            
            total_nodes = len(all_nodes)
            batch_size = config.EMBED_BATCH_SIZE
            inserted_count = 0
            
            if show_progress:
                pbar = tqdm(total=total_nodes, desc="向量化并插入", unit="node")
            
            batch_start_time = time.time()
            try:
                if hasattr(index_manager._index, 'insert_nodes'):
                    for i in range(0, len(all_nodes), batch_size):
                        batch_nodes = all_nodes[i:i+batch_size]
                        index_manager._index.insert_nodes(batch_nodes)
                        inserted_count += len(batch_nodes)
                        if show_progress:
                            pbar.update(len(batch_nodes))
                else:
                    raise AttributeError("insert_nodes not available")
            except (AttributeError, TypeError):
                for i in range(0, len(all_nodes), batch_size):
                    batch_nodes = all_nodes[i:i+batch_size]
                    for node in batch_nodes:
                        index_manager._index.insert(node)
                    inserted_count += len(batch_nodes)
                    if show_progress:
                        pbar.update(len(batch_nodes))
            
            if show_progress:
                pbar.close()
            
            insert_elapsed = time.time() - insert_start_time
            avg_rate = total_nodes / insert_elapsed if insert_elapsed > 0 else 0
            logger.info(f"[阶段2.3] ✅ 文档已批量添加到现有索引 (耗时: {insert_elapsed:.2f}s, 平均速率: {avg_rate:.1f} nodes/s)")
    
    return index_manager._index, {}
