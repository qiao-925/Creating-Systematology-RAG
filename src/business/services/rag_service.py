"""
RAG服务 - 核心服务模块
RAGService类实现
"""

from typing import Optional

from src.indexer import IndexManager
from src.query_engine import QueryEngine
from src.query.modular.engine import ModularQueryEngine
from src.chat_manager import ChatManager
from src.logger import setup_logger
from src.config import config
from src.business.services.modules.models import RAGResponse, IndexResult, ChatResponse

logger = setup_logger('rag_service')


class RAGService:
    """RAG统一服务
    
    提供查询、索引构建、对话等核心功能的统一入口
    支持模块化查询引擎（ModularQueryEngine）
    """
    
    def __init__(
        self,
        collection_name: Optional[str] = None,
        similarity_top_k: Optional[int] = None,
        enable_debug: bool = False,
        enable_markdown_formatting: bool = True,
        use_modular_engine: bool = True,
        **kwargs
    ):
        """初始化RAG服务
        
        Args:
            collection_name: 向量集合名称
            similarity_top_k: 检索相似文档数量
            enable_debug: 是否启用调试模式
            enable_markdown_formatting: 是否启用Markdown格式化
            use_modular_engine: 是否使用模块化查询引擎（推荐）
            **kwargs: 传递给ModularQueryEngine的其他参数
        """
        self.collection_name = collection_name or config.CHROMA_COLLECTION_NAME
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        self.enable_debug = enable_debug
        self.enable_markdown_formatting = enable_markdown_formatting
        self.use_modular_engine = use_modular_engine
        self.engine_kwargs = kwargs
        
        # 延迟初始化（按需加载）
        self._index_manager: Optional[IndexManager] = None
        self._query_engine: Optional[QueryEngine] = None
        self._modular_query_engine: Optional[ModularQueryEngine] = None
        self._chat_manager: Optional[ChatManager] = None
        
        logger.info(f"RAGService初始化: collection={self.collection_name}, top_k={self.similarity_top_k}, modular={use_modular_engine}")
    
    @property
    def index_manager(self) -> IndexManager:
        """获取索引管理器（延迟加载）"""
        if self._index_manager is None:
            logger.info("初始化IndexManager...")
            self._index_manager = IndexManager(collection_name=self.collection_name)
        return self._index_manager
    
    @property
    def query_engine(self) -> QueryEngine:
        """获取查询引擎（延迟加载，兼容旧接口）"""
        if self.use_modular_engine:
            # 使用模块化查询引擎，但返回兼容QueryEngine接口的包装
            return self.modular_query_engine
        
        if self._query_engine is None:
            logger.info("初始化QueryEngine...")
            self._query_engine = QueryEngine(
                index_manager=self.index_manager,
                similarity_top_k=self.similarity_top_k,
                enable_debug=self.enable_debug,
                enable_markdown_formatting=self.enable_markdown_formatting,
            )
        return self._query_engine
    
    @property
    def modular_query_engine(self) -> ModularQueryEngine:
        """获取模块化查询引擎（延迟加载）"""
        if self._modular_query_engine is None:
            logger.info("初始化ModularQueryEngine...")
            self._modular_query_engine = ModularQueryEngine(
                index_manager=self.index_manager,
                similarity_top_k=self.similarity_top_k,
                enable_markdown_formatting=self.enable_markdown_formatting,
                **self.engine_kwargs
            )
        return self._modular_query_engine
    
    @property
    def chat_manager(self) -> ChatManager:
        """获取对话管理器（延迟加载）"""
        if self._chat_manager is None:
            logger.info("初始化ChatManager...")
            self._chat_manager = ChatManager(
                index_manager=self.index_manager,
                similarity_top_k=self.similarity_top_k,
            )
        return self._chat_manager
    
    def query(
        self,
        question: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> RAGResponse:
        """查询接口"""
        from src.business.services.modules.query import handle_query
        return handle_query(self, question, user_id, session_id, **kwargs)
    
    def build_index(
        self,
        source_path: str,
        collection_name: Optional[str] = None,
        **kwargs
    ) -> IndexResult:
        """构建索引接口"""
        from src.business.services.modules.index import handle_build_index
        return handle_build_index(self, source_path, collection_name, **kwargs)
    
    def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """对话接口"""
        from src.business.services.modules.chat import handle_chat
        return handle_chat(self, message, session_id, user_id, **kwargs)
    
    def get_chat_history(self, session_id: str):
        """获取对话历史"""
        from src.chat_manager import ChatSession
        return self.chat_manager.get_current_session()
    
    def clear_chat_history(self, session_id: str) -> bool:
        """清空对话历史"""
        try:
            self.chat_manager.reset_session()
            logger.info(f"清空对话历史: session={session_id}")
            return True
        except Exception as e:
            logger.error(f"清空对话历史失败: {e}")
            return False
    
    def list_collections(self) -> list:
        """列出所有向量集合"""
        try:
            collections = self.index_manager.list_collections()
            logger.info(f"列出集合: {len(collections)}个")
            return collections
        except Exception as e:
            logger.error(f"列出集合失败: {e}")
            return []
    
    def delete_collection(self, collection_name: str) -> bool:
        """删除向量集合"""
        try:
            self.index_manager.delete_collection(collection_name)
            logger.info(f"删除集合: {collection_name}")
            return True
        except Exception as e:
            logger.error(f"删除集合失败: {e}")
            return False
    
    def close(self):
        """关闭服务，释放资源"""
        logger.info("关闭RAGService...")
        
        if self._index_manager:
            try:
                self._index_manager.close()
            except Exception as e:
                logger.warning(f"关闭IndexManager失败: {e}")
        
        self._index_manager = None
        self._query_engine = None
        self._chat_manager = None
        
        logger.info("RAGService已关闭")
    
    def __enter__(self):
        """支持上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持上下文管理器"""
        self.close()
