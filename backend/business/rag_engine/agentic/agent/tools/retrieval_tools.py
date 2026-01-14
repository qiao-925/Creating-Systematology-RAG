"""
检索工具封装模块：将检索器封装为 LlamaIndex Tool

主要功能：
- create_retrieval_tools()：创建3个检索工具（vector/hybrid/multi）
- 每个工具内部调用 create_retriever() 和 create_postprocessors()
- 使用 QueryEngineTool 包装为 LlamaIndex Tool
"""

from typing import List, Optional
from llama_index.core import VectorStoreIndex
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.tools import QueryEngineTool

from backend.infrastructure.indexer import IndexManager
from backend.infrastructure.logger import get_logger
from backend.business.rag_engine.retrieval.factory import create_retriever
from backend.business.rag_engine.processing.execution import create_postprocessors
from backend.infrastructure.config import config

logger = get_logger('rag_engine.agentic.tools')


def create_retrieval_tools(
    index_manager: IndexManager,
    llm,
    similarity_top_k: Optional[int] = None,
    similarity_cutoff: Optional[float] = None,
    enable_rerank: Optional[bool] = None,
    rerank_top_n: Optional[int] = None,
    reranker_type: Optional[str] = None,
) -> List[QueryEngineTool]:
    """创建检索工具列表（vector/hybrid/multi）
    
    Args:
        index_manager: 索引管理器
        llm: LLM 实例
        similarity_top_k: Top-K值（可选，默认使用配置）
        similarity_cutoff: 相似度阈值（可选，默认使用配置）
        enable_rerank: 是否启用重排序（可选，默认使用配置）
        rerank_top_n: 重排序Top-N（可选，默认使用配置）
        reranker_type: 重排序器类型（可选，默认使用配置）
        
    Returns:
        检索工具列表（QueryEngineTool实例）
    """
    index = index_manager.get_index()
    top_k = similarity_top_k or config.SIMILARITY_TOP_K
    cutoff = similarity_cutoff if similarity_cutoff is not None else config.SIMILARITY_CUTOFF
    rerank_enabled = enable_rerank if enable_rerank is not None else config.ENABLE_RERANK
    rerank_n = rerank_top_n or config.RERANK_TOP_N
    
    # 创建后处理器（所有工具共享相同的后处理器配置）
    postprocessors = create_postprocessors(
        index_manager=index_manager,
        similarity_cutoff=cutoff,
        enable_rerank=rerank_enabled,
        rerank_top_n=rerank_n,
        reranker_type=reranker_type,
    )
    
    tools = []
    
    # 1. Vector Search Tool
    vector_tool = _create_vector_search_tool(
        index=index,
        llm=llm,
        top_k=top_k,
        postprocessors=postprocessors,
    )
    tools.append(vector_tool)
    
    # 2. Hybrid Search Tool
    hybrid_tool = _create_hybrid_search_tool(
        index=index,
        llm=llm,
        top_k=top_k,
        postprocessors=postprocessors,
    )
    tools.append(hybrid_tool)
    
    # 3. Multi Search Tool
    multi_tool = _create_multi_search_tool(
        index=index,
        llm=llm,
        top_k=top_k,
        postprocessors=postprocessors,
    )
    tools.append(multi_tool)
    
    logger.info(
        "创建检索工具完成",
        tool_count=len(tools),
        strategies=["vector", "hybrid", "multi"]
    )
    
    return tools


def _create_vector_search_tool(
    index: VectorStoreIndex,
    llm,
    top_k: int,
    postprocessors: List,
) -> QueryEngineTool:
    """创建向量检索工具
    
    Args:
        index: 向量索引
        llm: LLM 实例
        top_k: Top-K值
        postprocessors: 后处理器列表
        
    Returns:
        QueryEngineTool实例
    """
    retriever = create_retriever(
        index=index,
        retrieval_strategy="vector",
        similarity_top_k=top_k,
    )
    
    query_engine = RetrieverQueryEngine.from_args(
        retriever=retriever,
        llm=llm,
        node_postprocessors=postprocessors,
    )
    
    tool = QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name="vector_search",
        description=(
            "向量检索工具：适合概念理解、语义相似查询。"
            "使用向量相似度搜索，能够理解查询的语义含义，"
            "找到语义上最相关的文档片段。"
        ),
    )
    
    logger.debug("创建向量检索工具", name="vector_search")
    return tool


def _create_hybrid_search_tool(
    index: VectorStoreIndex,
    llm,
    top_k: int,
    postprocessors: List,
) -> QueryEngineTool:
    """创建混合检索工具
    
    Args:
        index: 向量索引
        llm: LLM 实例
        top_k: Top-K值
        postprocessors: 后处理器列表
        
    Returns:
        QueryEngineTool实例
    """
    retriever = create_retriever(
        index=index,
        retrieval_strategy="hybrid",
        similarity_top_k=top_k,
    )
    
    query_engine = RetrieverQueryEngine.from_args(
        retriever=retriever,
        llm=llm,
        node_postprocessors=postprocessors,
    )
    
    tool = QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name="hybrid_search",
        description=(
            "混合检索工具：适合需要平衡精度和召回的查询。"
            "结合向量检索和BM25关键词检索，既考虑语义相似度，"
            "也考虑关键词匹配，能够提供更全面的检索结果。"
        ),
    )
    
    logger.debug("创建混合检索工具", name="hybrid_search")
    return tool


def _create_multi_search_tool(
    index: VectorStoreIndex,
    llm,
    top_k: int,
    postprocessors: List,
) -> QueryEngineTool:
    """创建多策略检索工具
    
    Args:
        index: 向量索引
        llm: LLM 实例
        top_k: Top-K值
        postprocessors: 后处理器列表
        
    Returns:
        QueryEngineTool实例
    """
    retriever = create_retriever(
        index=index,
        retrieval_strategy="multi",
        similarity_top_k=top_k,
    )
    
    query_engine = RetrieverQueryEngine.from_args(
        retriever=retriever,
        llm=llm,
        node_postprocessors=postprocessors,
    )
    
    tool = QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name="multi_search",
        description=(
            "多策略检索工具：适合复杂查询、需要全面检索。"
            "同时使用多种检索策略（向量、BM25、Grep等），"
            "合并结果，能够提供最全面的检索覆盖。"
        ),
    )
    
    logger.debug("创建多策略检索工具", name="multi_search")
    return tool

