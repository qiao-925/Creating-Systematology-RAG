"""
工具层：通用工具函数和辅助功能
"""

# 工具函数
from src.infrastructure.indexer.utils.hash import compute_documents_hash
from src.infrastructure.indexer.utils.dimension import ensure_collection_dimension_match
from src.infrastructure.indexer.utils.lifecycle import close
from src.infrastructure.indexer.utils.info import print_database_info
from src.infrastructure.indexer.utils.convenience import create_index_from_directory

# 操作功能
from src.infrastructure.indexer.utils.stats import get_stats
from src.infrastructure.indexer.utils.cleanup import clear_index, clear_collection_cache
from src.infrastructure.indexer.utils.incremental import incremental_update
from src.infrastructure.indexer.utils.ids import (
    get_vector_ids_by_metadata,
    get_vector_ids_batch,
    delete_vectors_by_ids
)
from src.infrastructure.indexer.utils.documents import add_documents

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
