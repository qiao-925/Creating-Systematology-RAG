"""
RAG服务：对话功能

主要功能：
- 对话处理
- 会话管理
"""

from typing import Optional

from backend.infrastructure.logger import get_logger
from backend.business.rag_api.models import ChatRequest, ChatResponse

logger = get_logger('rag_service')


def execute_chat(
    chat_manager,
    request: ChatRequest,
    user_id: Optional[str] = None
) -> ChatResponse:
    """执行对话
    
    Args:
        chat_manager: 对话管理器实例
        request: 对话请求
        user_id: 用户ID（可选）
        
    Returns:
        对话响应
    """
    logger.info(
        "收到对话请求",
        user_id=user_id,
        session_id=request.session_id,
        message=request.message[:50] if len(request.message) > 50 else request.message
    )
    
    try:
        # 确保会话存在
        if request.session_id:
            current_session = chat_manager.get_current_session()
            if not current_session or current_session.session_id != request.session_id:
                chat_manager.start_session(session_id=request.session_id)
        elif not chat_manager.get_current_session():
            chat_manager.start_session()
        
        # 执行对话
        answer, sources, reasoning_content = chat_manager.chat(request.message)
        
        # 获取当前会话
        session = chat_manager.get_current_session()
        
        # 转换为响应格式
        response = ChatResponse(
            answer=answer,
            sources=sources,
            session_id=session.session_id if session else None,
            turn_count=len(session.history) if session else 0,
            metadata={
                'user_id': user_id,
                'message': request.message,
                'reasoning_content': reasoning_content
            }
        )
        
        logger.info(
            "对话成功",
            user_id=user_id,
            session_id=session.session_id if session else None,
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
