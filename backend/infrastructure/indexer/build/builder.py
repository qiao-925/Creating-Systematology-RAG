"""
构建入口模块：构建或更新索引的入口函数
"""

import time
from typing import List, Optional, Tuple, Dict

from llama_index.core.schema import Document as LlamaDocument

from backend.infrastructure.config import config, get_gpu_device
from backend.infrastructure.logger import get_logger
from backend.infrastructure.indexer.build.normal import build_index_normal_mode
from backend.infrastructure.indexer.build.filter import filter_vectorized_documents
from backend.infrastructure.indexer.utils.ids import get_vector_ids_batch

logger = get_logger('indexer')


def build_index_method(
    index_manager,
    documents: List[LlamaDocument],
    show_progress: bool = True
) -> Tuple:
    """构建或更新索引（IndexManager的build_index方法实现）"""
    start_time = time.time()
    
    logger.info(f"[阶段2.1] 📥 build_index 被调用，文档数: {len(documents) if documents else 0}")
    
    if not documents:
        logger.warning("[阶段2.1] ⚠️  没有文档可索引")
        return index_manager.get_index(), {}
    
    logger.info(f"[阶段2.1] 🔍 开始过滤已向量化文档...")
    logger.debug(f"[阶段2.1]    调用 filter_vectorized_documents，输入文档数: {len(documents)}")
    # 文档级断点续传
    try:
        documents_to_process, already_vectorized = filter_vectorized_documents(index_manager, documents)
        logger.info(f"[阶段2.1] ✅ filter_vectorized_documents 调用完成")
        logger.debug(f"[阶段2.1]    返回结果: 待处理={len(documents_to_process)}, 已向量化={already_vectorized}")
    except Exception as e:
        logger.error(f"[阶段2.1] ❌ filter_vectorized_documents 调用失败: {e}", exc_info=True)
        raise
    
    if already_vectorized > 0:
        logger.info(f"[阶段2.1] ✅ 检测到 {already_vectorized} 个文档已向量化，跳过处理")
        logger.info(f"[阶段2.1] 📊 断点续传: {already_vectorized}/{len(documents)} 个文档已向量化，剩余 {len(documents_to_process)} 个待处理")
    
    if not documents_to_process:
        logger.info(f"[阶段2.1] ✅ 所有文档已向量化，跳过向量化步骤")
        index = index_manager.get_index()
        vector_ids_map = get_vector_ids_batch(
            index_manager,
            [doc.metadata.get("file_path", "") for doc in documents 
             if doc.metadata.get("file_path")]
            )
        
        return index, vector_ids_map
    
    documents = documents_to_process
    device = get_gpu_device()
    
    logger.info(f"[阶段2.1] 🔨 开始构建索引，共 {len(documents)} 个文档")
    logger.info(f"[阶段2.1]    分块参数: size={index_manager.chunk_size}, overlap={index_manager.chunk_overlap}")
    
    if device.startswith("cuda"):
        import torch
        device_name = torch.cuda.get_device_name()
        logger.info(f"[阶段2.2] 📊 索引构建设备: {device} ⚡ GPU加速模式")
        logger.info(f"[阶段2.2]    GPU: {device_name}")
    else:
        logger.warning(f"[阶段2.2] 📊 索引构建设备: {device} 🐌 CPU模式")
    
    try:
        # 只使用正常模式（批处理模式已移除）
        index, _ = build_index_normal_mode(index_manager, documents, show_progress)
        
        # 获取索引统计信息
        stats = index_manager.get_stats()
        total_elapsed = time.time() - start_time
        
        logger.info(f"[阶段2.3] 📊 索引统计: {stats}")
        logger.info(
            f"[阶段2.3] 索引构建完成: "
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
        
        return index_manager._index, vector_ids_map
        
    except Exception as e:
        logger.error(f"[阶段2.1/2.2/2.3] ❌ 索引构建失败: {e}")
        raise
