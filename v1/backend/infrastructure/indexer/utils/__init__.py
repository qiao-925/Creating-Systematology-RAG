"""
工具层：通用工具函数和辅助功能
"""

# 工具函数
from backend.infrastructure.indexer.utils.hash import compute_documents_hash
from backend.infrastructure.indexer.utils.dimension import ensure_collection_dimension_match
from backend.infrastructure.indexer.utils.lifecycle import close
from backend.infrastructure.indexer.utils.info import print_database_info
from backend.infrastructure.indexer.utils.convenience import create_index_from_directory

# 操作功能
from backend.infrastructure.indexer.utils.stats import get_stats
from backend.infrastructure.indexer.utils.cleanup import clear_index, clear_collection_cache
from backend.infrastructure.indexer.utils.incremental import incremental_update
from backend.infrastructure.indexer.utils.ids import (
    get_vector_ids_by_metadata,
    get_vector_ids_batch,
    delete_vectors_by_ids
)
from backend.infrastructure.indexer.utils.documents import add_documents

__all__ = [
    # 工具函数
    'compute_documents_hash',
    'ensure_collection_dimension_match',
    'close',
    'print_database_info',
    'create_index_from_directory',
    # 操作功能
    'get_stats',
    'clear_index',
    'clear_collection_cache',
    'incremental_update',
    'get_vector_ids_by_metadata',
    'get_vector_ids_batch',
    'delete_vectors_by_ids',
    'add_documents',
]
