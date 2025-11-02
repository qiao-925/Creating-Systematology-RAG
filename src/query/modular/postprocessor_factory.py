"""
模块化查询引擎 - 后处理器创建模块
后处理器创建逻辑
"""

from typing import List, Optional
from llama_index.core.postprocessor import SimilarityPostprocessor

from src.config import config
from src.logger import setup_logger
from src.rerankers.factory import create_reranker

logger = setup_logger('modular_query_engine')


def create_postprocessors(
    index_manager,
    similarity_cutoff: float,
    enable_rerank: bool,
    rerank_top_n: int,
    reranker_type: Optional[str] = None,
) -> List:
    """创建后处理器（链式组合）
    
    Args:
        index_manager: 索引管理器
        similarity_cutoff: 相似度阈值
        enable_rerank: 是否启用重排序
        rerank_top_n: 重排序Top-N
        reranker_type: 重排序器类型（可选，默认使用配置）
        
    Returns:
        后处理器列表
    """
    postprocessors = []
    
    # 1. 相似度过滤（总是启用）
    postprocessors.append(
        SimilarityPostprocessor(similarity_cutoff=similarity_cutoff)
    )
    logger.info(f"添加相似度过滤器: cutoff={similarity_cutoff}")
    
    # 2. 重排序（可选）
    if enable_rerank:
        try:
            # 使用工厂函数创建重排序器
            reranker = create_reranker(
                reranker_type=reranker_type,
                top_n=rerank_top_n,
            )
            
            if reranker:
                # 获取LlamaIndex兼容的Postprocessor
                llama_postprocessor = reranker.get_llama_index_postprocessor()
                if llama_postprocessor:
                    postprocessors.append(llama_postprocessor)
                    logger.info(
                        f"添加重排序模块: "
                        f"type={reranker.get_reranker_name()}, "
                        f"top_n={reranker.get_top_n()}"
                    )
                else:
                    logger.warning("重排序器未提供LlamaIndex Postprocessor，跳过")
            else:
                logger.info("重排序器类型为'none'，跳过重排序")
                
        except Exception as e:
            logger.warning(f"重排序模块初始化失败，跳过: {e}")
            print(f"⚠️  重排序模块初始化失败: {e}")
    
    return postprocessors

