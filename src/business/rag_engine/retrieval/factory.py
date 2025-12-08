"""
RAG引擎检索模块 - 检索器工厂：检索器创建逻辑
"""

from typing import Optional, List, Any, Union, TYPE_CHECKING

from llama_index.core.retrievers import VectorIndexRetriever, QueryFusionRetriever
from llama_index.core import VectorStoreIndex
from src.infrastructure.logger import get_logger
from src.infrastructure.config import config
from src.business.rag_engine.retrieval.strategies.grep import GrepRetriever
from src.business.rag_engine.retrieval.strategies.multi_strategy import MultiStrategyRetriever, BaseRetriever
from src.business.rag_engine.retrieval.adapters import (
    LlamaIndexRetrieverAdapter,
    MultiStrategyRetrieverAdapter,
    GrepRetrieverAdapter,
)

logger = get_logger('rag_engine.retrieval')


def create_retriever(index: VectorStoreIndex, retrieval_strategy: str, similarity_top_k: int) -> Union[Any, VectorIndexRetriever, QueryFusionRetriever]:
    """创建检索器（根据策略）
    
    Args:
        index: VectorStoreIndex实例
        retrieval_strategy: 检索策略
        similarity_top_k: Top-K值
        
    Returns:
        检索器实例（LlamaIndex检索器或MultiStrategyRetriever）
    """
    # 多策略检索
    if retrieval_strategy == "multi":
        logger.info("创建多策略检索器", strategy=retrieval_strategy)
        return _create_multi_strategy_retriever(index, similarity_top_k)
    
    # Grep检索
    elif retrieval_strategy == "grep":
        logger.info("创建Grep检索器", strategy=retrieval_strategy)
        grep_retriever = _create_grep_retriever()
        return GrepRetrieverAdapter(grep_retriever)
    
    # 传统检索策略
    elif retrieval_strategy == "vector":
        logger.info("创建向量检索器", strategy=retrieval_strategy, top_k=similarity_top_k)
        return VectorIndexRetriever(
            index=index,
            similarity_top_k=similarity_top_k,
        )
    
    elif retrieval_strategy == "bm25":
        logger.info("创建BM25检索器", strategy=retrieval_strategy, top_k=similarity_top_k)
        try:
            from llama_index.retrievers.bm25 import BM25Retriever
        except ImportError:
            logger.error("BM25Retriever未安装", error="请运行: pip install llama-index-retrievers-bm25")
            raise ImportError(
                "BM25Retriever未安装。请运行: pip install llama-index-retrievers-bm25"
            )
        
        nodes = list(index.docstore.docs.values())
        
        return BM25Retriever.from_defaults(
            nodes=nodes,
            similarity_top_k=similarity_top_k,
        )
    
    elif retrieval_strategy == "hybrid":
        logger.info("创建混合检索器", strategy=retrieval_strategy, top_k=similarity_top_k)
        try:
            from llama_index.retrievers.bm25 import BM25Retriever
        except ImportError:
            logger.warning("BM25未安装，降级为纯向量检索", strategy=retrieval_strategy)
            return VectorIndexRetriever(
                index=index,
                similarity_top_k=similarity_top_k,
            )
        
        vector_retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=similarity_top_k,
        )
        
        nodes = list(index.docstore.docs.values())
        bm25_retriever = BM25Retriever.from_defaults(
            nodes=nodes,
            similarity_top_k=similarity_top_k,
        )
        
        return QueryFusionRetriever(
            retrievers=[vector_retriever, bm25_retriever],
            similarity_top_k=similarity_top_k,
            num_queries=1,
            mode="reciprocal_rerank",
            use_async=False,
        )
    else:
        raise ValueError(f"不支持的检索策略: {retrieval_strategy}")


def _create_grep_retriever() -> GrepRetriever:
    """创建Grep检索器"""
    return GrepRetriever(
        data_source_path=config.GREP_DATA_SOURCE_PATH,
        enable_regex=config.GREP_ENABLE_REGEX,
        max_results=config.GREP_MAX_RESULTS,
    )


def _create_multi_strategy_retriever(index: VectorStoreIndex, similarity_top_k: int) -> MultiStrategyRetriever:
    """创建多策略检索器"""
    retrievers: List[BaseRetriever] = []
    
    # 创建各个检索器
    enabled_strategies = config.ENABLED_RETRIEVAL_STRATEGIES or ["vector"]
    
    if "vector" in enabled_strategies:
        vector_retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=similarity_top_k,
        )
        retrievers.append(LlamaIndexRetrieverAdapter(vector_retriever, "vector"))
    
    if "bm25" in enabled_strategies:
        try:
            from llama_index.retrievers.bm25 import BM25Retriever
            nodes = list(index.docstore.docs.values())
            bm25_retriever = BM25Retriever.from_defaults(
                nodes=nodes,
                similarity_top_k=similarity_top_k,
            )
            retrievers.append(LlamaIndexRetrieverAdapter(bm25_retriever, "bm25"))
        except ImportError:
            logger.warning("BM25Retriever未安装，跳过BM25策略", enabled_strategies=enabled_strategies)
    
    if "grep" in enabled_strategies:
        grep_retriever = _create_grep_retriever()
        retrievers.append(grep_retriever)
    
    if not retrievers:
        logger.warning("没有启用的检索策略，使用默认向量检索", enabled_strategies=enabled_strategies)
        vector_retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=similarity_top_k,
        )
        retrievers.append(LlamaIndexRetrieverAdapter(vector_retriever, "vector"))
    
    # 创建多策略检索器
    multi_retriever = MultiStrategyRetriever(
        retrievers=retrievers,
        merge_strategy=config.MERGE_STRATEGY,
        weights=config.RETRIEVER_WEIGHTS,
        enable_deduplication=config.ENABLE_DEDUPLICATION,
    )
    
    # 返回适配器（因为MultiStrategyRetriever已经实现了BaseRetriever接口）
    # 但我们需要将其适配为LlamaIndex检索器接口
    return MultiStrategyRetrieverAdapter(multi_retriever)
