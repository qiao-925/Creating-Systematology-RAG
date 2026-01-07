"""
索引服务 - 统一入口：封装所有索引管理功能，提供统一的接口、错误处理和进度反馈

主要功能：
- IndexService类：索引服务，提供统一的索引管理接口
- 封装索引构建、查询、更新、统计等所有功能

执行流程：
1. 初始化索引管理器
2. 执行索引操作（构建、查询、更新等）
3. 返回操作结果和统计信息

特性：
- 统一的接口设计
- 完整的错误处理
- 进度反馈和日志记录
- 统计信息收集
"""

from typing import List, Optional, Tuple, Dict

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import Document as LlamaDocument

from backend.infrastructure.logger import get_logger
from backend.infrastructure.indexer.core.manager import IndexManager

logger = get_logger('indexer_service')


class IndexService:
    """索引服务 - 统一入口
    
    封装所有索引管理功能，提供统一的接口、错误处理和进度反馈。
    类似 DataImportService 的设计模式。
    """
    
    def __init__(
        self,
        collection_name: Optional[str] = None,
        show_progress: bool = True,
        embedding_model: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        """初始化索引服务
        
        Args:
            collection_name: 集合名称
            show_progress: 是否显示进度
            embedding_model: Embedding模型名称
            chunk_size: 文档分块大小
            chunk_overlap: 文档分块重叠大小
        """
        self.show_progress = show_progress
        self._manager: Optional[IndexManager] = None
        self._collection_name = collection_name
        self._embedding_model = embedding_model
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
    
    @property
    def manager(self) -> IndexManager:
        """获取索引管理器实例（延迟初始化）"""
        if self._manager is None:
            self._manager = IndexManager(
                collection_name=self._collection_name,
                embedding_model=self._embedding_model,
                chunk_size=self._chunk_size,
                chunk_overlap=self._chunk_overlap,
            )
        return self._manager
    
    def build_index(
        self,
        documents: List[LlamaDocument],
        show_progress: Optional[bool] = None
    ) -> Tuple[VectorStoreIndex, Dict[str, List[str]]]:
        """构建或更新索引
        
        Args:
            documents: 文档列表
            show_progress: 是否显示进度（默认使用初始化时的设置）
            
        Returns:
            (索引实例, 向量ID映射)
        """
        show_progress = show_progress if show_progress is not None else self.show_progress
        return self.manager.build_index(documents, show_progress)
    
    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """搜索相似文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
        return self.manager.search(query, top_k)
    
    def get_stats(self) -> dict:
        """获取索引统计信息
        
        Returns:
            包含统计信息的字典
        """
        return self.manager.get_stats()
    
    def clear_index(self):
        """清空索引"""
        self.manager.clear_index()
    
    def clear_collection_cache(self):
        """清除collection中的所有向量数据（保留collection结构）"""
        self.manager.clear_collection_cache()
    
    def incremental_update(
        self,
        added_docs: List[LlamaDocument],
        modified_docs: List[LlamaDocument],
        deleted_file_paths: List[str],
        github_sync_manager=None
    ) -> dict:
        """执行增量更新
        
        Args:
            added_docs: 新增的文档列表
            modified_docs: 修改的文档列表
            deleted_file_paths: 删除的文件路径列表
            github_sync_manager: GitHub同步管理器实例
            
        Returns:
            更新统计信息
        """
        return self.manager.incremental_update(
            added_docs, modified_docs, deleted_file_paths, github_sync_manager
        )
    
    def close(self):
        """关闭索引服务，释放资源"""
        if self._manager is not None:
            self._manager.close()
            self._manager = None
