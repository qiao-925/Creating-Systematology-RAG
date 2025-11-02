"""
索引构建核心功能模块
包含索引构建的主要逻辑
"""

import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict

from tqdm import tqdm
from llama_index.core import VectorStoreIndex
from llama_index.core.schema import Document as LlamaDocument

from src.config import config, get_gpu_device
from src.logger import setup_logger

logger = setup_logger('indexer')


def build_index_batch_mode(
    index_manager,
    documents: List[LlamaDocument],
    show_progress: bool = True
) -> Tuple[VectorStoreIndex, Dict[str, List[str]]]:
    """批处理模式构建索引"""
    from llama_index.core.node_parser import SentenceSplitter
    from src.indexer.index_batch import (
        group_documents_by_directory,
        load_batch_ckpt,
        save_batch_ckpt,
        compute_batch_id
    )
    
    total_docs = len(documents)
    group_depth = max(1, config.GROUP_DEPTH)
    docs_per_batch = max(1, config.DOCS_PER_BATCH)
    
    logger.info("🧭 批处理模式已启用")
    logger.info(f"   分组方式: directory (depth={group_depth})")
    logger.info(f"   目标每批文档数: {docs_per_batch}")
    logger.info(f"   总文档数: {total_docs}")
    
    batches = group_documents_by_directory(
        documents=documents,
        depth=group_depth,
        docs_per_batch=docs_per_batch,
        persist_dir=index_manager.persist_dir
    )
    
    if config.INDEX_MAX_BATCHES and config.INDEX_MAX_BATCHES > 0:
        logger.info(f"   测试模式: 仅处理前 {config.INDEX_MAX_BATCHES} 批")
        batches = batches[:config.INDEX_MAX_BATCHES]
    
    total_batches = len(batches)
    logger.info(f"   生成批次数: {total_batches}")
    
    index = index_manager.get_index()
    node_parser = SentenceSplitter(
        chunk_size=index_manager.chunk_size,
        chunk_overlap=index_manager.chunk_overlap
    )
    
    grand_start = time.time()
    grand_docs = 0
    grand_nodes = 0
    grand_tokens_est = 0
    
    ckpt = load_batch_ckpt(index_manager.persist_dir, index_manager.collection_name)
    completed = ckpt.get("completed", {})
    
    for b_idx, batch_docs in enumerate(batches, start=1):
        if not batch_docs:
            continue
        
        first_path = batch_docs[0].metadata.get('file_path', '') or ''
        key = (first_path.replace('\\', '/').lstrip('/') or '_root').split('/')
        group_key = '/'.join(key[:group_depth]) if key else '_root'
        
        batch_doc_count = len(batch_docs)
        tokens_est = sum(max(1, len(d.text) // 4) for d in batch_docs)
        
        file_list = [d.metadata.get('file_path', '') or '' for d in batch_docs]
        batch_id = compute_batch_id(group_key, file_list)
        
        if completed.get(batch_id):
            logger.info(f"📦 批次 {b_idx}/{total_batches} | 组: {group_key} 已完成，跳过 (checkpoint)")
            grand_docs += batch_doc_count
            continue
        
        logger.info(f"📦 批次 {b_idx}/{total_batches} | 组: {group_key}")
        logger.info(f"   文档: {batch_doc_count} | 估算tokens: {tokens_est}")
        
        if show_progress:
            logger.debug("   阶段: 分块中...")
        
        nodes = []
        if show_progress:
            for d in tqdm(batch_docs, desc="分块", disable=not show_progress, unit="doc"):
                nodes.extend(node_parser.get_nodes_from_documents([d]))
        else:
            nodes = node_parser.get_nodes_from_documents(batch_docs)
        
        node_count = len(nodes)
        logger.info(f"   节点: {node_count}")
        
        if show_progress:
            logger.debug("   阶段: 向量化+写入中...")
        
        insert_start = time.time()
        try:
            if hasattr(index_manager._index, 'insert_nodes'):
                index_manager._index.insert_nodes(nodes)
            else:
                for node in nodes:
                    index_manager._index.insert(node)
        except Exception as e:
            logger.warning(f"批次插入异常，回退逐个插入重试: {e}")
            retry_ok = False
            for attempt in range(1, 3):
                try:
                    for node in nodes:
                        index_manager._index.insert(node)
                    retry_ok = True
                    break
                except Exception as e2:
                    logger.warning(f"逐个插入重试失败({attempt}/2): {e2}")
                    continue
            if not retry_ok:
                logger.error("批次写入失败，跳过该批次并继续")
                continue
        
        insert_elapsed = time.time() - insert_start
        docs_per_s = batch_doc_count / insert_elapsed if insert_elapsed > 0 else 0
        nodes_per_s = node_count / insert_elapsed if insert_elapsed > 0 else 0
        tokens_per_s = tokens_est / insert_elapsed if insert_elapsed > 0 else 0
        logger.info(f"   ⏱️ 批耗时: {insert_elapsed:.2f}s | 速率: {nodes_per_s:.1f} nodes/s, {docs_per_s:.1f} docs/s, {tokens_per_s:.1f} tok/s")
        
        grand_docs += batch_doc_count
        grand_nodes += node_count
        grand_tokens_est += tokens_est
        
        completed[batch_id] = {
            "group": group_key,
            "files": file_list,
            "docs": batch_doc_count,
            "nodes": node_count,
            "tokens_est": tokens_est,
            "elapsed": insert_elapsed,
        }
        ckpt["completed"] = completed
        save_batch_ckpt(ckpt, index_manager.persist_dir, index_manager.collection_name)
    
    grand_elapsed = time.time() - grand_start
    grand_docs_s = grand_docs / grand_elapsed if grand_elapsed > 0 else 0
    grand_nodes_s = grand_nodes / grand_elapsed if grand_elapsed > 0 else 0
    grand_tokens_s = grand_tokens_est / grand_elapsed if grand_elapsed > 0 else 0
    logger.info("✅ 批处理完成")
    logger.info(f"   总批次: {total_batches} | 总文档: {grand_docs} | 总节点: {grand_nodes} | 总tokens(估算): {grand_tokens_est}")
    logger.info(f"   总耗时: {grand_elapsed:.2f}s | 平均速率: {grand_nodes_s:.1f} nodes/s, {grand_docs_s:.1f} docs/s, {grand_tokens_s:.1f} tok/s")
    
    return index, {}


def build_index_normal_mode(
    index_manager,
    documents: List[LlamaDocument],
    show_progress: bool = True
) -> Tuple[VectorStoreIndex, Dict[str, List[str]]]:
    """正常模式构建索引"""
    if index_manager._index is None:
        index_start_time = time.time()
        index_manager._index = VectorStoreIndex.from_documents(
            documents,
            storage_context=index_manager.storage_context,
            show_progress=show_progress,
        )
        index_elapsed = time.time() - index_start_time
        logger.info(f"✅ 索引创建成功 (耗时: {index_elapsed:.2f}s)")
    else:
        # 增量添加文档
        insert_start_time = time.time()
        try:
            index_manager._index.insert_ref_docs(documents, show_progress=show_progress)
            insert_elapsed = time.time() - insert_start_time
            logger.info(f"✅ 文档已批量添加到现有索引 (耗时: {insert_elapsed:.2f}s)")
        except AttributeError:
            # 回退到节点批量插入
            from llama_index.core.node_parser import SentenceSplitter
            node_parser = SentenceSplitter(
                chunk_size=index_manager.chunk_size,
                chunk_overlap=index_manager.chunk_overlap
            )
            
            all_nodes = []
            if show_progress:
                logger.debug("   正在分块文档...")
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
            logger.info(f"✅ 文档已批量添加到现有索引 (耗时: {insert_elapsed:.2f}s, 平均速率: {avg_rate:.1f} nodes/s)")
    
    return index_manager._index, {}

