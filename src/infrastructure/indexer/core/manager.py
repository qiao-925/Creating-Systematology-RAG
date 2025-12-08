"""
索引管理器主类：整合所有索引管理功能
"""

from pathlib import Path
from typing import List, Optional, Tuple, Dict

from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.schema import Document as LlamaDocument
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.infrastructure.config import config
from src.infrastructure.logger import get_logger
from src.infrastructure.embeddings.base import BaseEmbedding
from src.infrastructure.indexer.core.init import init_index_manager
from src.infrastructure.indexer.utils.info import print_database_info
from src.infrastructure.indexer.utils.dimension import ensure_collection_dimension_match
from src.infrastructure.indexer.utils.stats import get_stats
from src.infrastructure.indexer.utils.cleanup import clear_index, clear_collection_cache
from src.infrastructure.indexer.utils.incremental import incremental_update
from src.infrastructure.indexer.utils.lifecycle import close
from src.infrastructure.indexer.build.builder import build_index_method

logger = get_logger('indexer')


class IndexManager:
    """索引管理器"""
    
    def __init__(
        self,
        collection_name: Optional[str] = None,
        persist_dir: Optional[Path] = None,
        embedding_model: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        embed_model_instance: Optional[BaseEmbedding] = None,
        embedding_instance: Optional[BaseEmbedding] = None,
    ):
        """初始化索引管理器"""
        # 使用配置或默认值
        self.collection_name = collection_name or config.CHROMA_COLLECTION_NAME
        self.embedding_model_name = embedding_model or config.EMBEDDING_MODEL
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP
        
        # 注意：Chroma Cloud模式不需要本地目录，persist_dir参数保留用于向后兼容但不再使用
        self.persist_dir = persist_dir
        
        # 保存统一的Embedding实例
        self._embedding_instance = embedding_instance
        
        # 初始化核心组件
        self.embed_model, self.chroma_client, self.chroma_collection = init_index_manager(
            collection_name=self.collection_name,
            persist_dir=self.persist_dir,
            embedding_model_name=self.embedding_model_name,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            embed_model_instance=embed_model_instance,
            embedding_instance=embedding_instance
        )
        
        # 一次性获取必要信息（最多2次查询：count + peek）
        # 避免在 print_database_info() 和 ensure_collection_dimension_match() 中重复查询
        try:
            collection_count = self.chroma_collection.count()
            # 获取样本数据用于维度检测和基本信息展示
            # 如果collection为空，sample_data为None
            sample_data = self.chroma_collection.peek(limit=1) if collection_count > 0 else None
        except Exception as e:
            logger.warning(f"获取collection信息时出错: {e}，将使用默认值")
            collection_count = 0
            sample_data = None
        
        # 打印基本信息（使用已有数据，不额外查询）
        print_database_info(
            self,
            collection_count=collection_count,
            sample_data=sample_data,
            detailed=False
        )
        
        # 检测维度（使用已有数据，不额外查询）
        ensure_collection_dimension_match(
            self,
            collection_count=collection_count,
            sample_data=sample_data
        )
        
        # 创建向量存储
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        
        # 创建存储上下文
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        
        # 索引对象（延迟初始化）
        self._index: Optional[VectorStoreIndex] = None
        
        logger.info("✅ 索引管理器初始化完成")
    
    def build_index(
        self,
        documents: List[LlamaDocument],
        show_progress: bool = True
    ) -> Tuple[VectorStoreIndex, Dict[str, List[str]]]:
        """构建或更新索引"""
        return build_index_method(self, documents, show_progress)
    
    def get_embedding_instance(self) -> Optional[BaseEmbedding]:
        """获取统一的Embedding实例"""
        return self._embedding_instance
    
    def _get_llama_index_compatible_embedding(self):
        """获取LlamaIndex兼容的Embedding实例
        
        Returns:
            LlamaIndex兼容的Embedding实例
            
        Raises:
            ValueError: 如果无法获取LlamaIndex兼容的Embedding实例
        """
        # 延迟导入LlamaIndex BaseEmbedding，尝试多个路径
        # 优先直接导入 BaseEmbedding（而不是通过 HuggingFaceEmbedding 获取）
        LlamaBaseEmbedding = None
        try:
            from llama_index.core.embeddings.base import BaseEmbedding as LlamaBaseEmbedding
            logger.debug("✅ 成功导入 llama_index.core.embeddings.base.BaseEmbedding")
        except ImportError:
            try:
                from llama_index.embeddings.base import BaseEmbedding as LlamaBaseEmbedding
                logger.debug("✅ 成功导入 llama_index.embeddings.base.BaseEmbedding")
            except ImportError:
                # 如果直接导入失败，尝试通过 HuggingFaceEmbedding 的 MRO 找到 BaseEmbedding
                try:
                    from llama_index.embeddings.huggingface import HuggingFaceEmbedding
                    # 通过 MRO 找到 BaseEmbedding（而不是直接取 __bases__[0]，可能是 MultiModalEmbedding）
                    for base_class in HuggingFaceEmbedding.__mro__:
                        if base_class.__name__ == 'BaseEmbedding' and 'embeddings' in base_class.__module__:
                            LlamaBaseEmbedding = base_class
                            logger.debug(f"✅ 通过MRO找到BaseEmbedding: {base_class.__module__}.{base_class.__name__}")
                            break
                    
                    if LlamaBaseEmbedding is None:
                        logger.warning("⚠️  无法在 HuggingFaceEmbedding 的 MRO 中找到 BaseEmbedding，将跳过类型检查")
                        LlamaBaseEmbedding = None
                except (ImportError, IndexError, AttributeError):
                    logger.warning("⚠️  无法导入LlamaIndex BaseEmbedding，将跳过类型检查")
                    LlamaBaseEmbedding = None
        
        # 如果embed_model本身就是LlamaIndex兼容的，直接返回
        if LlamaBaseEmbedding and isinstance(self.embed_model, LlamaBaseEmbedding):
            logger.debug(f"✅ embed_model已经是LlamaIndex兼容类型: {type(self.embed_model)}")
            return self.embed_model
        
        # 如果embed_model有get_llama_index_embedding方法，使用它
        if hasattr(self.embed_model, 'get_llama_index_embedding'):
            try:
                llama_embed = self.embed_model.get_llama_index_embedding()
                logger.debug(f"✅ 通过get_llama_index_embedding()获取: {type(self.embed_model)} -> {type(llama_embed)}")
                
                # 验证返回的对象确实是LlamaIndex兼容的
                if LlamaBaseEmbedding:
                    if isinstance(llama_embed, LlamaBaseEmbedding):
                        return llama_embed
                    else:
                        error_msg = (
                            f"get_llama_index_embedding()返回的对象不是LlamaIndex BaseEmbedding实例。"
                            f"期望类型: {LlamaBaseEmbedding}, 实际类型: {type(llama_embed)}"
                        )
                        logger.error(error_msg)
                        raise ValueError(error_msg)
                else:
                    # 如果无法导入BaseEmbedding，直接返回（相信get_llama_index_embedding的实现）
                    logger.debug("⚠️  无法验证类型，但相信get_llama_index_embedding()返回的是兼容的")
                    return llama_embed
            except Exception as e:
                error_msg = f"调用get_llama_index_embedding()失败: {e}"
                logger.error(error_msg, exc_info=True)
                raise ValueError(error_msg) from e
        
        # 其他情况，抛出错误而不是返回不兼容的对象
        error_msg = (
            f"无法获取LlamaIndex兼容的Embedding实例。"
            f"embed_model类型: {type(self.embed_model)}, "
            f"是否有get_llama_index_embedding方法: {hasattr(self.embed_model, 'get_llama_index_embedding')}"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    def get_index(self) -> VectorStoreIndex:
        """获取现有索引，支持延迟初始化"""
        if self._index is None:
            try:
                # 尝试从向量存储加载索引
                llama_embed_model = self._get_llama_index_compatible_embedding()
                self._index = VectorStoreIndex.from_vector_store(
                    vector_store=self.vector_store,
                    storage_context=self.storage_context,
                    embed_model=llama_embed_model,
                )
                
                # 检查 collection 是否为空
                try:
                    if hasattr(self, 'chroma_collection') and self.chroma_collection:
                        count = self.chroma_collection.count()
                        if count > 0:
                            logger.info("✅ 从向量存储加载索引成功")
                        else:
                            logger.info("ℹ️  Collection为空，将在添加文档后创建索引")
                            self._collection_is_empty = True
                    else:
                        logger.info("✅ 从向量存储加载索引成功")
                except Exception:
                    logger.info("✅ 从向量存储加载索引成功（无法验证向量数量）")
                    
            except Exception:
                logger.info("ℹ️  没有找到现有索引，将在添加文档后创建")
                # 创建一个空索引对象（向后兼容），但标记需要创建
                llama_embed_model = self._get_llama_index_compatible_embedding()
                self._index = VectorStoreIndex.from_documents(
                    [],
                    storage_context=self.storage_context,
                    embed_model=llama_embed_model,
                )
                self._collection_is_empty = True
        
        return self._index
    
    def clear_index(self):
        """清空索引"""
        clear_index(self)
    
    def clear_collection_cache(self):
        """清除collection中的所有向量数据（保留collection结构）"""
        clear_collection_cache(self)
    
    def get_stats(self) -> dict:
        """获取索引统计信息"""
        return get_stats(self)
    
    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """搜索相似文档"""
        if self._index is None:
            self.get_index()
        
        retriever = self._index.as_retriever(similarity_top_k=top_k)
        nodes = retriever.retrieve(query)
        
        results = []
        for node in nodes:
            results.append({
                "text": node.node.text,
                "score": node.score,
                "metadata": node.node.metadata,
            })
        
        return results
    
    def incremental_update(
        self,
        added_docs: List[LlamaDocument],
        modified_docs: List[LlamaDocument],
        deleted_file_paths: List[str],
        metadata_manager=None
    ) -> dict:
        """执行增量更新"""
        return incremental_update(self, added_docs, modified_docs, deleted_file_paths, metadata_manager)
    
    def close(self):
        """关闭索引管理器，释放资源"""
        close(self)
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        try:
            self.close()
        except Exception:
            pass
