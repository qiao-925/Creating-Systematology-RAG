"""
索引管理器兼容性方法模块
包含向后兼容的内部方法
"""

from typing import List

from llama_index.core.schema import Document as LlamaDocument

from src.indexer.index_batch import (
    group_documents_by_directory,
    load_batch_ckpt,
    save_batch_ckpt,
    compute_batch_id
)
from src.indexer.index_utils import (
    add_documents,
    check_vectors_exist,
    filter_vectorized_documents,
    compute_documents_hash
)
from src.indexer.index_vector_ids import (
    get_vector_ids_by_metadata,
    get_vector_ids_batch,
    delete_vectors_by_ids
)
from src.indexer.index_core import print_database_info
from src.indexer.index_dimension import ensure_collection_dimension_match


def get_compatibility_methods(index_manager):
    """返回兼容性方法的字典（用于动态添加到IndexManager）"""
    return {
        '_group_documents_by_directory': lambda docs, depth, docs_per_batch: 
            group_documents_by_directory(docs, depth, docs_per_batch, index_manager.persist_dir),
        '_load_batch_ckpt': lambda: load_batch_ckpt(index_manager.persist_dir, index_manager.collection_name),
        '_save_batch_ckpt': lambda data: save_batch_ckpt(data, index_manager.persist_dir, index_manager.collection_name),
        '_compute_batch_id': compute_batch_id,
        '_add_documents': lambda docs: add_documents(index_manager, docs),
        '_get_vector_ids_by_metadata': lambda fp: get_vector_ids_by_metadata(index_manager, fp),
        '_get_vector_ids_batch': lambda fps: get_vector_ids_batch(index_manager, fps),
        '_delete_vectors_by_ids': lambda ids: delete_vectors_by_ids(index_manager, ids),
        '_compute_documents_hash': compute_documents_hash,
        '_check_vectors_exist': lambda docs: check_vectors_exist(index_manager, docs),
        '_filter_vectorized_documents': lambda docs: filter_vectorized_documents(index_manager, docs),
        '_print_database_info': lambda: print_database_info(index_manager),
        '_ensure_collection_dimension_match': lambda: ensure_collection_dimension_match(index_manager),
    }

