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

注意：为了优化启动时间，大部分导入已改为延迟导入。
如需使用这些类，请直接从子模块导入，例如：
    from backend.business.rag_engine.core.engine import ModularQueryEngine
"""

# 延迟导入：只在实际使用时才导入耗时的模块
def __getattr__(name):
    """延迟导入支持"""
    if name == 'ModularQueryEngine':
        from backend.business.rag_engine.core.engine import ModularQueryEngine
        return ModularQueryEngine
    elif name == 'QueryEngine':
        from backend.business.rag_engine.core.legacy_engine import QueryEngine
        return QueryEngine
    elif name == 'SimpleQueryEngine':
        from backend.business.rag_engine.core.simple_engine import SimpleQueryEngine
        return SimpleQueryEngine
    elif name == 'ResponseFormatter':
        from backend.business.rag_engine.formatting import ResponseFormatter
        return ResponseFormatter
    elif name == 'GrepRetriever':
        from backend.business.rag_engine.retrieval.strategies.grep import GrepRetriever
        return GrepRetriever
    elif name == 'MultiStrategyRetriever':
        from backend.business.rag_engine.retrieval.strategies.multi_strategy import MultiStrategyRetriever
        return MultiStrategyRetriever
    elif name == 'BaseRetriever':
        from backend.business.rag_engine.retrieval.strategies.multi_strategy import BaseRetriever
        return BaseRetriever
    elif name == 'ResultMerger':
        from backend.business.rag_engine.retrieval.merger import ResultMerger
        return ResultMerger
    elif name == 'BaseReranker':
        from backend.business.rag_engine.reranking.base import BaseReranker
        return BaseReranker
    elif name == 'BGEReranker':
        from backend.business.rag_engine.reranking.strategies.bge import BGEReranker
        return BGEReranker
    elif name == 'SentenceTransformerReranker':
        from backend.business.rag_engine.reranking.strategies.sentence_transformer import SentenceTransformerReranker
        return SentenceTransformerReranker
    elif name == 'create_reranker':
        from backend.business.rag_engine.reranking.factory import create_reranker
        return create_reranker
    elif name == 'clear_reranker_cache':
        from backend.business.rag_engine.reranking.factory import clear_reranker_cache
        return clear_reranker_cache
    elif name == 'QueryRouter':
        from backend.business.rag_engine.routing.query_router import QueryRouter
        return QueryRouter
    elif name == 'QueryProcessor':
        from backend.business.rag_engine.processing.query_processor import QueryProcessor
        return QueryProcessor
    elif name == 'get_query_processor':
        from backend.business.rag_engine.processing.query_processor import get_query_processor
        return get_query_processor
    elif name == 'reset_query_processor':
        from backend.business.rag_engine.processing.query_processor import reset_query_processor
        return reset_query_processor
    elif name == 'execute_query':
        from backend.business.rag_engine.processing.execution import execute_query
        return execute_query
    elif name == 'create_postprocessors':
        from backend.business.rag_engine.processing.execution import create_postprocessors
        return create_postprocessors
    elif name == 'format_sources':
        from backend.business.rag_engine.utils.utils import format_sources
        return format_sources
    elif name == 'handle_fallback':
        from backend.business.rag_engine.utils.utils import handle_fallback
        return handle_fallback
    elif name == 'collect_trace_info':
        from backend.business.rag_engine.utils.utils import collect_trace_info
        return collect_trace_info
    elif name == 'extract_sources_from_response':
        from backend.business.rag_engine.utils.utils import extract_sources_from_response
        return extract_sources_from_response
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

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
