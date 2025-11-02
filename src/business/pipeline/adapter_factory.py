"""
Pipeline模块适配器工厂

创建PipelineModule适配器
"""

from typing import Optional

from src.business.pipeline.adapters import (
    ModularQueryEngineRetrievalModule,
    ModularRerankingModule,
    ModularGenerationModule,
    ModularFormattingModule,
)
from src.query.modular.engine import ModularQueryEngine
from src.indexer import IndexManager
from src.logger import setup_logger

logger = setup_logger('pipeline_adapter_factory')


def create_retrieval_module(
    index_manager: IndexManager,
    modular_query_engine: Optional[ModularQueryEngine] = None,
    config: Optional[dict] = None,
) -> ModularQueryEngineRetrievalModule:
    """创建检索模块适配器"""
    return ModularQueryEngineRetrievalModule(
        index_manager=index_manager,
        modular_query_engine=modular_query_engine,
        config=config,
    )


def create_reranking_module(
    config: Optional[dict] = None,
) -> ModularRerankingModule:
    """创建重排序模块适配器"""
    return ModularRerankingModule(config=config)


def create_generation_module(
    modular_query_engine: ModularQueryEngine,
    config: Optional[dict] = None,
) -> ModularGenerationModule:
    """创建生成模块适配器"""
    return ModularGenerationModule(
        modular_query_engine=modular_query_engine,
        config=config,
    )


def create_formatting_module(
    modular_query_engine: ModularQueryEngine,
    config: Optional[dict] = None,
) -> ModularFormattingModule:
    """创建格式化模块适配器"""
    return ModularFormattingModule(
        modular_query_engine=modular_query_engine,
        config=config,
    )


def create_modular_rag_pipeline(
    index_manager: IndexManager,
    modular_query_engine: Optional[ModularQueryEngine] = None,
    enable_reranking: bool = True,
    enable_formatting: bool = True,
    config: Optional[dict] = None,
) -> 'Pipeline':
    """创建模块化RAG流水线
    
    Args:
        index_manager: 索引管理器
        modular_query_engine: ModularQueryEngine实例（可选）
        enable_reranking: 是否启用重排序
        enable_formatting: 是否启用格式化
        config: 配置字典
        
    Returns:
        Pipeline实例
    """
    from src.business.pipeline.executor import Pipeline
    from src.business.protocols import ModuleList
    
    # 创建ModularQueryEngine（如果未提供）
    if not modular_query_engine:
        engine_config = config or {}
        modular_query_engine = ModularQueryEngine(
            index_manager=index_manager,
            **engine_config
        )
    
    # 创建模块列表
    modules: ModuleList = []
    
    # 1. 检索模块
    retrieval_module = create_retrieval_module(
        index_manager=index_manager,
        modular_query_engine=modular_query_engine,
        config=config,
    )
    modules.append(retrieval_module)
    
    # 2. 重排序模块（可选）
    if enable_reranking:
        reranking_module = create_reranking_module(config=config)
        modules.append(reranking_module)
    
    # 3. 生成模块
    generation_module = create_generation_module(
        modular_query_engine=modular_query_engine,
        config=config,
    )
    modules.append(generation_module)
    
    # 4. 格式化模块（可选）
    if enable_formatting:
        formatting_module = create_formatting_module(
            modular_query_engine=modular_query_engine,
            config=config,
        )
        modules.append(formatting_module)
    
    # 创建流水线
    pipeline = Pipeline(
        name="modular_rag",
        modules=modules,
        description="模块化RAG流水线: 检索 → 重排序 → 生成 → 格式化",
    )
    
    logger.info(f"创建模块化RAG流水线: {len(modules)} 个模块")
    
    return pipeline

