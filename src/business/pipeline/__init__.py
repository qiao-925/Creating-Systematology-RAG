"""
流水线编排模块

提供模块化的RAG流水线执行能力
"""

from .executor import PipelineExecutor, Pipeline, ExecutionResult, create_simple_rag_pipeline, create_advanced_rag_pipeline
from .adapters import (
    ModularQueryEngineRetrievalModule,
    ModularRerankingModule,
    ModularGenerationModule,
    ModularFormattingModule,
)
from .adapter_factory import (
    create_retrieval_module,
    create_reranking_module,
    create_generation_module,
    create_formatting_module,
    create_modular_rag_pipeline,
)

__all__ = [
    'PipelineExecutor',
    'Pipeline',
    'ExecutionResult',
    'create_simple_rag_pipeline',
    'create_advanced_rag_pipeline',
    'ModularQueryEngineRetrievalModule',
    'ModularRerankingModule',
    'ModularGenerationModule',
    'ModularFormattingModule',
    'create_retrieval_module',
    'create_reranking_module',
    'create_generation_module',
    'create_formatting_module',
    'create_modular_rag_pipeline',
]
