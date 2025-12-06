"""
对话路由
"""

import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.dependencies import get_rag_service, get_current_user
from src.business.services.rag_service import RAGService
from src.business.services.modules.models import ChatResponse
from src.logger import setup_logger

logger = setup_logger('api_chat_router')

router = APIRouter(prefix="/chat", tags=["对话"])


class ChatRequest(BaseModel):
    """对话请求"""
    message: str
    session_id: str | None = None


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
):
    """对话接口
    
    Args:
        request: 对话请求
        current_user: 当前用户（自动注入）
        rag_service: RAGService 实例（自动注入，已按用户隔离）
        
    Returns:
        ChatResponse: 对话响应
    """
    logger.info(f"收到对话请求: user={current_user['email']}, message={request.message[:50]}...")
    
    # 使用 asyncio.to_thread 包装同步调用
    response = await asyncio.to_thread(
        rag_service.chat,
        message=request.message,
        session_id=request.session_id,
        user_id=current_user["email"],
    )
    
    return response




