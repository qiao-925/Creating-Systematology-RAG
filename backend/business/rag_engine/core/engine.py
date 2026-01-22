"""
RAG引擎核心模块：ModularQueryEngine类实现

主要功能：
- ModularQueryEngine类：模块化查询引擎，支持vector、bm25、hybrid、grep、multi等策略
- query()：执行查询，返回格式化的回答和引用来源
- stream_query()：流式查询，实时返回答案token
"""

from typing import List, Optional, Tuple, Dict, Any
from llama_index.core.query_engine import RetrieverQueryEngine

from backend.infrastructure.indexer import IndexManager
from backend.infrastructure.logger import get_logger
from backend.business.rag_engine.formatting import ResponseFormatter
from backend.infrastructure.observers.manager import ObserverManager
from backend.business.rag_engine.processing.execution import create_postprocessors
from backend.business.rag_engine.processing.query_processor import QueryProcessor
from backend.business.rag_engine.utils.utils import handle_fallback
from backend.business.rag_engine.models import QueryContext, QueryResult, SourceModel
from backend.business.rag_engine.core.engine_setup import (
    load_engine_config,
    setup_observer_manager,
    setup_llm,
    setup_query_router,
    setup_retrieval_components,
    log_initialization_summary,
)
from backend.business.rag_engine.core.engine_execution import (
    create_query_engine_from_retriever,
    get_or_create_query_engine,
    execute_with_query_engine,
)
from backend.business.rag_engine.core.engine_streaming import execute_stream_query

logger = get_logger('rag_engine')


