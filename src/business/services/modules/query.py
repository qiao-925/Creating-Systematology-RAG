"""
RAG服务 - 查询处理模块
查询相关方法
"""

from typing import Optional

from src.logger import setup_logger
from src.business.services.modules.models import RAGResponse

logger = setup_logger('rag_service')


def handle_query(
    service,
    question: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    **kwargs
) -> RAGResponse:
    """处理查询请求
    
    Args:
        service: RAGService实例
        question: 用户问题
        user_id: 用户ID
        session_id: 会话ID
        **kwargs: 其他参数
        
    Returns:
        RAGResponse: 查询响应
    """
    logger.info(f"收到查询请求: user={user_id}, session={session_id}, question={question[:50]}...")
    
    try:
        # 使用模块化查询引擎（如果可用）
        if hasattr(service, 'modular_query_engine') and service.use_modular_engine:
            answer, sources, trace_info = service.modular_query_engine.query(question, collect_trace=False)
        else:
            # 降级到旧查询引擎
            answer, sources, trace_info = service.query_engine.query(question, collect_trace=False)
        
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

