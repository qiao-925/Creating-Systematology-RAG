"""
RAG引擎执行模块：负责查询引擎的创建和执行

主要功能：
- 从检索器创建查询引擎
- 获取或创建查询引擎（支持自动路由）
- 执行查询
"""

from typing import Optional, Tuple, Dict, Any

from llama_index.core import get_response_synthesizer
from llama_index.core.query_engine import RetrieverQueryEngine

from backend.infrastructure.logger import get_logger
from backend.business.rag_engine.processing.execution import execute_query

logger = get_logger('rag_engine')


def create_query_engine_from_retriever(
    retriever,
    llm,
    postprocessors,
    streaming: bool = False
) -> RetrieverQueryEngine:
    """从检索器创建查询引擎
    
    Args:
        retriever: 检索器实例
        llm: LLM实例
        postprocessors: 后处理器列表
        streaming: 是否启用流式输出
        
    Returns:
        RetrieverQueryEngine实例
    """
    if streaming:
        response_synthesizer = get_response_synthesizer(
            streaming=True,
            llm=llm
        )
        return RetrieverQueryEngine(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
            node_postprocessors=postprocessors,
        )
    else:
        return RetrieverQueryEngine.from_args(
            retriever=retriever,
            llm=llm,
            node_postprocessors=postprocessors,
        )


def get_or_create_query_engine(
    enable_auto_routing: bool,
    query_router,
    retriever,
    query_engine,
    retrieval_strategy: str,
    similarity_top_k: int,
    final_query: str,
    understanding: Optional[Dict[str, Any]] = None,
    streaming: bool = False,
    create_query_engine_func=None
) -> Tuple[RetrieverQueryEngine, str]:
    """获取或创建查询引擎（支持自动路由）
    
    Args:
        enable_auto_routing: 是否启用自动路由
        query_router: 查询路由器
        retriever: 检索器
        query_engine: 查询引擎
        retrieval_strategy: 检索策略
        similarity_top_k: 相似度top_k
        final_query: 处理后的查询
        understanding: 查询理解结果（可选）
        streaming: 是否启用流式输出
        create_query_engine_func: 创建查询引擎的函数
        
    Returns:
        (查询引擎实例, 路由决策/策略名称)
    """
    if enable_auto_routing and query_router:
        # 自动路由模式：根据查询意图动态选择检索器
        if understanding:
            retriever, routing_decision = query_router.route_with_understanding(
                final_query,
                understanding=understanding,
                top_k=similarity_top_k
            )
        else:
            retriever, routing_decision = query_router.route(
                final_query,
                top_k=similarity_top_k
            )
        
        query_engine = create_query_engine_func(retriever, streaming=streaming)
        strategy_info = f"策略={routing_decision}, 原因=自动路由模式，根据查询意图动态选择"
        return query_engine, strategy_info
    else:
        # 固定模式：使用初始化时创建的查询引擎
        if streaming:
            current_retriever = retriever
            if current_retriever:
                query_engine = create_query_engine_func(current_retriever, streaming=True)
                strategy_info = f"策略={retrieval_strategy}, 原因=固定检索模式（流式）"
                return query_engine, strategy_info
        strategy_info = f"策略={retrieval_strategy}, 原因=固定检索模式（初始化时配置）"
        return query_engine, strategy_info


def execute_with_query_engine(
    query_engine: RetrieverQueryEngine,
    formatter,
    observer_manager,
    final_query: str,
    collect_trace: bool,
    retrieval_strategy: str,
    similarity_top_k: int,
    query_processing_result: Optional[Dict[str, Any]] = None
) -> Tuple[str, list, Optional[str], Optional[Dict[str, Any]]]:
    """使用查询引擎执行查询
    
    Args:
        query_engine: 查询引擎实例
        formatter: 响应格式化器
        observer_manager: 观察器管理器
        final_query: 处理后的查询
        collect_trace: 是否收集追踪信息
        retrieval_strategy: 检索策略
        similarity_top_k: 相似度top_k
        query_processing_result: 查询处理结果（包含改写、意图理解等）
        
    Returns:
        (答案, 引用来源, 推理链内容, 追踪信息)
    """
    return execute_query(
        query_engine,
        formatter,
        observer_manager,
        final_query,
        collect_trace,
        query_processing_result=query_processing_result,
        retrieval_strategy=retrieval_strategy,
        similarity_top_k=similarity_top_k,
    )
