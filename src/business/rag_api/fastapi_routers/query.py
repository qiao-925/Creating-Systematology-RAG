"""
RAG API - FastAPI查询路由

提供RAG查询相关的API端点
"""

import asyncio
from fastapi import APIRouter, Depends

from src.business.rag_api.fastapi_dependencies import get_rag_service
from src.business.rag_api.rag_service import RAGService
from src.business.rag_api.models import RAGResponse, QueryRequest
from src.infrastructure.logger import get_logger

logger = get_logger('rag_api_query_router')

router = APIRouter(prefix="/query", tags=["查询"])


@router.post("", response_model=RAGResponse)
async def query(
    request: QueryRequest,
    rag_service: RAGService = Depends(get_rag_service),
):
    """RAG 查询接口
    
    使用 Pydantic 验证请求和响应模型
    """
    logger.info(
        "收到查询请求",
        question=request.question[:50] if len(request.question) > 50 else request.question,
        session_id=request.session_id,
        top_k=request.top_k,
        strategy=request.strategy
    )
    response = await asyncio.to_thread(
        rag_service.query,
        question=request.question,
        user_id=None,  # 单用户模式，不需要用户标识
        session_id=request.session_id,
        top_k=request.top_k,
        strategy=request.strategy
    )
    return response
