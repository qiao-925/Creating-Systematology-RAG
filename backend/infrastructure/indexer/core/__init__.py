"""
核心功能层：IndexManager主类、初始化
"""

from backend.infrastructure.indexer.core.manager import IndexManager
from backend.infrastructure.indexer.core.init import init_index_manager

__all__ = [
    'IndexManager',
    'init_index_manager',
]
