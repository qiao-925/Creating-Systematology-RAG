"""
索引管理器主类 - 方法转发模块
IndexManager方法转发到模块函数
"""

from typing import List, Optional, Tuple, Dict

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import Document as LlamaDocument

from src.indexer.index_batch import (
    group_documents_by_directory,
    load_batch_ckpt,
    save_batch_ckpt,
    compute_batch_id
)
from src.indexer.index_vector_ids import (
    get_vector_ids_by_metadata,
    get_vector_ids_batch,
    delete_vectors_by_ids
)
from src.indexer.index_utils import (
    add_documents as _add_documents,
    compute_documents_hash,
    check_vectors_exist,
    filter_vectorized_documents
)


def get_manager_methods():
    """返回IndexManager需要转发的方法实现"""
    
    def _group_documents_by_directory(self, documents, depth, docs_per_batch):
        """按目录分组文档"""
        return group_documents_by_directory(documents, depth, docs_per_batch, self.persist_dir)
    
    def _load_batch_ckpt(self):
        """加载批级checkpoint"""
        return load_batch_ckpt(self.persist_dir, self.collection_name)
    
    def _save_batch_ckpt(self, data):
        """保存批级checkpoint"""
        return save_batch_ckpt(data, self.persist_dir, self.collection_name)
    
    def _compute_batch_id(self, group_key, file_paths):
        """计算批次ID"""
        return compute_batch_id(group_key, file_paths)
    
    def _add_documents(self, documents):
        """添加文档"""
        return _add_documents(self, documents)
    
    def _get_vector_ids_by_metadata(self, file_path):
        """获取向量ID"""
        return get_vector_ids_by_metadata(self, file_path)
    
    def _get_vector_ids_batch(self, file_paths):
        """批量获取向量ID"""
        return get_vector_ids_batch(self, file_paths)
    
    def _delete_vectors_by_ids(self, vector_ids):
        """删除向量"""
        return delete_vectors_by_ids(self, vector_ids)
    
    def _compute_documents_hash(self, documents):
        """计算文档哈希"""
        return compute_documents_hash(documents)
    
    def _check_vectors_exist(self, documents):
        """检查向量是否存在"""
        return check_vectors_exist(self, documents)
    
    def _filter_vectorized_documents(self, documents):
        """过滤已向量化文档"""
        return filter_vectorized_documents(self, documents)
    
    return {
        '_group_documents_by_directory': _group_documents_by_directory,
        '_load_batch_ckpt': _load_batch_ckpt,
        '_save_batch_ckpt': _save_batch_ckpt,
        '_compute_batch_id': _compute_batch_id,
        '_add_documents': _add_documents,
        '_get_vector_ids_by_metadata': _get_vector_ids_by_metadata,
        '_get_vector_ids_batch': _get_vector_ids_batch,
        '_delete_vectors_by_ids': _delete_vectors_by_ids,
        '_compute_documents_hash': _compute_documents_hash,
        '_check_vectors_exist': _check_vectors_exist,
        '_filter_vectorized_documents': _filter_vectorized_documents,
    }

