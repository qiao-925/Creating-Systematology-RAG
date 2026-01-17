"""
构建入口模块：构建或更新索引的入口函数
"""

import time
from typing import List, Optional, Tuple, Dict, TYPE_CHECKING

from llama_index.core.schema import Document as LlamaDocument

from backend.infrastructure.config import config, get_gpu_device
from backend.infrastructure.logger import get_logger
from backend.infrastructure.indexer.build.normal import build_index_normal_mode
from backend.infrastructure.indexer.build.filter import filter_vectorized_documents
from backend.infrastructure.indexer.utils.ids import get_vector_ids_batch

if TYPE_CHECKING:
    from backend.infrastructure.data_loader.github_sync.manager import GitHubSyncManager

logger = get_logger('indexer')


def build_index_method(
    index_manager,
    documents: List[LlamaDocument],
    show_progress: bool = True,
    github_sync_manager: Optional["GitHubSyncManager"] = None
) -> Tuple:
    """构建或更新索引（IndexManager的build_index方法实现）
    
    Args:
        index_manager: IndexManager实例
        documents: 文档列表
        show_progress: 是否显示进度
        github_sync_manager: GitHub同步管理器实例（可选）
        
    Returns:
        (索引, 向量ID映射)
    """
    start_time = time.time()
    
    logger.info(f"[阶段2.1] 📥 build_index 被调用，文档数: {len(documents) if documents else 0}")
    
    if not documents:
        logger.warning("[阶段2.1] ⚠️  没有文档可索引")
        return index_manager.get_index(), {}
    
    # 保存原始文档列表（用于中间层保存状态时查找元数据）
    all_documents = documents
    
    logger.info(f"[阶段2.1] 🔍 开始过滤已向量化文档...")
    logger.debug(f"[阶段2.1]    调用 filter_vectorized_documents，输入文档数: {len(documents)}")
    # 文档级断点续传
    try:
        documents_to_process, already_vectorized, already_vectorized_map = filter_vectorized_documents(
            index_manager, documents, github_sync_manager
        )
        logger.info(f"[阶段2.1] ✅ filter_vectorized_documents 调用完成")
        logger.debug(f"[阶段2.1]    返回结果: 待处理={len(documents_to_process)}, 已向量化={already_vectorized}, 已向量化文档向量ID映射={len(already_vectorized_map)}个文件")
    except Exception as e:
        logger.error(f"[阶段2.1] ❌ filter_vectorized_documents 调用失败: {e}", exc_info=True)
        raise
    
    if already_vectorized > 0:
        logger.info(f"[阶段2.1] ✅ 检测到 {already_vectorized} 个文档已向量化，跳过处理")
        logger.info(f"[阶段2.1] 📊 断点续传: {already_vectorized}/{len(documents)} 个文档已向量化，剩余 {len(documents_to_process)} 个待处理")
    
    if not documents_to_process:
        logger.info(f"[阶段2.1] ✅ 所有文档已向量化，跳过向量化步骤")
        index = index_manager.get_index()
        # 使用已向量化文档的向量ID映射
        vector_ids_map = already_vectorized_map
        
        # 中间层：保存已向量化文档的状态（使用原始文档列表查找元数据）
        if github_sync_manager and vector_ids_map:
            _save_vector_ids_middle_layer(
                github_sync_manager, vector_ids_map, all_documents
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
        index, new_vector_ids_map, metadata_map = build_index_normal_mode(
            index_manager, documents, show_progress, github_sync_manager
        )
        
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
        
        # 合并向量ID映射（已向量化 + 新处理）
        all_vector_ids_map = {**already_vectorized_map, **new_vector_ids_map}
        
        # 中间层：按文档逐个保存状态（使用原始文档列表查找元数据）
        if github_sync_manager and all_vector_ids_map:
            _save_vector_ids_middle_layer(
                github_sync_manager, all_vector_ids_map, all_documents, metadata_map
            )
        
        return index_manager._index, all_vector_ids_map
        
    except Exception as e:
        logger.error(f"[阶段2.1/2.2/2.3] ❌ 索引构建失败: {e}")
        raise


def _save_vector_ids_middle_layer(
    github_sync_manager: "GitHubSyncManager",
    vector_ids_map: Dict[str, List[str]],
    documents: List[LlamaDocument],
    metadata_map: Optional[Dict[str, Dict]] = None
) -> None:
    """中间层：按文档逐个保存向量ID状态（带重试机制）
    
    Args:
        github_sync_manager: GitHub同步管理器实例
        vector_ids_map: 向量ID映射
        documents: 文档列表（用于查找元数据）
        metadata_map: 文档元数据映射（可选，如果提供则优先使用）
    """
    if not vector_ids_map:
        return
    
    logger.info(f"[中间层] 开始保存向量ID状态，共 {len(vector_ids_map)} 个文件")
    
    # 创建文件路径到文档的映射（用于查找元数据）
    doc_map = {}
    for doc in documents:
        file_path = doc.metadata.get("file_path", "")
        if file_path:
            doc_map[file_path] = doc
    
    saved_count = 0
    skipped_count = 0
    failed_count = 0
    
    for file_path, vector_ids in vector_ids_map.items():
        # 提取元数据
        if metadata_map and file_path in metadata_map:
            metadata = metadata_map[file_path]
            repository = metadata.get("repository", "")
            branch = metadata.get("branch", "main")
        elif file_path in doc_map:
            doc = doc_map[file_path]
            repository = doc.metadata.get("repository", "")
            branch = doc.metadata.get("branch", "main")
        else:
            logger.warning(f"[中间层] 无法找到文档元数据 [{file_path}]，跳过状态保存")
            skipped_count += 1
            continue
        
        # 元数据完整性检查
        if not repository or "/" not in repository:
            logger.warning(f"[中间层] 文档元数据不完整 [{file_path}]，跳过状态保存")
            skipped_count += 1
            continue
        
        owner, repo = repository.split("/", 1)
        if not owner or not repo:
            logger.warning(f"[中间层] 文档元数据格式错误 [{file_path}]，跳过状态保存")
            skipped_count += 1
            continue
        
        # 更新并保存（带重试）
        success = False
        for retry in range(3):
            try:
                github_sync_manager.update_file_vector_ids(
                    owner, repo, branch, file_path, vector_ids
                )
                github_sync_manager.save_sync_state()
                success = True
                saved_count += 1
                break
            except Exception as e:
                if retry < 2:
                    delay = 0.1 * (retry + 1)  # 递增延迟
                    logger.warning(f"[中间层] 保存状态失败 [{file_path}] (重试 {retry + 1}/3): {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"[中间层] 保存状态最终失败 [{file_path}]: {e}")
        
        if not success:
            failed_count += 1
            logger.warning(f"[中间层] 状态保存失败 [{file_path}]，继续处理其他文档")
    
    logger.info(
        f"[中间层] 状态保存完成: "
        f"成功={saved_count}, 跳过={skipped_count}, 失败={failed_count}, "
        f"总计={len(vector_ids_map)}"
    )
