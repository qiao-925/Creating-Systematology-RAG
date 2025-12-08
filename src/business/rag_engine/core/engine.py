"""
RAG引擎核心模块：ModularQueryEngine类实现

主要功能：
- ModularQueryEngine类：模块化查询引擎，支持vector、bm25、hybrid、grep、multi等策略
- query()：执行查询，返回格式化的回答和引用来源

执行流程：
1. 初始化查询引擎（创建检索器、后处理器等）
2. 执行查询
3. 处理检索结果
4. 应用后处理（重排序等）
5. 生成回答并格式化
6. 返回查询结果

特性：
- 模块化设计
- 支持多种检索策略
- 可插拔的后处理器
- 完整的错误处理和兜底机制
"""

from typing import List, Optional, Tuple, Dict, Any
from llama_index.core import Settings
from llama_index.core.query_engine import RetrieverQueryEngine
from src.infrastructure.config import config
from src.infrastructure.indexer import IndexManager
from src.infrastructure.logger import get_logger
from src.business.rag_engine.formatting import ResponseFormatter
from src.infrastructure.observers.manager import ObserverManager
from src.infrastructure.observers.factory import create_observer_from_config
from src.business.rag_engine.retrieval.factory import create_retriever
from src.business.rag_engine.processing.execution import create_postprocessors, execute_query
from src.business.rag_engine.processing.query_processor import QueryProcessor
from src.business.rag_engine.utils.utils import handle_fallback
from src.infrastructure.llms import create_deepseek_llm_for_query
from src.business.rag_engine.models import QueryContext, QueryResult, SourceModel

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
        self._load_config(
            retrieval_strategy, similarity_top_k, enable_rerank,
            rerank_top_n, reranker_type, similarity_cutoff, enable_auto_routing
        )
        
        # 初始化组件
        self.formatter = ResponseFormatter(enable_formatting=enable_markdown_formatting)
        self.observer_manager = self._setup_observer_manager(observer_manager)
        self.llm = self._setup_llm(api_key, model)
        self.query_processor = QueryProcessor(llm=self.llm)
        logger.info("查询处理器已初始化", note="标准化流程：意图理解+改写")
        
        # 初始化路由和检索组件
        self.query_router = self._setup_query_router(index_manager) if self.enable_auto_routing else None
        self.retriever, self.query_engine = self._setup_retrieval_components()
        self.postprocessors = create_postprocessors(
            self.index_manager,
            self.similarity_cutoff,
            self.enable_rerank,
            self.rerank_top_n,
            reranker_type=self.reranker_type,
        )
        
        self._log_initialization_summary()
    
    def _load_config(
        self,
        retrieval_strategy: Optional[str],
        similarity_top_k: Optional[int],
        enable_rerank: Optional[bool],
        rerank_top_n: Optional[int],
        reranker_type: Optional[str],
        similarity_cutoff: Optional[float],
        enable_auto_routing: Optional[bool]
    ) -> None:
        """加载并验证配置参数"""
        self.retrieval_strategy = retrieval_strategy or config.RETRIEVAL_STRATEGY
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        self.enable_rerank = enable_rerank if enable_rerank is not None else config.ENABLE_RERANK
        self.rerank_top_n = rerank_top_n or config.RERANK_TOP_N
        self.reranker_type = reranker_type or config.RERANKER_TYPE
        self.similarity_cutoff = similarity_cutoff or config.SIMILARITY_CUTOFF
        self.enable_auto_routing = enable_auto_routing if enable_auto_routing is not None else config.ENABLE_AUTO_ROUTING
        
        if self.retrieval_strategy not in self.SUPPORTED_STRATEGIES:
            raise ValueError(
                f"不支持的检索策略: {self.retrieval_strategy}. "
                f"支持的策略: {self.SUPPORTED_STRATEGIES}"
            )
    
    def _setup_observer_manager(self, observer_manager: Optional[ObserverManager]) -> ObserverManager:
        """设置观察器管理器"""
        if observer_manager is not None:
            manager = observer_manager
            logger.info("使用提供的观察器管理器", observer_count=len(manager.observers))
        else:
            manager = create_observer_from_config()
            logger.info("从配置创建观察器管理器", observer_count=len(manager.observers))
        
        callback_handlers = manager.get_callback_handlers()
        if callback_handlers:
            from llama_index.core.callbacks import CallbackManager
            Settings.callback_manager = CallbackManager(callback_handlers)
            logger.info("设置回调处理器到LlamaIndex", handler_count=len(callback_handlers))
        
        return manager
    
    def _setup_llm(self, api_key: Optional[str], model: Optional[str]):
        """设置LLM"""
        api_key = api_key or config.DEEPSEEK_API_KEY
        model = model or config.LLM_MODEL
        if not api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY")
        
        return create_deepseek_llm_for_query(
            api_key=api_key,
            model=model,
            max_tokens=4096,
        )
    
    def _setup_query_router(self, index_manager: IndexManager):
        """设置查询路由器"""
        from src.business.rag_engine.routing.query_router import QueryRouter
        router = QueryRouter(
            index_manager=index_manager,
            llm=self.llm,
            enable_auto_routing=True,
        )
        logger.info("查询路由器已启用", mode="自动路由模式")
        return router
    
    def _setup_retrieval_components(self) -> Tuple[Optional[Any], Optional[RetrieverQueryEngine]]:
        """设置检索组件"""
        if not self.enable_auto_routing:
            retriever = create_retriever(
                self.index,
                self.retrieval_strategy,
                self.similarity_top_k
            )
            query_engine = self._create_query_engine_from_retriever(retriever)
            return retriever, query_engine
        else:
            return None, None
    
    def _log_initialization_summary(self) -> None:
        """记录初始化摘要"""
        logger.info(
            "模块化查询引擎初始化完成",
            strategy=self.retrieval_strategy,
            top_k=self.similarity_top_k,
            rerank_enabled=self.enable_rerank,
            similarity_cutoff=self.similarity_cutoff,
            auto_routing=self.enable_auto_routing
        )
    
    def _create_query_engine_from_retriever(self, retriever) -> RetrieverQueryEngine:
        """从检索器创建查询引擎
        
        Args:
            retriever: 检索器实例
            
        Returns:
            RetrieverQueryEngine实例
        """
        return RetrieverQueryEngine.from_args(
            retriever=retriever,
            llm=self.llm,
            node_postprocessors=self.postprocessors,
        )
    
    def _get_or_create_query_engine(
        self,
        final_query: str,
        understanding: Optional[Dict[str, Any]] = None
    ) -> Tuple[RetrieverQueryEngine, str]:
        """获取或创建查询引擎（支持自动路由）
        
        Args:
            final_query: 处理后的查询
            understanding: 查询理解结果（可选）
            
        Returns:
            (查询引擎实例, 路由决策/策略名称)
        """
        if self.enable_auto_routing and self.query_router:
            # 自动路由模式：根据查询意图动态选择检索器
            if understanding:
                retriever, routing_decision = self.query_router.route_with_understanding(
                    final_query,
                    understanding=understanding,
                    top_k=self.similarity_top_k
                )
            else:
                retriever, routing_decision = self.query_router.route(
                    final_query,
                    top_k=self.similarity_top_k
                )
            
            query_engine = self._create_query_engine_from_retriever(retriever)
            strategy_info = f"策略={routing_decision}, 原因=自动路由模式，根据查询意图动态选择"
            return query_engine, strategy_info
        else:
            # 固定模式：使用初始化时创建的查询引擎
            strategy_info = f"策略={self.retrieval_strategy}, 原因=固定检索模式（初始化时配置）"
            return self.query_engine, strategy_info
    
    def _execute_with_query_engine(
        self,
        query_engine: RetrieverQueryEngine,
        final_query: str,
        collect_trace: bool
    ) -> Tuple[str, List[dict], Optional[str], Optional[Dict[str, Any]]]:
        """使用查询引擎执行查询
        
        Args:
            query_engine: 查询引擎实例
            final_query: 处理后的查询
            collect_trace: 是否收集追踪信息
            
        Returns:
            (答案, 引用来源, 推理链内容, 追踪信息)
        """
        return execute_query(
            query_engine,
            self.formatter,
            self.observer_manager,
            final_query,
            collect_trace
        )
    
    def query(
        self, 
        question: str, 
        collect_trace: bool = False
    ) -> Tuple[str, List[dict], Optional[str], Optional[Dict[str, Any]]]:
        """执行查询（兼容现有API）
        
        Returns:
            (答案, 引用来源, 推理链内容, 追踪信息)
        """
        
        # Step 1: 查询处理（标准化流程：意图理解+改写）
        processed = self.query_processor.process(question)
        final_query = processed["final_query"]
        understanding = processed.get("understanding")
        
        logger.info(
            "查询处理完成",
            original_query=question[:50] if len(question) > 50 else question,
            processed_query=final_query[:50] if len(final_query) > 50 else final_query,
            processing_method=processed['processing_method']
        )
        
        # Step 2: 获取或创建查询引擎（支持自动路由）
        query_engine, strategy_info = self._get_or_create_query_engine(
            final_query,
            understanding
        )
        
        logger.info("使用检索策略", strategy_info=strategy_info)
        
        # Step 3: 执行查询
        answer, sources, reasoning_content, trace_info = self._execute_with_query_engine(
            query_engine,
            final_query,
            collect_trace
        )
        
        # 记录追踪信息
        if collect_trace and trace_info:
            trace_info["original_query"] = question
            trace_info["processed_query"] = final_query
            trace_info["query_processing"] = processed
        
        # 处理兜底逻辑（无来源、低相似度或空答案时触发）
        # 注意：使用原始查询进行兜底处理，确保用户看到的是原始问题的答案
        answer, fallback_reason = handle_fallback(
            answer, sources, question, self.llm, self.similarity_cutoff
        )
        
        # 如果收集追踪信息，记录兜底状态
        if collect_trace and trace_info:
            trace_info['fallback_used'] = bool(fallback_reason)
            trace_info['fallback_reason'] = fallback_reason
        
        return answer, sources, reasoning_content, trace_info
    
    def query_with_context(
        self,
        context: QueryContext
    ) -> QueryResult:
        """执行查询（使用 QueryContext 和 QueryResult 模型）
        
        Args:
            context: 查询上下文模型
            
        Returns:
            QueryResult 模型
        """
        logger.info(
            "执行查询（使用上下文模型）",
            query=context.query[:50] if len(context.query) > 50 else context.query,
            user_id=context.user_id,
            session_id=context.session_id,
            strategy=context.strategy,
            top_k=context.top_k
        )
        
        # 使用处理后的查询或原始查询
        query_text = context.processed_query or context.query
        
        # 执行查询
        answer, sources, reasoning_content, trace_info = self.query(
            query_text,
            collect_trace=bool(context.metadata.get('collect_trace', False))
        )
        
        # 转换为 SourceModel 列表
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
        
        # 创建 QueryResult
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
        
        logger.info(
            "查询完成",
            user_id=context.user_id,
            sources_count=len(result.sources),
            answer_len=len(answer)
        )
        
        return result
    
    async def stream_query(self, question: str):
        """异步流式查询（用于Web应用）"""
        raise NotImplementedError("流式查询暂未实现")


