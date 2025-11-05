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
        # 使用模块化查询引擎（返回包含 reasoning_content）
        answer, sources, reasoning_content, trace_info = service.modular_query_engine.query(question, collect_trace=False)
        
        # 构造响应
        response = RAGResponse(
            answer=answer,
            sources=sources,
            metadata={
                'user_id': user_id,
                'session_id': session_id,
                'question': question,
                'reasoning_content': reasoning_content,  # 包含推理链内容
            }
        )
        
        logger.info(f"查询成功: sources={len(sources)}, answer_len={len(answer)}")
        if reasoning_content:
            logger.debug(f"推理链内容已包含（长度: {len(reasoning_content)} 字符）")
        return response
        
    except Exception as e:
        logger.error(f"查询失败: {e}", exc_info=True)
        raise

