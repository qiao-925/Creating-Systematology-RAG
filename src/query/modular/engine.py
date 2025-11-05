"""
模块化查询引擎 - 核心引擎模块
ModularQueryEngine类实现
"""

from typing import List, Optional, Tuple, Dict, Any
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.query_engine import RetrieverQueryEngine
from src.config import config
from src.indexer import IndexManager
from src.logger import setup_logger
from src.response_formatter import ResponseFormatter
from src.observers.manager import ObserverManager
from src.observers.factory import create_observer_from_config
from src.query.modular.retriever_factory import create_retriever
from src.query.modular.postprocessor_factory import create_postprocessors
from src.query.modular.query_executor import execute_query
from src.query.modular.query_processor import QueryProcessor
from src.query.fallback import handle_fallback
from src.llms import create_deepseek_llm_for_query

logger = setup_logger('modular_query_engine')


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
        self.retrieval_strategy = retrieval_strategy or config.RETRIEVAL_STRATEGY
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        self.enable_rerank = enable_rerank if enable_rerank is not None else config.ENABLE_RERANK
        self.rerank_top_n = rerank_top_n or config.RERANK_TOP_N
        self.reranker_type = reranker_type or config.RERANKER_TYPE
        self.similarity_cutoff = similarity_cutoff or config.SIMILARITY_CUTOFF
        self.enable_auto_routing = enable_auto_routing if enable_auto_routing is not None else config.ENABLE_AUTO_ROUTING
        
        # 验证策略
        if self.retrieval_strategy not in self.SUPPORTED_STRATEGIES:
            raise ValueError(
                f"不支持的检索策略: {self.retrieval_strategy}. "
                f"支持的策略: {self.SUPPORTED_STRATEGIES}"
            )
        
        # 初始化响应格式化器
        self.formatter = ResponseFormatter(enable_formatting=enable_markdown_formatting)
        
        # 初始化观察器管理器
        if observer_manager is not None:
            self.observer_manager = observer_manager
            logger.info(f"✅ 使用提供的观察器管理器: {len(observer_manager.observers)} 个观察器")
        else:
            self.observer_manager = create_observer_from_config()
            logger.info(f"✅ 从配置创建观察器管理器: {len(self.observer_manager.observers)} 个观察器")
        
        # 获取所有回调处理器
        callback_handlers = self.observer_manager.get_callback_handlers()
        if callback_handlers:
            from llama_index.core.callbacks import CallbackManager
            Settings.callback_manager = CallbackManager(callback_handlers)
            logger.info(f"✅ 设置 {len(callback_handlers)} 个回调处理器到 LlamaIndex")
        
        # 配置 LLM（使用工厂函数，自然语言场景）
        self.api_key = api_key or config.DEEPSEEK_API_KEY
        self.model = model or config.LLM_MODEL
        if not self.api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY")
        
        self.llm = create_deepseek_llm_for_query(
            api_key=self.api_key,
            model=self.model,
            max_tokens=4096,
        )
        
        # 初始化查询处理器（标准化流程：意图理解+改写）
        self.query_processor = QueryProcessor(llm=self.llm)
        logger.info("✅ 查询处理器已初始化（标准化流程：意图理解+改写）")
        
        # 如果启用自动路由，创建QueryRouter
        if self.enable_auto_routing:
            from src.routers.query_router import QueryRouter
            self.query_router = QueryRouter(
                index_manager=index_manager,
                llm=self.llm,
                enable_auto_routing=True,
            )
            logger.info("✅ 查询路由器已启用（自动路由模式）")
        else:
            self.query_router = None
        
        # 创建检索器（如果启用自动路由，retriever会在query时动态创建）
        if not self.enable_auto_routing:
            self.retriever = create_retriever(
                self.index,
                self.retrieval_strategy,
                self.similarity_top_k
            )
        else:
            # 自动路由模式下，retriever在query时动态创建
            self.retriever = None
        
        # 创建后处理器
        self.postprocessors = create_postprocessors(
            self.index_manager,
            self.similarity_cutoff,
            self.enable_rerank,
            self.rerank_top_n,
            reranker_type=self.reranker_type,
        )
        
        # 创建查询引擎（如果启用自动路由，query_engine在query时动态创建）
        if not self.enable_auto_routing:
            self.query_engine = RetrieverQueryEngine.from_args(
                retriever=self.retriever,
                llm=self.llm,
                node_postprocessors=self.postprocessors,
            )
        else:
            # 自动路由模式下，query_engine在query时动态创建
            self.query_engine = None
        
        logger.info(f"✅ 模块化查询引擎初始化完成")
        logger.info(f"   检索策略: {self.retrieval_strategy}")
        logger.info(f"   Top-K: {self.similarity_top_k}")
        logger.info(f"   重排序: {'启用' if self.enable_rerank else '禁用'}")
        logger.info(f"   相似度阈值: {self.similarity_cutoff}")
    
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
            f"📝 查询处理完成: "
            f"原始='{question[:50]}...', "
            f"最终='{final_query[:50]}...', "
            f"处理方式={processed['processing_method']}"
        )
        
        # 如果启用自动路由，动态创建query_engine
        if self.enable_auto_routing and self.query_router:
            # 传递意图理解结果给路由器
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
            
            # 动态创建query_engine
            query_engine = RetrieverQueryEngine.from_args(
                retriever=retriever,
                llm=self.llm,
                node_postprocessors=self.postprocessors,
            )
            
            logger.info(
                f"🔍 使用检索策略: "
                f"策略={routing_decision}, "
                f"原因=自动路由模式，根据查询意图动态选择"
            )
            answer, sources, reasoning_content, trace_info = execute_query(
                query_engine,
                self.formatter,
                self.observer_manager,
                final_query,  # 使用改写后的查询
                collect_trace
            )
        else:
            # 使用固定的query_engine
            logger.info(
                f"🔍 使用检索策略: "
                f"策略={self.retrieval_strategy}, "
                f"原因=固定检索模式（初始化时配置）"
            )
            answer, sources, reasoning_content, trace_info = execute_query(
                self.query_engine,
                self.formatter,
                self.observer_manager,
                final_query,  # 使用改写后的查询
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
    
    async def stream_query(self, question: str):
        """异步流式查询（用于Web应用）"""
        raise NotImplementedError("流式查询暂未实现")


def create_modular_query_engine(
    index_manager: IndexManager,
    strategy: Optional[str] = None,
    **kwargs
) -> ModularQueryEngine:
    """创建模块化查询引擎（便捷函数）"""
    return ModularQueryEngine(
        index_manager=index_manager,
        retrieval_strategy=strategy,
        **kwargs
    )
