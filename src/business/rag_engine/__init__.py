"""
RAG引擎模块 - 完整的RAG流程引擎

主要功能：
- ModularQueryEngine类：模块化查询引擎（推荐使用）
- QueryEngine类：遗留查询引擎
- SimpleQueryEngine类：简单查询引擎
- 检索、重排序、格式化、路由等完整RAG流程

模块结构：
- core/：核心查询引擎实现
- retrieval/：检索策略和适配器
- reranking/：重排序策略
- formatting/：响应格式化
- routing/：查询路由
- processing/：查询处理和执行
- utils/：工具函数
"""

# 核心引擎
from src.business.rag_engine.core.engine import ModularQueryEngine
from src.business.rag_engine.core.legacy_engine import QueryEngine
from src.business.rag_engine.core.simple_engine import SimpleQueryEngine

# 格式化
from src.business.rag_engine.formatting import ResponseFormatter

# 检索
from src.business.rag_engine.retrieval.strategies.grep import GrepRetriever
from src.business.rag_engine.retrieval.strategies.multi_strategy import MultiStrategyRetriever, BaseRetriever
from src.business.rag_engine.retrieval.merger import ResultMerger

# 重排序
from src.business.rag_engine.reranking.base import BaseReranker
from src.business.rag_engine.reranking.strategies.bge import BGEReranker
from src.business.rag_engine.reranking.strategies.sentence_transformer import SentenceTransformerReranker
from src.business.rag_engine.reranking.factory import create_reranker, clear_reranker_cache

# 路由
from src.business.rag_engine.routing.query_router import QueryRouter

# 处理
from src.business.rag_engine.processing.query_processor import QueryProcessor, get_query_processor, reset_query_processor
from src.business.rag_engine.processing.execution import execute_query, create_postprocessors

# 工具函数
from src.business.rag_engine.utils.utils import (
    format_sources,
    handle_fallback,
    collect_trace_info,
    extract_sources_from_response,
)

__all__ = [
    # 核心引擎
    'ModularQueryEngine',
    'QueryEngine',  # 遗留实现（推荐使用 ModularQueryEngine）
    'SimpleQueryEngine',
    # 格式化
    'ResponseFormatter',
    # 检索
    'GrepRetriever',
    'MultiStrategyRetriever',
    'BaseRetriever',
    'ResultMerger',
    # 重排序
    'BaseReranker',
    'BGEReranker',
    'SentenceTransformerReranker',
    'create_reranker',
    'clear_reranker_cache',
    # 路由
    'QueryRouter',
    # 处理
    'QueryProcessor',
    'get_query_processor',
    'reset_query_processor',
    'execute_query',
    'create_postprocessors',
    # 工具函数
    'format_sources',
    'handle_fallback',
    'collect_trace_info',
    'extract_sources_from_response',
]
