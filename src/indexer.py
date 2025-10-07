"""
索引构建模块
负责构建和管理向量索引，集成Chroma向量数据库
"""

from pathlib import Path
from typing import List, Optional

import chromadb
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    Settings,
)
from llama_index.core.schema import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.config import config


class IndexManager:
    """索引管理器"""
    
    def __init__(
        self,
        collection_name: Optional[str] = None,
        persist_dir: Optional[Path] = None,
        embedding_model: Optional[str] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        """初始化索引管理器
        
        Args:
            collection_name: Chroma集合名称
            persist_dir: 向量存储持久化目录
            embedding_model: Embedding模型名称
            chunk_size: 文本分块大小
            chunk_overlap: 文本分块重叠大小
        """
        # 使用配置或默认值
        self.collection_name = collection_name or config.CHROMA_COLLECTION_NAME
        self.persist_dir = persist_dir or config.VECTOR_STORE_PATH
        self.embedding_model_name = embedding_model or config.EMBEDDING_MODEL
        self.chunk_size = chunk_size or config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP
        
        # 确保持久化目录存在
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化embedding模型
        print(f"📦 正在加载Embedding模型: {self.embedding_model_name}")
        self.embed_model = HuggingFaceEmbedding(
            model_name=self.embedding_model_name,
            trust_remote_code=True,
        )
        
        # 配置全局Settings
        Settings.embed_model = self.embed_model
        Settings.chunk_size = self.chunk_size
        Settings.chunk_overlap = self.chunk_overlap
        
        # 初始化Chroma客户端
        print(f"🗄️  初始化Chroma向量数据库: {self.persist_dir}")
        self.chroma_client = chromadb.PersistentClient(path=str(self.persist_dir))
        
        # 获取或创建集合
        self.chroma_collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name
        )
        
        # 创建向量存储
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        
        # 创建存储上下文
        self.storage_context = StorageContext.from_defaults(
            vector_store=self.vector_store
        )
        
        # 索引对象（延迟初始化）
        self._index: Optional[VectorStoreIndex] = None
        
        print("✅ 索引管理器初始化完成")
    
    def build_index(
        self,
        documents: List[LlamaDocument],
        show_progress: bool = True
    ) -> VectorStoreIndex:
        """构建或更新索引
        
        Args:
            documents: 文档列表
            show_progress: 是否显示进度
            
        Returns:
            VectorStoreIndex对象
        """
        if not documents:
            print("⚠️  没有文档可索引")
            return self.get_index()
        
        print(f"\n🔨 开始构建索引，共 {len(documents)} 个文档")
        print(f"   分块参数: size={self.chunk_size}, overlap={self.chunk_overlap}")
        
        try:
            # 如果索引不存在，创建新索引
            if self._index is None:
                self._index = VectorStoreIndex.from_documents(
                    documents,
                    storage_context=self.storage_context,
                    show_progress=show_progress,
                )
                print("✅ 索引创建成功")
            else:
                # 如果索引已存在，增量添加文档
                for doc in documents:
                    self._index.insert(doc)
                print("✅ 文档已添加到现有索引")
            
            # 获取索引统计信息
            stats = self.get_stats()
            print(f"📊 索引统计: {stats}")
            
            return self._index
            
        except Exception as e:
            print(f"❌ 索引构建失败: {e}")
            raise
    
    def get_index(self) -> VectorStoreIndex:
        """获取现有索引
        
        Returns:
            VectorStoreIndex对象
        """
        if self._index is None:
            # 尝试从已有的向量存储加载
            try:
                self._index = VectorStoreIndex.from_vector_store(
                    vector_store=self.vector_store,
                    storage_context=self.storage_context,
                )
                print("✅ 从向量存储加载索引成功")
            except Exception as e:
                print(f"ℹ️  没有找到现有索引，将在添加文档后创建")
                # 创建一个空索引
                self._index = VectorStoreIndex.from_documents(
                    [],
                    storage_context=self.storage_context,
                )
        
        return self._index
    
    def clear_index(self):
        """清空索引"""
        try:
            # 删除集合
            self.chroma_client.delete_collection(name=self.collection_name)
            print(f"✅ 已删除集合: {self.collection_name}")
            
            # 重新创建集合
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name
            )
            self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
            self.storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )
            
            # 重置索引
            self._index = None
            print("✅ 索引已清空")
            
        except Exception as e:
            print(f"❌ 清空索引失败: {e}")
            raise
    
    def get_stats(self) -> dict:
        """获取索引统计信息
        
        Returns:
            包含统计信息的字典
        """
        try:
            count = self.chroma_collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "embedding_model": self.embedding_model_name,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
            }
        except Exception as e:
            print(f"❌ 获取统计信息失败: {e}")
            return {}
    
    def search(self, query: str, top_k: int = 5) -> List[dict]:
        """搜索相似文档（用于测试）
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            搜索结果列表
        """
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


def create_index_from_directory(
    directory_path: str | Path,
    collection_name: Optional[str] = None,
    recursive: bool = True
) -> IndexManager:
    """从目录创建索引（便捷函数）
    
    Args:
        directory_path: 文档目录路径
        collection_name: 集合名称
        recursive: 是否递归加载
        
    Returns:
        IndexManager对象
    """
    from src.data_loader import load_documents_from_directory
    
    # 加载文档
    print(f"📂 从目录加载文档: {directory_path}")
    documents = load_documents_from_directory(directory_path, recursive=recursive)
    
    if not documents:
        print("⚠️  未找到任何文档")
        return IndexManager(collection_name=collection_name)
    
    # 创建索引管理器
    index_manager = IndexManager(collection_name=collection_name)
    
    # 构建索引
    index_manager.build_index(documents)
    
    return index_manager


def create_index_from_urls(
    urls: List[str],
    collection_name: Optional[str] = None
) -> IndexManager:
    """从URL列表创建索引（便捷函数）
    
    Args:
        urls: URL列表
        collection_name: 集合名称
        
    Returns:
        IndexManager对象
    """
    from src.data_loader import load_documents_from_urls
    
    # 加载文档
    print(f"🌐 从 {len(urls)} 个URL加载文档")
    documents = load_documents_from_urls(urls)
    
    if not documents:
        print("⚠️  未成功加载任何网页")
        return IndexManager(collection_name=collection_name)
    
    # 创建索引管理器
    index_manager = IndexManager(collection_name=collection_name)
    
    # 构建索引
    index_manager.build_index(documents)
    
    return index_manager


if __name__ == "__main__":
    # 测试代码
    print("=== 测试索引构建 ===\n")
    
    # 创建测试文档
    test_docs = [
        LlamaDocument(
            text="系统科学是研究系统的一般规律和方法的科学。",
            metadata={"title": "系统科学简介", "source": "test"}
        ),
        LlamaDocument(
            text="钱学森是中国系统科学的创建者之一，他提出了系统工程的理论体系。",
            metadata={"title": "钱学森与系统科学", "source": "test"}
        ),
    ]
    
    # 创建索引
    index_manager = IndexManager(collection_name="test_collection")
    index_manager.build_index(test_docs)
    
    # 测试搜索
    print("\n=== 测试搜索 ===")
    results = index_manager.search("钱学森", top_k=2)
    for i, result in enumerate(results, 1):
        print(f"\n结果 {i}:")
        print(f"相似度: {result['score']:.4f}")
        print(f"内容: {result['text']}")
    
    # 清理测试数据
    index_manager.clear_index()
    print("\n✅ 测试完成")

