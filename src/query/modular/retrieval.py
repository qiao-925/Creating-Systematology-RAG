"""
模块化查询引擎 - 检索模块
检索器创建逻辑
"""

from typing import Optional

from src.indexer import IndexManager
from src.logger import setup_logger
from src.config import config

logger = setup_logger('modular_query_engine')


def create_retriever(
    index_manager: IndexManager,
    retrieval_strategy: str,
    similarity_top_k: int,
    **kwargs
):
    """创建检索器
    
    Args:
        index_manager: 索引管理器
        retrieval_strategy: 检索策略
        similarity_top_k: Top-K值
        **kwargs: 其他参数
        
    Returns:
        检索器实例
    """
    index = index_manager.get_index()
    
    if retrieval_strategy == "vector":
        # 向量检索
        return index.as_retriever(similarity_top_k=similarity_top_k)
    
    elif retrieval_strategy == "bm25":
        # BM25检索
        try:
            from llama_index.core.retrievers import BM25Retriever
            return BM25Retriever.from_defaults(
                index=index,
                similarity_top_k=similarity_top_k
            )
        except ImportError:
            logger.warning("BM25Retriever不可用，降级到向量检索")
            return index.as_retriever(similarity_top_k=similarity_top_k)
    
    elif retrieval_strategy == "hybrid":
        # 混合检索
        try:
            from llama_index.core.retrievers import VectorIndexRetriever
            from llama_index.core.retrievers import BM25Retriever
            from llama_index.core.retrievers import FusionRetriever
            
            vector_retriever = VectorIndexRetriever(index=index, similarity_top_k=similarity_top_k)
            bm25_retriever = BM25Retriever.from_defaults(index=index, similarity_top_k=similarity_top_k)
            
            hybrid_alpha = kwargs.get('hybrid_alpha', config.HYBRID_ALPHA)
            
            return FusionRetriever(
                retrievers=[vector_retriever, bm25_retriever],
                weights=[hybrid_alpha, 1 - hybrid_alpha]
            )
        except ImportError:
            logger.warning("混合检索器不可用，降级到向量检索")
            return index.as_retriever(similarity_top_k=similarity_top_k)
    
    else:
        logger.warning(f"未知检索策略: {retrieval_strategy}，使用向量检索")
        return index.as_retriever(similarity_top_k=similarity_top_k)

