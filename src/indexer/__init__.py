"""
索引构建模块 - 模块化版本
保持向后兼容的接口导出
"""

from src.indexer.index_manager import IndexManager
from src.indexer.index_convenience import (
    create_index_from_directory,
    create_index_from_urls,
)
from src.indexer.embedding_utils import (
    get_embedding_model_status,
    get_global_embed_model,
    load_embedding_model,
    set_global_embed_model,
    clear_embedding_model_cache,
)

__all__ = [
    'IndexManager',
    'create_index_from_directory',
    'create_index_from_urls',
    'get_embedding_model_status',
    'get_global_embed_model',
    'load_embedding_model',
    'set_global_embed_model',
    'clear_embedding_model_cache',
]

