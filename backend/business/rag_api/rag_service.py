"""
RAG API - RAG服务核心模块

提供查询、索引构建、对话等核心功能的统一入口
"""

from typing import Optional, List, AsyncIterator, Dict, Any, TYPE_CHECKING
from pathlib import Path

# 延迟导入：将耗时的导入移到实际使用时
if TYPE_CHECKING:
    from backend.infrastructure.indexer import IndexManager
    from backend.business.rag_engine.core.engine import ModularQueryEngine
    from backend.business.rag_engine.agentic import AgenticQueryEngine
    from backend.business.chat import ChatManager

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
        use_agentic_rag: bool = False,
        model_id: Optional[str] = None,  # 新增：模型 ID
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
        self.use_agentic_rag = use_agentic_rag
        self.model_id = model_id  # 保存模型 ID
        self.engine_kwargs = kwargs
        
        # 延迟初始化（按需加载）
        self._index_manager: Optional[IndexManager] = None
        self._modular_query_engine: Optional[ModularQueryEngine] = None
        self._agentic_query_engine: Optional[AgenticQueryEngine] = None
        self._chat_manager: Optional[ChatManager] = None
        
        logger.info(
            "RAGService初始化",
            collection=self.collection_name,
            top_k=self.similarity_top_k,
            enable_debug=self.enable_debug
        )
    
    @property
    def index_manager(self):
        """获取索引管理器（延迟加载）"""
        if self._index_manager is None:
            from backend.infrastructure.indexer import IndexManager
            logger.info("初始化IndexManager", collection=self.collection_name)
            self._index_manager = IndexManager(collection_name=self.collection_name)
        return self._index_manager
    
    @property
    def modular_query_engine(self):
        """获取模块化查询引擎（延迟加载）"""
        if self._modular_query_engine is None:
            from backend.business.rag_engine.core.engine import ModularQueryEngine
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
    
    def _get_query_engine(self):
        """获取查询引擎（根据 use_agentic_rag 选择）"""
        if self.use_agentic_rag:
            if self._agentic_query_engine is None:
                from backend.business.rag_engine.agentic import AgenticQueryEngine
                logger.info(
                    "初始化AgenticQueryEngine",
                    top_k=self.similarity_top_k,
                    markdown_formatting=self.enable_markdown_formatting
                )
                self._agentic_query_engine = AgenticQueryEngine(
                    index_manager=self.index_manager,
                    similarity_top_k=self.similarity_top_k,
                    enable_markdown_formatting=self.enable_markdown_formatting,
                    **self.engine_kwargs
                )
            return self._agentic_query_engine
        else:
            return self.modular_query_engine
    
    @property
    def chat_manager(self):
        """获取对话管理器（延迟加载）"""
        if self._chat_manager is None:
            from backend.business.chat import ChatManager
            logger.info("初始化ChatManager", top_k=self.similarity_top_k, model_id=self.model_id)
            self._chat_manager = ChatManager(
                index_manager=self.index_manager,
                similarity_top_k=self.similarity_top_k,
                use_agentic_rag=self.use_agentic_rag,
                model_id=self.model_id,  # 传入模型 ID
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
        from backend.business.rag_api.rag_service_query import execute_query as _execute_query
        query_engine = self._get_query_engine()
        return _execute_query(query_engine, request, user_id, collect_trace)
    
    def _load_documents_from_source(self, source_path: str) -> tuple[list, Optional[str]]:
        """从数据源加载文档（私有方法）"""
        from backend.business.rag_api.rag_service_index import load_documents_from_source
        return load_documents_from_source(source_path)
    
    def build_index(
        self,
        source_path: str,
        collection_name: Optional[str] = None,
        **kwargs
    ) -> IndexResult:
        """构建索引接口"""
        target_collection = collection_name or self.collection_name
        from backend.business.rag_api.rag_service_index import build_index as build_index_func
        result = build_index_func(self.index_manager, source_path, target_collection)
        # 适配返回格式
        return IndexResult(
            success=result.success,
            collection_name=result.collection_name,
            doc_count=result.document_count,
            message=result.message
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
        from backend.business.rag_api.rag_service_chat import execute_chat as _execute_chat
        return _execute_chat(self.chat_manager, request, user_id)
    
    def get_chat_history(self, session_id: Optional[str] = None):
        """获取对话历史"""
        from backend.business.rag_api.rag_service_sessions import get_chat_history as _get_chat_history
        return _get_chat_history(self.chat_manager, session_id)

    def clear_chat_history(self, session_id: str) -> bool:
        """清空对话历史"""
        from backend.business.rag_api.rag_service_sessions import clear_chat_history as _clear_chat_history
        return _clear_chat_history(self.chat_manager, session_id)

    def start_new_session(self, request: CreateSessionRequest) -> Dict[str, Any]:
        """创建新会话"""
        from backend.business.rag_api.rag_service_sessions import start_new_session as _start_new_session
        return _start_new_session(self.chat_manager, request)

    def get_current_session_detail(self) -> SessionDetailResponse:
        """获取当前会话详情（包含完整历史）"""
        from backend.business.rag_api.rag_service_sessions import get_current_session_detail as _get_current_session_detail
        return _get_current_session_detail(self.chat_manager)
    
    async def stream_chat(self, message: str, session_id: Optional[str] = None) -> AsyncIterator[Dict[str, Any]]:
        """流式对话"""
        logger.info("开始流式对话", session_id=session_id, message=message[:50] if len(message) > 50 else message)
        
        if session_id:
            current_session = self.chat_manager.get_current_session()
            if not current_session or current_session.session_id != session_id:
                self.chat_manager.start_session(session_id=session_id)
        elif not self.chat_manager.get_current_session():
            self.chat_manager.start_session()
        
        async for chunk in self.chat_manager.stream_chat(message):
            yield chunk
    
    def get_session_history(self, session_id: str) -> SessionHistoryResponse:
        """获取指定会话的历史记录"""
        from backend.business.rag_api.rag_service_sessions import get_session_history as _get_session_history
        return _get_session_history(session_id)

    def list_sessions(self, user_email: str = None) -> SessionListResponse:
        """列出用户的所有会话"""
        from backend.business.rag_api.rag_service_sessions import list_sessions as _list_sessions
        return _list_sessions(user_email)

    def list_collections(self) -> list:
        """列出所有向量集合"""
        from backend.business.rag_api.rag_service_index import list_collections as _list_collections
        return _list_collections(self.index_manager)

    def delete_collection(self, collection_name: str) -> bool:
        """删除向量集合"""
        from backend.business.rag_api.rag_service_index import delete_collection as _delete_collection
        return _delete_collection(self.index_manager, collection_name)
    
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
