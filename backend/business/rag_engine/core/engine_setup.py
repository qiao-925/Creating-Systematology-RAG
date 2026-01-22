"""
RAG引擎初始化模块：负责引擎组件的设置和配置

主要功能：
- 配置加载和验证
- 组件初始化（观察器、LLM、路由、检索）
"""

from typing import Optional, Tuple, Any

from llama_index.core import Settings
from llama_index.core.query_engine import RetrieverQueryEngine

from backend.infrastructure.config import config
from backend.infrastructure.indexer import IndexManager
from backend.infrastructure.logger import get_logger
from backend.infrastructure.observers.manager import ObserverManager
from backend.infrastructure.observers.factory import create_observer_from_config
from backend.business.rag_engine.retrieval.factory import create_retriever
from backend.business.rag_engine.processing.execution import create_postprocessors
from backend.infrastructure.llms import create_deepseek_llm_for_query

logger = get_logger('rag_engine')


def load_engine_config(
    retrieval_strategy: Optional[str],
    similarity_top_k: Optional[int],
    enable_rerank: Optional[bool],
    rerank_top_n: Optional[int],
    reranker_type: Optional[str],
    similarity_cutoff: Optional[float],
    enable_auto_routing: Optional[bool],
    supported_strategies: list
) -> dict:
    """加载并验证配置参数
    
    Returns:
        配置字典
    """
    config_dict = {
        'retrieval_strategy': retrieval_strategy or config.RETRIEVAL_STRATEGY,
        'similarity_top_k': similarity_top_k or config.SIMILARITY_TOP_K,
        'enable_rerank': enable_rerank if enable_rerank is not None else config.ENABLE_RERANK,
        'rerank_top_n': rerank_top_n or config.RERANK_TOP_N,
        'reranker_type': reranker_type or config.RERANKER_TYPE,
        'similarity_cutoff': similarity_cutoff or config.SIMILARITY_CUTOFF,
        'enable_auto_routing': enable_auto_routing if enable_auto_routing is not None else config.ENABLE_AUTO_ROUTING,
    }
    
    if config_dict['retrieval_strategy'] not in supported_strategies:
        raise ValueError(
            f"不支持的检索策略: {config_dict['retrieval_strategy']}. "
            f"支持的策略: {supported_strategies}"
        )
    
    return config_dict


def setup_observer_manager(observer_manager: Optional[ObserverManager]) -> ObserverManager:
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


def setup_llm(api_key: Optional[str], model: Optional[str]):
    """设置LLM"""
    api_key = api_key or config.DEEPSEEK_API_KEY
    model = model or config.LLM_MODEL
    if not api_key:
        raise ValueError("未设置DEEPSEEK_API_KEY")
    
    logger.info(f"初始化DeepSeek LLM: {model}")
    return create_deepseek_llm_for_query(api_key=api_key, model=model, max_tokens=4096)


def setup_query_router(index_manager: IndexManager, llm):
    """设置查询路由器"""
    from backend.business.rag_engine.routing.query_router import QueryRouter
    router = QueryRouter(
        index_manager=index_manager,
        llm=llm,
        enable_auto_routing=True,
    )
    logger.info("查询路由器已启用", mode="自动路由模式")
    return router


def setup_retrieval_components(
    index,
    retrieval_strategy: str,
    similarity_top_k: int,
    enable_auto_routing: bool,
    create_query_engine_func
) -> Tuple[Optional[Any], Optional[RetrieverQueryEngine]]:
    """设置检索组件"""
    if not enable_auto_routing:
        retriever = create_retriever(
            index,
            retrieval_strategy,
            similarity_top_k
        )
        query_engine = create_query_engine_func(retriever)
        return retriever, query_engine
    else:
        return None, None


def log_initialization_summary(
    retrieval_strategy: str,
    similarity_top_k: int,
    enable_rerank: bool,
    similarity_cutoff: float,
    enable_auto_routing: bool
) -> None:
    """记录初始化摘要"""
    logger.info(
        "模块化查询引擎初始化完成",
        strategy=retrieval_strategy,
        top_k=similarity_top_k,
        rerank_enabled=enable_rerank,
        similarity_cutoff=similarity_cutoff,
        auto_routing=enable_auto_routing
    )
