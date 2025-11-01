"""
RAG统一服务接口

提供查询、索引构建、对话等核心功能的统一入口
解耦前端层与业务逻辑，简化调用方式
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from src.indexer import IndexManager
from src.query_engine import QueryEngine
from src.chat_manager import ChatManager, ChatSession
from src.logger import setup_logger
from src.config import config

logger = setup_logger('rag_service')


@dataclass
class RAGResponse:
    """RAG查询响应"""
    answer: str
    sources: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def has_sources(self) -> bool:
        """是否有引用来源"""
        return bool(self.sources)


@dataclass
class IndexResult:
    """索引构建结果"""
    success: bool
    collection_name: str
    doc_count: int
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatResponse:
    """对话响应"""
    answer: str
    sources: List[Dict[str, Any]]
    session_id: str
    turn_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class RAGService:
    """RAG统一服务
    
    提供查询、索引构建、对话等核心功能的统一入口
    封装QueryEngine、IndexManager、ChatManager，简化前端调用
    
    Examples:
        >>> service = RAGService()
        >>> response = service.query("什么是系统思维？", user_id="user1")
        >>> print(response.answer)
        >>> 
        >>> # 对话模式
        >>> chat_response = service.chat("你好", session_id="session1")
        >>> print(chat_response.answer)
    """
    
    def __init__(
        self,
        collection_name: Optional[str] = None,
        similarity_top_k: Optional[int] = None,
        enable_debug: bool = False,
        enable_markdown_formatting: bool = True,
    ):
        """初始化RAG服务
        
        Args:
            collection_name: 向量集合名称
            similarity_top_k: 检索相似文档数量
            enable_debug: 是否启用调试模式
            enable_markdown_formatting: 是否启用Markdown格式化
        """
        self.collection_name = collection_name or config.COLLECTION_NAME
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        self.enable_debug = enable_debug
        self.enable_markdown_formatting = enable_markdown_formatting
        
        # 延迟初始化（按需加载）
        self._index_manager: Optional[IndexManager] = None
        self._query_engine: Optional[QueryEngine] = None
        self._chat_manager: Optional[ChatManager] = None
        
        logger.info(f"RAGService初始化: collection={self.collection_name}, top_k={self.similarity_top_k}")
    
    @property
    def index_manager(self) -> IndexManager:
        """获取索引管理器（延迟加载）"""
        if self._index_manager is None:
            logger.info("初始化IndexManager...")
            self._index_manager = IndexManager(collection_name=self.collection_name)
        return self._index_manager
    
    @property
    def query_engine(self) -> QueryEngine:
        """获取查询引擎（延迟加载）"""
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
        """查询接口
        
        Args:
            question: 用户问题
            user_id: 用户ID（可选，用于日志追踪）
            session_id: 会话ID（可选，用于日志追踪）
            **kwargs: 其他参数传递给QueryEngine
            
        Returns:
            RAGResponse: 查询响应
            
        Examples:
            >>> response = service.query("什么是系统思维？", user_id="user1")
            >>> print(response.answer)
            >>> for source in response.sources:
            ...     print(source['file_name'])
        """
        logger.info(f"收到查询请求: user={user_id}, session={session_id}, question={question[:50]}...")
        
        try:
            # 调用QueryEngine
            answer, sources = self.query_engine.query(question, **kwargs)
            
            # 构造响应
            response = RAGResponse(
                answer=answer,
                sources=sources,
                metadata={
                    'user_id': user_id,
                    'session_id': session_id,
                    'question': question,
                }
            )
            
            logger.info(f"查询成功: sources={len(sources)}, answer_len={len(answer)}")
            return response
            
        except Exception as e:
            logger.error(f"查询失败: {e}", exc_info=True)
            raise
    
    def build_index(
        self,
        source_path: str,
        collection_name: Optional[str] = None,
        **kwargs
    ) -> IndexResult:
        """构建索引接口
        
        Args:
            source_path: 数据源路径（本地路径、GitHub仓库等）
            collection_name: 集合名称（可选，覆盖默认值）
            **kwargs: 其他参数传递给IndexManager
            
        Returns:
            IndexResult: 索引构建结果
            
        Examples:
            >>> result = service.build_index("./data/documents")
            >>> if result.success:
            ...     print(f"成功索引 {result.doc_count} 个文档")
        """
        target_collection = collection_name or self.collection_name
        logger.info(f"开始构建索引: source={source_path}, collection={target_collection}")
        
        try:
            # 检测数据源类型
            if source_path.startswith(('http://', 'https://', 'git@')):
                # GitHub仓库或Web源
                from src.data_source import GitHubDataSource, WebDataSource
                if 'github.com' in source_path:
                    data_source = GitHubDataSource(url=source_path)
                else:
                    data_source = WebDataSource(url=source_path)
            else:
                # 本地文件系统
                from src.data_source import LocalDataSource
                data_source = LocalDataSource(path=source_path)
            
            # 加载文档
            documents = data_source.load_documents()
            
            if not documents:
                return IndexResult(
                    success=False,
                    collection_name=target_collection,
                    doc_count=0,
                    message="未找到文档"
                )
            
            # 构建索引
            self.index_manager.build_index(
                documents=documents,
                collection_name=target_collection,
                **kwargs
            )
            
            result = IndexResult(
                success=True,
                collection_name=target_collection,
                doc_count=len(documents),
                message=f"成功索引 {len(documents)} 个文档"
            )
            
            logger.info(f"索引构建成功: {result.message}")
            return result
            
        except Exception as e:
            logger.error(f"索引构建失败: {e}", exc_info=True)
            return IndexResult(
                success=False,
                collection_name=target_collection,
                doc_count=0,
                message=f"索引构建失败: {str(e)}"
            )
    
    def chat(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> ChatResponse:
        """对话接口
        
        Args:
            message: 用户消息
            session_id: 会话ID（可选，不提供则创建新会话）
            user_id: 用户ID（可选，用于日志追踪）
            **kwargs: 其他参数传递给ChatManager
            
        Returns:
            ChatResponse: 对话响应
            
        Examples:
            >>> # 开始新对话
            >>> response1 = service.chat("你好", session_id="s1")
            >>> print(response1.answer)
            >>> 
            >>> # 继续对话
            >>> response2 = service.chat("请详细解释一下", session_id="s1")
            >>> print(response2.turn_count)  # 2
        """
        logger.info(f"收到对话请求: user={user_id}, session={session_id}, message={message[:50]}...")
        
        try:
            # 获取或创建会话
            if session_id:
                session = self.chat_manager.get_session(session_id)
                if not session:
                    session = self.chat_manager.create_session(session_id=session_id)
            else:
                session = self.chat_manager.create_session()
            
            # 发送消息
            answer, sources = self.chat_manager.chat(
                message=message,
                session_id=session.session_id,
                **kwargs
            )
            
            # 构造响应
            response = ChatResponse(
                answer=answer,
                sources=sources,
                session_id=session.session_id,
                turn_count=len(session.history),
                metadata={
                    'user_id': user_id,
                    'message': message,
                }
            )
            
            logger.info(f"对话成功: session={session.session_id}, turn={response.turn_count}")
            return response
            
        except Exception as e:
            logger.error(f"对话失败: {e}", exc_info=True)
            raise
    
    def get_chat_history(self, session_id: str) -> Optional[ChatSession]:
        """获取对话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            ChatSession: 对话会话对象，如果不存在则返回None
        """
        return self.chat_manager.get_session(session_id)
    
    def clear_chat_history(self, session_id: str) -> bool:
        """清空对话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功清空
        """
        try:
            self.chat_manager.reset_session(session_id)
            logger.info(f"清空对话历史: session={session_id}")
            return True
        except Exception as e:
            logger.error(f"清空对话历史失败: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """列出所有向量集合
        
        Returns:
            List[str]: 集合名称列表
        """
        try:
            collections = self.index_manager.list_collections()
            logger.info(f"列出集合: {len(collections)}个")
            return collections
        except Exception as e:
            logger.error(f"列出集合失败: {e}")
            return []
    
    def delete_collection(self, collection_name: str) -> bool:
        """删除向量集合
        
        Args:
            collection_name: 集合名称
            
        Returns:
            bool: 是否成功删除
        """
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


# 向后兼容：提供便捷函数
def create_rag_service(
    collection_name: Optional[str] = None,
    **kwargs
) -> RAGService:
    """创建RAG服务实例
    
    便捷函数，用于快速创建服务实例
    
    Args:
        collection_name: 集合名称
        **kwargs: 其他参数传递给RAGService
        
    Returns:
        RAGService: 服务实例
    """
    return RAGService(collection_name=collection_name, **kwargs)
