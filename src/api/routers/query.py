"""
查询路由
"""

import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.dependencies import get_rag_service, get_current_user
from src.business.services.rag_service import RAGService
from src.business.services.modules.models import RAGResponse
from src.logger import setup_logger

logger = setup_logger('api_query_router')

router = APIRouter(prefix="/query", tags=["查询"])


class QueryRequest(BaseModel):
    """查询请求"""
    question: str
    session_id: str | None = None


@router.post("", response_model=RAGResponse)
async def query(
    request: QueryRequest,
    current_user: dict = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
):
    """RAG 查询接口
    
    Args:
        request: 查询请求
        current_user: 当前用户（自动注入）
        rag_service: RAGService 实例（自动注入，已按用户隔离）
        
    Returns:
        RAGResponse: 查询结果
    """
    logger.info(f"收到查询请求: user={current_user['email']}, question={request.question[:50]}...")
    
    # 使用 asyncio.to_thread 包装同步调用
    response = await asyncio.to_thread(
        rag_service.query,
        question=request.question,
        user_id=current_user["email"],
        session_id=request.session_id,
    )
    
    return response




