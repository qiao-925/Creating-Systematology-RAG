"""
模块化查询引擎 - 核心引擎模块
ModularQueryEngine类实现
"""

from typing import List, Optional, Tuple, Dict, Any
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.deepseek import DeepSeek

from src.config import config
from src.indexer import IndexManager
from src.logger import setup_logger
from src.response_formatter import ResponseFormatter
from src.observers.manager import ObserverManager
from src.observers.factory import create_observer_from_config
from src.query.modular.retriever_factory import create_retriever
from src.query.modular.postprocessor_factory import create_postprocessors
from src.query.modular.query_executor import execute_query

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
        
        # 配置 LLM
        self.api_key = api_key or config.DEEPSEEK_API_KEY
        self.model = model or config.LLM_MODEL
        if not self.api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY")
        
        self.llm = DeepSeek(
            api_key=self.api_key,
            model=self.model,
            temperature=0.5,
            max_tokens=4096,
        )
        
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
    ) -> Tuple[str, List[dict], Optional[Dict[str, Any]]]:
        """执行查询（兼容现有API）"""
        # 如果启用自动路由，动态创建query_engine
        if self.enable_auto_routing and self.query_router:
            retriever, routing_decision = self.query_router.route(question, top_k=self.similarity_top_k)
            
            # 动态创建query_engine
            query_engine = RetrieverQueryEngine.from_args(
                retriever=retriever,
                llm=self.llm,
                node_postprocessors=self.postprocessors,
            )
            
            logger.info(f"自动路由查询: decision={routing_decision}")
            return execute_query(
                query_engine,
                self.formatter,
                self.observer_manager,
                question,
                collect_trace
            )
        else:
            # 使用固定的query_engine
            return execute_query(
                self.query_engine,
                self.formatter,
                self.observer_manager,
                question,
                collect_trace
            )
    
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
