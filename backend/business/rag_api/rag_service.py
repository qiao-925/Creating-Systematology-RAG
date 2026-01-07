"""
RAG API - RAG服务核心模块

提供查询、索引构建、对话等核心功能的统一入口
"""

from typing import Optional, List, AsyncIterator, Dict, Any
from pathlib import Path

from backend.infrastructure.indexer import IndexManager
from backend.business.rag_engine.core.engine import ModularQueryEngine
from backend.business.chat import ChatManager
from backend.business.chat.session import ChatSession, ChatTurn
from backend.business.chat.utils import get_user_sessions_metadata, load_session_from_file
from backend.infrastructure.logger import get_logger
from backend.infrastructure.config import config
from backend.business.rag_api.models import (
    RAGResponse,
    IndexResult,
    ChatResponse,
    QueryRequest,
    ChatRequest,
    CreateSessionRequest,
    SessionInfo,
    ChatTurnResponse,
    SessionDetailResponse,
    SessionHistoryResponse,
    SessionListResponse,
)
from backend.business.rag_engine.models import QueryContext, QueryResult, SourceModel

logger = get_logger('rag_service')


class RAGService:
    """RAG统一服务
    
    提供查询、索引构建、对话等核心功能的统一入口
    使用模块化查询引擎（ModularQueryEngine）
    """
    
    def __init__(
        self,
        collection_name: Optional[str] = None,
        similarity_top_k: Optional[int] = None,
        enable_debug: bool = False,
        enable_markdown_formatting: bool = True,
        **kwargs
    ):
        """初始化RAG服务
        
        Args:
            collection_name: 向量集合名称
            similarity_top_k: 检索相似文档数量
            enable_debug: 是否启用调试模式
            enable_markdown_formatting: 是否启用Markdown格式化
            **kwargs: 传递给ModularQueryEngine的其他参数
        """
        self.collection_name = collection_name or config.CHROMA_COLLECTION_NAME
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        self.enable_debug = enable_debug
        self.enable_markdown_formatting = enable_markdown_formatting
        self.engine_kwargs = kwargs
        
        # 延迟初始化（按需加载）
        self._index_manager: Optional[IndexManager] = None
        self._modular_query_engine: Optional[ModularQueryEngine] = None
        self._chat_manager: Optional[ChatManager] = None
        
        logger.info(
            "RAGService初始化",
            collection=self.collection_name,
            top_k=self.similarity_top_k,
            enable_debug=self.enable_debug
        )
    
    @property
    def index_manager(self) -> IndexManager:
        """获取索引管理器（延迟加载）"""
        if self._index_manager is None:
            logger.info("初始化IndexManager", collection=self.collection_name)
            self._index_manager = IndexManager(collection_name=self.collection_name)
        return self._index_manager
    
    @property
    def modular_query_engine(self) -> ModularQueryEngine:
        """获取模块化查询引擎（延迟加载）"""
        if self._modular_query_engine is None:
            logger.info(
                "初始化ModularQueryEngine",
                top_k=self.similarity_top_k,
                markdown_formatting=self.enable_markdown_formatting
            )
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
            logger.info("初始化ChatManager", top_k=self.similarity_top_k)
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
        collect_trace: bool = False,
        **kwargs
    ) -> RAGResponse:
        """查询接口
        
        Args:
            question: 查询问题
            user_id: 用户ID（可选）
            session_id: 会话ID（可选）
            collect_trace: 是否收集追踪信息
            **kwargs: 其他参数
        """
        # 验证输入
        request = QueryRequest(question=question, session_id=session_id, **kwargs)
        return self._query_internal(request, user_id=user_id, collect_trace=collect_trace)
    
    def _query_internal(
        self,
        request: QueryRequest,
        user_id: Optional[str] = None,
        collect_trace: bool = False
    ) -> RAGResponse:
        """查询接口（使用 Pydantic 验证）"""
        logger.info(
            "收到查询请求",
            user_id=user_id,
            session_id=request.session_id,
            question=request.question[:50] if len(request.question) > 50 else request.question,
            top_k=request.top_k,
            strategy=request.strategy,
            collect_trace=collect_trace
        )
        try:
            # 执行查询
            answer, sources, reasoning_content, trace_info = self.modular_query_engine.query(
                request.question,
                collect_trace=collect_trace
            )
            
            # 转换为 SourceModel 列表
            source_models = []
            for source in sources:
                if isinstance(source, dict):
                    source_models.append(SourceModel(**source))
                else:
                    source_models.append(SourceModel(
                        text=source.get('text', ''),
                        score=source.get('score', 0.0),
                        metadata=source.get('metadata', {}),
                        file_name=source.get('file_name'),
                        page_number=source.get('page_number'),
                        node_id=source.get('node_id')
                    ))
            
            # 创建元数据
            metadata = {
                'user_id': user_id,
                'session_id': request.session_id,
                'question': request.question,
                'reasoning_content': reasoning_content,
            }
            
            # 如果收集了追踪信息，添加到元数据
            if collect_trace and trace_info:
                metadata['trace_info'] = trace_info
            
            # 创建 Pydantic 响应模型
            response = RAGResponse(
                answer=answer,
                sources=source_models,
                metadata=metadata
            )
            
            logger.info(
                "查询成功",
                user_id=user_id,
                sources_count=len(response.sources),
                answer_len=len(answer)
            )
            return response
        except Exception as e:
            logger.error("查询失败", user_id=user_id, error=str(e), exc_info=True)
            raise
    
    def _load_documents_from_source(self, source_path: str) -> tuple[list, Optional[str]]:
        """从数据源加载文档（私有方法）"""
        from backend.infrastructure.data_loader import DataImportService, parse_github_url
        data_service = DataImportService(show_progress=False)
        if source_path.startswith(('http://', 'https://', 'git@')):
            if 'github.com' in source_path:
                repo_info = parse_github_url(source_path)
                if not repo_info:
                    return [], "无法解析GitHub URL"
                result = data_service.import_from_github(
                    owner=repo_info['owner'],
                    repo=repo_info['repo'],
                    branch=repo_info.get('branch', 'main')
                )
                documents = result.documents if result.success else []
                return documents, None if result.success else "GitHub导入失败"
            return [], "不支持Web URL，仅支持GitHub和本地路径"
        result = data_service.import_from_directory(source_path)
        documents = result.documents if result.success else []
        return documents, None if result.success else "本地目录导入失败"
    
    def build_index(
        self,
        source_path: str,
        collection_name: Optional[str] = None,
        **kwargs
    ) -> IndexResult:
        """构建索引接口"""
        target_collection = collection_name or self.collection_name
        logger.info(
            "开始构建索引",
            source=source_path,
            collection=target_collection
        )
        try:
            documents, error_msg = self._load_documents_from_source(source_path)
            if error_msg:
                logger.warning("索引构建失败", collection=target_collection, error=error_msg)
                return IndexResult(
                    success=False,
                    collection_name=target_collection,
                    doc_count=0,
                    message=error_msg
                )
            if not documents:
                logger.warning("未找到文档", collection=target_collection)
                return IndexResult(
                    success=False,
                    collection_name=target_collection,
                    doc_count=0,
                    message="未找到文档"
                )
            
            self.index_manager.build_index(documents=documents, collection_name=target_collection, **kwargs)
            logger.info(
                "索引构建成功",
                collection=target_collection,
                doc_count=len(documents)
            )
            return IndexResult(
                success=True,
                collection_name=target_collection,
                doc_count=len(documents),
                message=f"成功索引 {len(documents)} 个文档"
            )
        except Exception as e:
            logger.error(
                "索引构建失败",
                collection=target_collection,
                error=str(e),
                exc_info=True
            )
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
        """对话接口"""
        request = ChatRequest(message=message, session_id=session_id)
        return self._chat_internal(request, user_id=user_id)
    
    def _chat_internal(
        self,
        request: ChatRequest,
        user_id: Optional[str] = None
    ) -> ChatResponse:
        """对话接口（使用 Pydantic 验证）"""
        logger.info(
            "收到对话请求",
            user_id=user_id,
            session_id=request.session_id,
            message=request.message[:50] if len(request.message) > 50 else request.message
        )
        try:
            if request.session_id:
                session = self.chat_manager.get_current_session()
                if not session or session.session_id != request.session_id:
                    session = self.chat_manager.start_session(session_id=request.session_id)
            else:
                session = self.chat_manager.start_session()
            
            answer, sources, reasoning_content = self.chat_manager.chat(message=request.message)
            
            # 转换为 SourceModel 列表
            source_models = []
            for source in sources:
                if isinstance(source, dict):
                    source_models.append(SourceModel(**source))
                else:
                    source_models.append(SourceModel(
                        text=source.get('text', ''),
                        score=source.get('score', 0.0),
                        metadata=source.get('metadata', {}),
                        file_name=source.get('file_name'),
                        page_number=source.get('page_number'),
                        node_id=source.get('node_id')
                    ))
            
            # 创建 Pydantic 响应模型
            response = ChatResponse(
                answer=answer,
                sources=source_models,
                session_id=session.session_id,
                turn_count=len(session.history),
                metadata={
                    'user_id': user_id,
                    'message': request.message,
                    'reasoning_content': reasoning_content
                }
            )
            
            logger.info(
                "对话成功",
                user_id=user_id,
                session_id=session.session_id,
                turn_count=response.turn_count
            )
            return response
        except Exception as e:
            logger.error(
                "对话失败",
                user_id=user_id,
                session_id=request.session_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    def get_chat_history(self, session_id: Optional[str] = None):
        """获取对话历史"""
        if session_id:
            current_session = self.chat_manager.get_current_session()
            if not current_session or current_session.session_id != session_id:
                self.chat_manager.start_session(session_id=session_id)
        return self.chat_manager.get_current_session()
    
    def clear_chat_history(self, session_id: str) -> bool:
        """清空对话历史"""
        try:
            self.chat_manager.reset_session()
            logger.info("清空对话历史", session_id=session_id)
            return True
        except Exception as e:
            logger.error("清空对话历史失败", session_id=session_id, error=str(e))
            return False
    
    def start_new_session(self, request: CreateSessionRequest) -> Dict[str, Any]:
        """创建新会话
        
        Args:
            request: 创建会话请求
            
        Returns:
            会话信息字典
        """
        logger.info("创建新会话", session_id=request.session_id, has_message=request.message is not None)
        
        # 创建新会话
        session = self.chat_manager.start_session(session_id=request.session_id)
        
        # 如果提供了消息，发送第一条消息
        if request.message:
            answer, sources, reasoning_content = self.chat_manager.chat(request.message)
            logger.info("新会话创建并发送第一条消息", session_id=session.session_id)
        
        return {
            'session_id': session.session_id,
            'title': session.title,
            'created_at': session.created_at,
            'updated_at': session.updated_at,
            'turn_count': len(session.history),
        }
    
    def get_current_session_detail(self) -> SessionDetailResponse:
        """获取当前会话详情（包含完整历史）
        
        Returns:
            会话详情响应
        """
        session = self.chat_manager.get_current_session()
        if session is None:
            raise ValueError("当前没有活跃会话")
        
        # 转换历史记录
        history = []
        for turn in session.history:
            # 转换 sources 为 SourceModel
            source_models = []
            for source in turn.sources:
                if isinstance(source, dict):
                    source_models.append(SourceModel(**source))
                else:
                    source_models.append(SourceModel(
                        text=source.get('text', ''),
                        score=source.get('score', 0.0),
                        metadata=source.get('metadata', {}),
                        file_name=source.get('file_name'),
                        page_number=source.get('page_number'),
                        node_id=source.get('node_id')
                    ))
            
            history.append(ChatTurnResponse(
                question=turn.question,
                answer=turn.answer,
                sources=source_models,
                timestamp=turn.timestamp,
                reasoning_content=turn.reasoning_content,
            ))
        
        return SessionDetailResponse(
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            history=history,
        )
    
    def get_session_history(self, session_id: str) -> SessionHistoryResponse:
        """获取指定会话的历史记录
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话历史响应
        """
        logger.info("获取会话历史", session_id=session_id)
        
        # 尝试从文件加载会话
        sessions_dir = config.SESSIONS_PATH / "default"
        session_file = sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            raise FileNotFoundError(f"会话不存在: {session_id}")
        
        session = load_session_from_file(str(session_file))
        if session is None:
            raise ValueError(f"无法加载会话: {session_id}")
        
        # 转换历史记录
        history = []
        for turn in session.history:
            source_models = []
            for source in turn.sources:
                if isinstance(source, dict):
                    source_models.append(SourceModel(**source))
                else:
                    source_models.append(SourceModel(
                        text=source.get('text', ''),
                        score=source.get('score', 0.0),
                        metadata=source.get('metadata', {}),
                        file_name=source.get('file_name'),
                        page_number=source.get('page_number'),
                        node_id=source.get('node_id')
                    ))
            
            history.append(ChatTurnResponse(
                question=turn.question,
                answer=turn.answer,
                sources=source_models,
                timestamp=turn.timestamp,
                reasoning_content=turn.reasoning_content,
            ))
        
        return SessionHistoryResponse(
            session_id=session.session_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            history=history,
        )
    
    def list_sessions(self) -> SessionListResponse:
        """列出所有会话
        
        Returns:
            会话列表响应
        """
        logger.info("列出所有会话")
        
        # 获取会话元数据（单用户模式，user_email=None）
        sessions_metadata = get_user_sessions_metadata(user_email=None)
        
        # 转换为 SessionInfo 列表
        sessions = []
        for metadata in sessions_metadata:
            sessions.append(SessionInfo(
                session_id=metadata['session_id'],
                title=metadata.get('title', '新对话'),
                created_at=metadata['created_at'],
                updated_at=metadata['updated_at'],
                turn_count=metadata.get('message_count', 0),
            ))
        
        return SessionListResponse(
            sessions=sessions,
            total=len(sessions),
        )
    
    async def stream_chat(self, message: str, session_id: Optional[str] = None) -> AsyncIterator[Dict[str, Any]]:
        """流式对话
        
        Args:
            message: 对话消息
            session_id: 会话ID（可选）
            
        Yields:
            流式响应字典
        """
        logger.info("开始流式对话", session_id=session_id, message=message[:50] if len(message) > 50 else message)
        
        # 确保会话存在
        if session_id:
            current_session = self.chat_manager.get_current_session()
            if not current_session or current_session.session_id != session_id:
                self.chat_manager.start_session(session_id=session_id)
        elif not self.chat_manager.get_current_session():
            self.chat_manager.start_session()
        
        # 使用 ChatManager 的流式对话
        async for chunk in self.chat_manager.stream_chat(message):
            yield chunk
    
    def list_collections(self) -> list:
        """列出所有向量集合"""
        try:
            collections = self.index_manager.list_collections()
            logger.info("列出集合", count=len(collections))
            return collections
        except Exception as e:
            logger.error("列出集合失败", error=str(e))
            return []
    
    def delete_collection(self, collection_name: str) -> bool:
        """删除向量集合"""
        try:
            self.index_manager.delete_collection(collection_name)
            logger.info("删除集合", collection=collection_name)
            return True
        except Exception as e:
            logger.error("删除集合失败", collection=collection_name, error=str(e))
            return False
    
    def close(self):
        """关闭服务，释放资源"""
        logger.info("关闭RAGService")
        
        if self._index_manager:
            try:
                self._index_manager.close()
            except Exception as e:
                logger.warning("关闭IndexManager失败", error=str(e))
        
        self._index_manager = None
        self._modular_query_engine = None
        self._chat_manager = None
        
        logger.info("RAGService已关闭")
    
    def __enter__(self):
        """支持上下文管理器"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持上下文管理器"""
        self.close()
