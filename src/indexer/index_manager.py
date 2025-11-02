"""
索引管理器主类
整合所有索引管理功能
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict

import chromadb
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Settings,
)
from llama_index.core.schema import Document as LlamaDocument
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.config import config, get_gpu_device, is_gpu_available
from src.logger import setup_logger
from src.embeddings.base import BaseEmbedding
from src.indexer.index_init import init_index_manager
from src.indexer.index_core import get_index, print_database_info
from src.indexer.index_dimension import ensure_collection_dimension_match
from src.indexer.index_operations import search, get_stats, clear_index
from src.indexer.index_incremental import incremental_update
from src.indexer.index_utils import (
    add_documents as _add_documents
)
from src.indexer.index_vector_ids import (
    get_vector_ids_by_metadata,
    delete_vectors_by_ids
)
from src.indexer.index_wikipedia import preload_wikipedia_concepts
from src.indexer.index_lifecycle import close
from src.indexer.index_manager_build import build_index_method

logger = setup_logger('indexer')


class IndexManager:
    """索引管理器"""
    
    def __init__(
        self,
        collection_name: Optional[str] = None,
        persist_dir: Optional[Path] = None,
        embedding_model: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        embed_model_instance: Optional[HuggingFaceEmbedding] = None,
        embedding_instance: Optional[BaseEmbedding] = None,
    ):
        """初始化索引管理器"""
        # 使用配置或默认值
        self.collection_name = collection_name or config.CHROMA_COLLECTION_NAME
        self.persist_dir = persist_dir or config.VECTOR_STORE_PATH
        self.embedding_model_name = embedding_model or config.EMBEDDING_MODEL
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP
        
        # 确保持久化目录存在
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存统一的Embedding实例
        self._embedding_instance = embedding_instance
        
        # 初始化核心组件
        self.embed_model, self.chroma_client, self.chroma_collection, _ = init_index_manager(
            collection_name=self.collection_name,
            persist_dir=self.persist_dir,
            embedding_model_name=self.embedding_model_name,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            embed_model_instance=embed_model_instance,
            embedding_instance=embedding_instance
        )
        
        # 打印数据库信息
        print_database_info(self)
        
        # 检测并修复embedding维度不匹配问题
        ensure_collection_dimension_match(self)
        
        # 创建向量存储
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        
        # 创建存储上下文
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        
        # 索引对象（延迟初始化）
        self._index: Optional[VectorStoreIndex] = None
        
        print("✅ 索引管理器初始化完成")
        
        # 绑定转发方法
        manager_methods = get_manager_methods()
        for method_name, method_func in manager_methods.items():
            setattr(self, method_name, method_func.__get__(self, type(self)))
    
    
    def build_index(
        self,
        documents: List[LlamaDocument],
        show_progress: bool = True,
        cache_manager=None,
        task_id: Optional[str] = None
    ) -> Tuple[VectorStoreIndex, Dict[str, List[str]]]:
        """构建或更新索引"""
        return build_index_method(self, documents, show_progress, cache_manager, task_id)
    
    def get_embedding_instance(self) -> Optional[BaseEmbedding]:
        """获取统一的Embedding实例"""
        return self._embedding_instance
    
    def get_index(self) -> VectorStoreIndex:
        """获取现有索引"""
        return get_index(self)
    
    def clear_index(self):
        """清空索引"""
        clear_index(self)
    
    def get_stats(self) -> dict:
        """获取索引统计信息"""
        return get_stats(self)
    
    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """搜索相似文档"""
        return search(self, query, top_k)
    
    def incremental_update(
        self,
        added_docs: List[LlamaDocument],
        modified_docs: List[LlamaDocument],
        deleted_file_paths: List[str],
        metadata_manager=None
    ) -> dict:
        """执行增量更新"""
        return incremental_update(self, added_docs, modified_docs, deleted_file_paths, metadata_manager)
    
    def preload_wikipedia_concepts(
        self,
        concept_keywords: List[str],
        lang: str = "zh",
        show_progress: bool = True
    ) -> int:
        """预加载核心概念的维基百科内容到索引"""
        return preload_wikipedia_concepts(self, concept_keywords, lang, show_progress)
    
    def close(self):
        """关闭索引管理器，释放资源"""
        close(self)
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        try:
            self.close()
        except Exception:
            pass

