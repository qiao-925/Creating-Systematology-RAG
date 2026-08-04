"""
Embedding工厂函数：根据配置创建合适的Embedding实例

主要功能：
- create_embedding()：创建Embedding实例（工厂函数），支持local、hf-inference类型
- 全局Embedding实例缓存（单例模式）

执行流程：
1. 检查全局缓存（如果force_reload=False）
2. 根据embedding_type创建相应的Embedding实例
3. 缓存实例并返回

特性：
- 支持两种Embedding类型（local、hf-inference）
- 单例模式缓存
- 支持强制重新加载
- 自动配置管理
"""

import os
from typing import Optional
from backend.infrastructure.embeddings.base import BaseEmbedding
from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger('embedding_factory')

# 全局Embedding实例缓存（单例模式）
_global_embedding_instance: Optional[BaseEmbedding] = None


def create_embedding(
    embedding_type: Optional[str] = None,
    model_name: Optional[str] = None,
    force_reload: bool = False,
    **kwargs
) -> BaseEmbedding:
    """创建Embedding实例（工厂函数）
    
    Args:
        embedding_type: Embedding类型（"local"|"hf-inference"，默认使用配置）
        model_name: 模型名称（默认使用配置）
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
        
        logger.info(f"✅ 使用缓存的Embedding实例: {cached_type} ({cached_model})")
        
        return _global_embedding_instance
    
    # 创建新实例
    logger.info(f"📦 创建新的Embedding实例: {embedding_type} ({model_name})")
    
    match embedding_type:
        case "local":
            raise ValueError(
                "Local embedding (sentence-transformers) has been removed. "
                "Use 'hf-inference' (HuggingFace Inference API) instead."
            )

        case "hf-inference":
            from backend.infrastructure.embeddings.hf_inference_embedding import HFInferenceEmbedding
            
            # 如果未提供 model_name，使用配置中的默认值
            if not model_name:
                model_name = config.EMBEDDING_MODEL
            
            # 处理 api_key 参数（从环境变量或配置读取）
            api_key = kwargs.get('api_key') or os.getenv("HF_TOKEN") or getattr(config, 'HF_TOKEN', None)
            
            if not api_key:
                raise ValueError(
                    "HF Inference API 需要设置 HF_TOKEN 环境变量或配置。"
                    "获取 Token: https://huggingface.co/settings/tokens"
                )
            
            # 从 kwargs 中移除 api_key，避免重复传递
            kwargs_without_key = {k: v for k, v in kwargs.items() if k != 'api_key'}
            
            _global_embedding_instance = HFInferenceEmbedding(
                model_name=model_name,
                api_key=api_key,
                **kwargs_without_key
            )
        
        case _:
            raise ValueError(
                f"不支持的Embedding类型: {embedding_type}. "
                f"支持的类型: local, hf-inference"
            )
    
    instance_type = type(_global_embedding_instance).__name__
    logger.info(f"✅ Embedding实例创建完成: {instance_type} ({model_name})")
    
    return _global_embedding_instance


def get_embedding_instance() -> Optional[BaseEmbedding]:
    """获取当前缓存的Embedding实例
    
    Returns:
        当前缓存的实例，如果没有则返回None
    """
    return _global_embedding_instance


def clear_embedding_cache() -> None:
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

