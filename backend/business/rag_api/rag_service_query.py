"""
RAG服务：查询功能

主要功能：
- 查询处理
- 响应格式化
"""

from typing import Optional

from backend.infrastructure.logger import get_logger
from backend.infrastructure.embeddings.hf_stats import set_current_task_id, finish_task
from backend.business.rag_api.models import QueryRequest, RAGResponse
from backend.business.rag_engine.models import SourceModel

logger = get_logger('rag_service')


def execute_query(
    query_engine,
    request: QueryRequest,
    user_id: Optional[str] = None,
    collect_trace: bool = False
) -> RAGResponse:
    """执行查询
    
    Args:
        query_engine: 查询引擎实例
        request: 查询请求
        user_id: 用户ID（可选）
        collect_trace: 是否收集追踪信息
        
    Returns:
        RAG响应
    """
    # 设置当前任务 ID（用于 HF API 统计）
    task_id = request.session_id or user_id or 'anonymous'
    set_current_task_id(task_id)
    
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
        answer, sources, reasoning_content, trace_info = query_engine.query(
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
        
        if collect_trace and trace_info:
            metadata['trace_info'] = trace_info
        
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
