"""
RAG服务：会话管理功能

主要功能：
- 会话历史管理
- 会话创建和查询
- 会话列表
"""

from typing import Optional, Dict, Any

from backend.business.chat.utils import get_user_sessions_metadata, load_session_from_file
from backend.infrastructure.logger import get_logger
from backend.infrastructure.config import config
from backend.business.rag_api.models import (
    SessionDetailResponse,
    SessionHistoryResponse,
    SessionListResponse,
    SessionInfo,
    ChatTurnResponse,
    CreateSessionRequest,
)
from backend.business.rag_engine.models import SourceModel

logger = get_logger('rag_service')


def get_chat_history(chat_manager, session_id: Optional[str] = None):
    """获取对话历史"""
    if session_id:
        current_session = chat_manager.get_current_session()
        if not current_session or current_session.session_id != session_id:
            chat_manager.start_session(session_id=session_id)
    return chat_manager.get_current_session()


def clear_chat_history(chat_manager, session_id: str) -> bool:
    """清空对话历史"""
    try:
        chat_manager.reset_session()
        logger.info("清空对话历史", session_id=session_id)
        return True
    except Exception as e:
        logger.error("清空对话历史失败", session_id=session_id, error=str(e))
        return False


def start_new_session(chat_manager, request: CreateSessionRequest) -> Dict[str, Any]:
    """创建新会话"""
    logger.info("创建新会话", session_id=request.session_id, has_message=request.message is not None)
    
    session = chat_manager.start_session(session_id=request.session_id)
    
    if request.message:
        answer, sources, reasoning_content = chat_manager.chat(request.message)
        logger.info("新会话创建并发送第一条消息", session_id=session.session_id)
    
    return {
        'session_id': session.session_id,
        'title': session.title,
        'created_at': session.created_at,
        'updated_at': session.updated_at,
        'turn_count': len(session.history),
    }


def get_current_session_detail(chat_manager) -> SessionDetailResponse:
    """获取当前会话详情（包含完整历史）"""
    session = chat_manager.get_current_session()
    if session is None:
        raise ValueError("当前没有活跃会话")
    
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
    
    return SessionDetailResponse(
        session_id=session.session_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        history=history,
    )


def get_session_history(session_id: str) -> SessionHistoryResponse:
    """获取指定会话的历史记录"""
    logger.info("获取会话历史", session_id=session_id)
    
    sessions_dir = config.SESSIONS_PATH / "default"
    session_file = sessions_dir / f"{session_id}.json"
    
    if not session_file.exists():
        raise FileNotFoundError(f"会话不存在: {session_id}")
    
    session = load_session_from_file(str(session_file))
    if session is None:
        raise ValueError(f"无法加载会话: {session_id}")
    
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


def list_sessions(user_email: str = None) -> SessionListResponse:
    """列出用户的所有会话"""
    logger.info("列出会话", user_email=user_email)
    
    sessions_metadata = get_user_sessions_metadata(user_email)
    
    sessions = [
        SessionInfo(
            session_id=meta['session_id'],
            title=meta['title'],
            created_at=meta['created_at'],
            updated_at=meta['updated_at'],
            turn_count=meta.get('message_count', 0),
        )
        for meta in sessions_metadata
    ]
    
    return SessionListResponse(
        sessions=sessions,
        total=len(sessions),
    )
