"""
核心功能层：IndexManager主类、初始化、Chroma客户端管理
"""

from backend.infrastructure.indexer.core.manager import IndexManager
from backend.infrastructure.indexer.core.init import init_index_manager
from backend.infrastructure.indexer.core.chroma_client import (
    ChromaClientManager,
    get_chroma_client,
    get_chroma_collection,
)

__all__ = [
    'IndexManager',
    'init_index_manager',
    'ChromaClientManager',
    'get_chroma_client',
    'get_chroma_collection',
]
