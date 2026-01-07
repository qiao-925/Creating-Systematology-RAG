"""
RAG引擎重排序模块 - 重排序器工厂：创建和管理重排序器实例

主要功能：
- create_reranker()：创建重排序器实例（工厂函数），支持sentence-transformer、bge等类型
- clear_reranker_cache()：清除重排序器缓存

执行流程：
1. 检查缓存（如果启用）
2. 根据类型创建相应的重排序器实例
3. 缓存实例并返回

特性：
- 支持多种重排序器类型
- 单例模式缓存
- 支持强制重新加载
- 自动配置管理
"""

from typing import Optional
from backend.business.rag_engine.reranking.base import BaseReranker
from backend.business.rag_engine.reranking.strategies.sentence_transformer import SentenceTransformerReranker
from backend.business.rag_engine.reranking.strategies.bge import BGEReranker
from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger('rag_engine.reranking.factory')

# 全局重排序器缓存
_reranker_cache: dict = {}


def create_reranker(
    reranker_type: Optional[str] = None,
    model: Optional[str] = None,
    top_n: Optional[int] = None,
    use_cache: bool = True,
) -> Optional[BaseReranker]:
    """创建重排序器
    
    Args:
        reranker_type: 重排序器类型（"sentence-transformer" | "bge" | "none"）
        model: 模型名称（可选）
        top_n: Top-N数量（可选）
        use_cache: 是否使用缓存
        
    Returns:
        重排序器实例，如果type为"none"则返回None
    """
    # 使用配置默认值
    reranker_type = reranker_type or config.RERANKER_TYPE or "sentence-transformer"
    
    # 如果禁用重排序
    if reranker_type == "none":
        logger.info("重排序已禁用")
        return None
    
    # 检查缓存
    cache_key = f"{reranker_type}:{model}:{top_n}"
    if use_cache and cache_key in _reranker_cache:
        logger.debug(f"使用缓存的重排序器: {cache_key}")
        return _reranker_cache[cache_key]
    
    # 创建重排序器
    reranker = None
    
    match reranker_type:
        case "sentence-transformer":
            logger.info(f"创建SentenceTransformer重排序器")
            reranker = SentenceTransformerReranker(
                model=model,
                top_n=top_n,
            )
        
        case "bge":
            logger.info(f"创建BGE重排序器")
            reranker = BGEReranker(
                model=model,
                top_n=top_n,
            )
        
        case _:
            logger.warning(f"未知的重排序器类型: {reranker_type}，使用默认SentenceTransformer")
            reranker = SentenceTransformerReranker(
                model=model,
                top_n=top_n,
            )
    
    # 缓存
    if use_cache and reranker:
        _reranker_cache[cache_key] = reranker
    
    return reranker


def clear_reranker_cache() -> None:
    """清除重排序器缓存"""
    global _reranker_cache
    _reranker_cache.clear()
    logger.info("重排序器缓存已清除")
