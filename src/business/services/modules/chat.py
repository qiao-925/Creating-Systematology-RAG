"""
RAG服务 - 对话处理模块
对话相关方法
"""

from typing import Optional

from src.logger import setup_logger
from src.chat_manager import ChatSession
from src.business.services.modules.models import ChatResponse

logger = setup_logger('rag_service')


def handle_chat(
    service,
    message: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **kwargs
) -> ChatResponse:
    """处理对话请求
    
    Args:
        service: RAGService实例
        message: 用户消息
        session_id: 会话ID
        user_id: 用户ID
        **kwargs: 其他参数
        
    Returns:
        ChatResponse: 对话响应
    """
    logger.info(f"收到对话请求: user={user_id}, session={session_id}, message={message[:50]}...")
    
    try:
        # 获取或创建会话
        if session_id:
            session = service.chat_manager.get_current_session()
            if not session or session.session_id != session_id:
                session = service.chat_manager.start_session(session_id=session_id)
        else:
            session = service.chat_manager.start_session()
        
        # 发送消息（返回包含 reasoning_content）
        answer, sources, reasoning_content = service.chat_manager.chat(message=message)
        
        # 构造响应
        response = ChatResponse(
            answer=answer,
            sources=sources,
            session_id=session.session_id,
            turn_count=len(session.history),
            metadata={
                'user_id': user_id,
                'message': message,
                'reasoning_content': reasoning_content,  # 包含推理链内容
            }
        )
        
        logger.info(f"对话成功: session={session.session_id}, turn={response.turn_count}")
        if reasoning_content:
            logger.debug(f"推理链内容已包含（长度: {len(reasoning_content)} 字符）")
        return response
        
    except Exception as e:
        logger.error(f"对话失败: {e}", exc_info=True)
        raise

