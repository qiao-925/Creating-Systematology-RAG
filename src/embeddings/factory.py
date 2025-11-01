"""
Embedding工厂函数
根据配置创建合适的Embedding实例
"""

from typing import Optional
from src.embeddings.base import BaseEmbedding
from src.embeddings.local_embedding import LocalEmbedding
from src.embeddings.api_embedding import APIEmbedding
from src.config import config
from src.logger import setup_logger

logger = setup_logger('embedding_factory')

# 全局Embedding实例缓存（单例模式）
_global_embedding_instance: Optional[BaseEmbedding] = None


def create_embedding(
    embedding_type: Optional[str] = None,
    model_name: Optional[str] = None,
    api_url: Optional[str] = None,
    force_reload: bool = False,
    **kwargs
) -> BaseEmbedding:
    """创建Embedding实例（工厂函数）
    
    Args:
        embedding_type: Embedding类型（"local"|"api"，默认使用配置）
        model_name: 模型名称（默认使用配置）
        api_url: API地址（仅API类型需要）
        force_reload: 是否强制重新创建（忽略缓存）
        **kwargs: 其他参数
        
    Returns:
        BaseEmbedding实例
        
    Raises:
        ValueError: 不支持的Embedding类型
    """
    global _global_embedding_instance
    
    # 使用配置中的默认值
    embedding_type = embedding_type or config.EMBEDDING_TYPE
    model_name = model_name or config.EMBEDDING_MODEL
    
    # 如果已有缓存且不强制重载，返回缓存
    if _global_embedding_instance is not None and not force_reload:
        cached_type = type(_global_embedding_instance).__name__
        cached_model = _global_embedding_instance.get_model_name()
        
        logger.info(f"✅ 使用缓存的Embedding实例")
        logger.info(f"   类型: {cached_type}")
        logger.info(f"   模型: {cached_model}")
        
        return _global_embedding_instance
    
    # 创建新实例
    logger.info(f"📦 创建新的Embedding实例")
    logger.info(f"   类型: {embedding_type}")
    logger.info(f"   模型: {model_name}")
    
    if embedding_type == "local":
        _global_embedding_instance = LocalEmbedding(
            model_name=model_name,
            **kwargs
        )
    elif embedding_type == "api":
        api_url = api_url or getattr(config, 'EMBEDDING_API_URL', None)
        if not api_url:
            raise ValueError("API类型需要提供api_url参数或配置EMBEDDING_API_URL")
        
        _global_embedding_instance = APIEmbedding(
            api_url=api_url,
            model_name=model_name,
            **kwargs
        )
    else:
        raise ValueError(
            f"不支持的Embedding类型: {embedding_type}. "
            f"支持的类型: local, api"
        )
    
    logger.info(f"✅ Embedding实例创建完成: {_global_embedding_instance}")
    
    return _global_embedding_instance


def get_embedding_instance() -> Optional[BaseEmbedding]:
    """获取当前缓存的Embedding实例
    
    Returns:
        当前缓存的实例，如果没有则返回None
    """
    return _global_embedding_instance


def clear_embedding_cache():
    """清除Embedding缓存
    
    用于切换模型或重新加载
    """
    global _global_embedding_instance
    
    if _global_embedding_instance is not None:
        logger.info("🧹 清除Embedding缓存")
        _global_embedding_instance = None
    else:
        logger.info("ℹ️  Embedding缓存已为空")


def reload_embedding(**kwargs) -> BaseEmbedding:
    """重新加载Embedding
    
    清除缓存并创建新实例
    
    Args:
        **kwargs: 传递给create_embedding的参数
        
    Returns:
        新的BaseEmbedding实例
    """
    logger.info("🔄 重新加载Embedding")
    clear_embedding_cache()
    return create_embedding(force_reload=True, **kwargs)

