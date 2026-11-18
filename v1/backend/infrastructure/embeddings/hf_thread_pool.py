"""
Hugging Face Inference API 线程池管理

主要功能：
- 全局线程池创建和管理
- 资源清理函数
"""

import os
import threading
import weakref
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from backend.infrastructure.logger import get_logger

logger = get_logger('hf_thread_pool')

# 全局线程池实例
_global_executor: Optional[ThreadPoolExecutor] = None
_executor_lock = threading.Lock()
_embedding_instances: weakref.WeakSet = weakref.WeakSet()


def _get_or_create_executor() -> ThreadPoolExecutor:
    """获取或创建全局线程池执行器
    
    Returns:
        ThreadPoolExecutor: 全局线程池执行器
    """
    global _global_executor
    if _global_executor is None:
        max_workers = min(32, (os.cpu_count() or 1) * 2)
        _global_executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="hf_embedding")
        logger.debug(f"创建全局线程池执行器: max_workers={max_workers}")
    return _global_executor


def register_embedding_instance(instance):
    """注册 embedding 实例到全局集合"""
    _embedding_instances.add(instance)


def cleanup_hf_embedding_resources() -> None:
    """清理所有 HFInferenceEmbedding 资源和线程池"""
    global _global_executor
    
    logger.info("🔧 开始清理 Hugging Face Embedding 资源...")
    
    # 1. 关闭所有 HFInferenceEmbedding 实例
    instances_to_close = list(_embedding_instances)
    if instances_to_close:
        logger.info(f"关闭 {len(instances_to_close)} 个 HFInferenceEmbedding 实例...")
        for instance in instances_to_close:
            try:
                instance.close()
            except Exception as e:
                logger.warning(f"关闭 HFInferenceEmbedding 实例时出错: {e}")
    
    # 2. 关闭全局线程池执行器
    if _global_executor is not None:
        try:
            logger.info("关闭全局线程池执行器...")
            _global_executor.shutdown(wait=True, timeout=5.0)
            logger.info("✅ 全局线程池执行器已关闭")
        except Exception as e:
            logger.warning(f"关闭线程池执行器时出错: {e}")
        finally:
            _global_executor = None
    
    logger.info("✅ Hugging Face Embedding 资源清理完成")