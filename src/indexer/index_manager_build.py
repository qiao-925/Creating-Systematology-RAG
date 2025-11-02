"""
索引管理器构建方法模块
包含build_index方法的实现
"""

import time
from typing import List, Optional, Tuple, Dict

from llama_index.core.schema import Document as LlamaDocument

from src.config import config, get_gpu_device
from src.logger import setup_logger
from src.indexer.index_builder import build_index_batch_mode, build_index_normal_mode
from src.indexer.index_vector_ids import get_vector_ids_batch
from src.indexer.index_utils import (
    filter_vectorized_documents,
    compute_documents_hash
)

logger = setup_logger('indexer')


def build_index_method(
    index_manager,
    documents: List[LlamaDocument],
    show_progress: bool = True,
    cache_manager=None,
    task_id: Optional[str] = None
) -> Tuple:
    """构建或更新索引（IndexManager的build_index方法实现）"""
    start_time = time.time()
    
    if not documents:
        print("⚠️  没有文档可索引")
        return index_manager.get_index(), {}
    
    # 文档级断点续传
    documents_to_process, already_vectorized = filter_vectorized_documents(index_manager, documents)
    
    if already_vectorized > 0:
        logger.info(f"✅ 检测到 {already_vectorized} 个文档已向量化，跳过处理")
        print(f"📊 断点续传: {already_vectorized}/{len(documents)} 个文档已向量化，剩余 {len(documents_to_process)} 个待处理")
    
    if not documents_to_process:
        logger.info(f"✅ 所有文档已向量化，跳过向量化步骤")
        index = index_manager.get_index()
        vector_ids_map = get_vector_ids_batch(
            index_manager,
            [doc.metadata.get("file_path", "") for doc in documents 
             if doc.metadata.get("file_path")]
        )
        
        if cache_manager and task_id and config.ENABLE_CACHE:
            docs_hash = compute_documents_hash(documents)
            cache_manager.mark_step_completed(
                task_id=task_id,
                step_name=cache_manager.STEP_VECTORIZE,
                input_hash=docs_hash,
                vector_count=index_manager.chroma_collection.count() if hasattr(index_manager, 'chroma_collection') else 0,
                collection_name=index_manager.collection_name
            )
        
        return index, vector_ids_map
    
    documents = documents_to_process
    device = get_gpu_device()
    
    print(f"\n🔨 开始构建索引，共 {len(documents)} 个文档")
    print(f"   分块参数: size={index_manager.chunk_size}, overlap={index_manager.chunk_overlap}")
    
    if device.startswith("cuda"):
        import torch
        device_name = torch.cuda.get_device_name()
        print(f"📊 索引构建设备: {device} ⚡ GPU加速模式")
        print(f"   GPU: {device_name}")
        logger.info(f"📊 索引构建使用GPU: {device_name} ({device})")
    else:
        print(f"📊 索引构建设备: {device} 🐌 CPU模式")
        logger.warning(f"📊 索引构建使用CPU（性能较慢）")
    
    try:
        if config.INDEX_BATCH_MODE:
            index, _ = build_index_batch_mode(index_manager, documents, show_progress)
        else:
            index, _ = build_index_normal_mode(index_manager, documents, show_progress)
        
        # 获取索引统计信息
        stats = index_manager.get_stats()
        total_elapsed = time.time() - start_time
        
        print(f"📊 索引统计: {stats}")
        logger.info(
            f"索引构建完成: "
            f"文档数={len(documents)}, "
            f"向量数={stats.get('document_count', 0)}, "
            f"总耗时={total_elapsed:.2f}s"
        )
        
        # 构建向量ID映射
        vector_ids_map = get_vector_ids_batch(
            index_manager,
            [doc.metadata.get("file_path", "") for doc in documents 
             if doc.metadata.get("file_path")]
        )
        
        # 如果提供了缓存管理器，更新缓存状态
        if cache_manager and task_id and config.ENABLE_CACHE:
            try:
                docs_hash = compute_documents_hash(documents)
                vector_count = stats.get('document_count', 0)
                cache_manager.mark_step_completed(
                    task_id=task_id,
                    step_name=cache_manager.STEP_VECTORIZE,
                    input_hash=docs_hash,
                    vector_count=vector_count,
                    collection_name=index_manager.collection_name
                )
            except Exception as e:
                logger.warning(f"更新向量化缓存状态失败: {e}")
        
        return index_manager._index, vector_ids_map
        
    except Exception as e:
        print(f"❌ 索引构建失败: {e}")
        if cache_manager and task_id:
            try:
                cache_manager.mark_step_failed(
                    task_id=task_id,
                    step_name=cache_manager.STEP_VECTORIZE,
                    error_message=str(e)
                )
            except Exception:
                pass
        raise