class ModularQueryEngine:
    """模块化查询引擎（工厂模式）"""
    
    SUPPORTED_STRATEGIES = ["vector", "bm25", "hybrid", "grep", "multi"]
    
    def __init__(
        self,
        index_manager: IndexManager,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        retrieval_strategy: Optional[str] = None,
        similarity_top_k: Optional[int] = None,
        enable_rerank: Optional[bool] = None,
        rerank_top_n: Optional[int] = None,
        reranker_type: Optional[str] = None,
        similarity_cutoff: Optional[float] = None,
        enable_markdown_formatting: bool = True,
        observer_manager: Optional[ObserverManager] = None,
        enable_auto_routing: Optional[bool] = None,
        **kwargs
    ):
        """初始化模块化查询引擎"""
        self.index_manager = index_manager
        self.index = index_manager.get_index()
        
        # 配置参数
        config_dict = load_engine_config(
            retrieval_strategy, similarity_top_k, enable_rerank,
            rerank_top_n, reranker_type, similarity_cutoff, enable_auto_routing,
            self.SUPPORTED_STRATEGIES
        )
        for key, value in config_dict.items():
            setattr(self, key, value)
        
        # 初始化组件
        self.formatter = ResponseFormatter(enable_formatting=enable_markdown_formatting)
        self.observer_manager = setup_observer_manager(observer_manager)
        self.llm = setup_llm(api_key, model)
        self.query_processor = QueryProcessor(llm=self.llm)
        logger.info("查询处理器已初始化", note="标准化流程：意图理解+改写")
        
        # 初始化路由和检索组件
        self.query_router = setup_query_router(index_manager, self.llm) if self.enable_auto_routing else None
        self.retriever, self.query_engine = setup_retrieval_components(
            self.index,
            self.retrieval_strategy,
            self.similarity_top_k,
            self.enable_auto_routing,
            lambda ret, stream=False: create_query_engine_from_retriever(
                ret, self.llm, self.postprocessors, stream
            )
        )
        self.postprocessors = create_postprocessors(
            self.index_manager,
            self.similarity_cutoff,
            self.enable_rerank,
            self.rerank_top_n,
            reranker_type=self.reranker_type,
        )
        
        log_initialization_summary(
            self.retrieval_strategy,
            self.similarity_top_k,
            self.enable_rerank,
            self.similarity_cutoff,
            self.enable_auto_routing
        )
    
    def _create_query_engine_from_retriever(self, retriever, streaming: bool = False) -> RetrieverQueryEngine:
        """从检索器创建查询引擎（包装函数）"""
        return create_query_engine_from_retriever(
            retriever, self.llm, self.postprocessors, streaming
        )
    
    def _get_or_create_query_engine(
        self,
        final_query: str,
        understanding: Optional[Dict[str, Any]] = None,
        streaming: bool = False
    ) -> Tuple[RetrieverQueryEngine, str]:
        """获取或创建查询引擎（支持自动路由）"""
        return get_or_create_query_engine(
            self.enable_auto_routing,
            self.query_router,
            self.retriever,
            self.query_engine,
            self.retrieval_strategy,
            self.similarity_top_k,
            final_query,
            understanding,
            streaming,
            self._create_query_engine_from_retriever
        )
    
    def _execute_with_query_engine(
        self,
        query_engine: RetrieverQueryEngine,
        final_query: str,
        collect_trace: bool,
        query_processing_result: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[dict], Optional[str], Optional[Dict[str, Any]]]:
        """使用查询引擎执行查询"""
        return execute_with_query_engine(
            query_engine,
            self.formatter,
            self.observer_manager,
            final_query,
            collect_trace,
            self.retrieval_strategy,
            self.similarity_top_k,
            query_processing_result
        )
    
    def query(
        self, 
        question: str, 
        collect_trace: bool = False
    ) -> Tuple[str, List[dict], Optional[str], Optional[Dict[str, Any]]]:
        """执行查询（兼容现有API）"""
        processed = self.query_processor.process(question)
        final_query = processed["final_query"]
        understanding = processed.get("understanding")
        
        logger.info(
            "查询处理完成",
            original_query=question[:50] if len(question) > 50 else question,
            processed_query=final_query[:50] if len(final_query) > 50 else final_query,
            processing_method=processed['processing_method']
        )
        
        query_engine, strategy_info = self._get_or_create_query_engine(final_query, understanding)
        logger.info("使用检索策略", strategy_info=strategy_info)
        
        answer, sources, reasoning_content, trace_info = self._execute_with_query_engine(
            query_engine, final_query, collect_trace, query_processing_result=processed
        )
        
        if collect_trace and trace_info:
            trace_info["original_query"] = question
            trace_info["processed_query"] = final_query
            trace_info["query_processing"] = processed
        
        answer, fallback_reason = handle_fallback(answer, sources, question, self.llm, self.similarity_cutoff)
        
        if collect_trace and trace_info:
            trace_info['fallback_used'] = bool(fallback_reason)
            trace_info['fallback_reason'] = fallback_reason
        
        return answer, sources, reasoning_content, trace_info
    
    def query_with_context(self, context: QueryContext) -> QueryResult:
        """执行查询（使用 QueryContext 和 QueryResult 模型）"""
        logger.info(
            "执行查询（使用上下文模型）",
            query=context.query[:50] if len(context.query) > 50 else context.query,
            user_id=context.user_id,
            session_id=context.session_id,
            strategy=context.strategy,
            top_k=context.top_k
        )
        
        query_text = context.processed_query or context.query
        answer, sources, reasoning_content, trace_info = self.query(
            query_text, collect_trace=bool(context.metadata.get('collect_trace', False))
        )
        
        source_models = []
        for source in sources:
            if isinstance(source, dict):
                source_models.append(SourceModel(**source))
            else:
                source_models.append(SourceModel(
                    text=source.get('text', ''),
                    score=source.get('score', 0.0),
                    metadata=source.get('metadata', {}),
                    file_name=source.get('file_name'),
                    page_number=source.get('page_number'),
                    node_id=source.get('node_id')
                ))
        
        result = QueryResult(
            answer=answer,
            sources=source_models,
            reasoning_content=reasoning_content,
            trace_info=trace_info,
            metadata={
                **context.metadata,
                'query': context.query,
                'processed_query': context.processed_query,
                'strategy': context.strategy,
                'top_k': context.top_k
            }
        )
        
        logger.info("查询完成", user_id=context.user_id, sources_count=len(result.sources), answer_len=len(answer))
        return result
    
    async def stream_query(self, question: str):
        """异步流式查询：直接使用 DeepSeek 流式输出
        
        Args:
            question: 用户问题
            
        Yields:
            dict: 流式响应字典
        """
        # Step 1: 查询处理（标准化流程：意图理解+改写）
        processed = self.query_processor.process(question)
        final_query = processed["final_query"]
        understanding = processed.get("understanding")
        
        logger.info(
            "流式查询处理完成（直接流式模式）",
            original_query=question[:50] if len(question) > 50 else question,
            processed_query=final_query[:50] if len(final_query) > 50 else final_query,
            processing_method=processed['processing_method']
        )
        
        # 执行流式查询
        async for result in execute_stream_query(
            self.llm,
            self.formatter,
            self.query_processor,
            self.retriever,
            self.postprocessors,
            self.query_router,
            self.enable_auto_routing,
            self.retrieval_strategy,
            self.similarity_top_k,
            final_query,
            understanding
        ):
            yield result


