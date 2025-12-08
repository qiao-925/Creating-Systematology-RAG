"""
Embedding缓存管理模块

主要功能：
- 管理BaseEmbedding缓存
- 提供缓存查询、设置、清除功能
- 提供状态查询功能

执行流程：
1. 管理BaseEmbedding缓存
2. 提供统一的缓存操作接口

特性：
- 统一缓存管理
- 状态查询功能
"""

from pathlib import Path
from typing import Optional

from src.infrastructure.embeddings.base import BaseEmbedding
from src.infrastructure.config import config
from src.infrastructure.logger import get_logger

logger = get_logger('embedding_cache')


def get_global_embedding() -> Optional[BaseEmbedding]:
    """获取全局BaseEmbedding缓存
    
    Returns:
        当前缓存的BaseEmbedding实例，如果没有则返回None
    """
    # 从factory模块获取缓存
    from src.infrastructure.embeddings.factory import get_embedding_instance
    return get_embedding_instance()


def set_global_embedding(embedding: BaseEmbedding) -> None:
    """设置全局BaseEmbedding缓存
    
    Args:
        embedding: BaseEmbedding实例
    """
    # 同步到factory的缓存
    import src.infrastructure.embeddings.factory as factory_module
    factory_module._global_embedding_instance = embedding
    logger.debug("🔧 设置全局BaseEmbedding缓存")


def clear_all_cache() -> None:
    """清除所有Embedding缓存"""
    from src.infrastructure.embeddings.factory import clear_embedding_cache
    clear_embedding_cache()


def get_embedding_status() -> dict:
    """获取Embedding状态信息
    
    Returns:
        包含模型状态的字典：
        {
            "base_embedding_loaded": bool,      # BaseEmbedding是否已加载
            "model_name": str,                   # 模型名称
            "cache_dir": str,                    # 缓存目录
            "cache_exists": bool,                # 本地缓存是否存在
            "offline_mode": bool,                # 是否离线模式
            "mirror": str,                       # 镜像地址
        }
    """
    model_name = config.EMBEDDING_MODEL
    
    # 检查缓存目录
    cache_root = Path.home() / ".cache" / "huggingface" / "hub"
    model_cache_name = model_name.replace("/", "--")
    cache_dir = cache_root / f"models--{model_cache_name}"
    cache_exists = cache_dir.exists()
    
    base_embedding = get_global_embedding()
    
    return {
        "base_embedding_loaded": base_embedding is not None,
        "model_name": model_name,
        "cache_dir": str(cache_dir),
        "cache_exists": cache_exists,
        "offline_mode": config.HF_OFFLINE_MODE,
        "mirror": config.HF_ENDPOINT if config.HF_ENDPOINT else "huggingface.co (官方)",
    }
