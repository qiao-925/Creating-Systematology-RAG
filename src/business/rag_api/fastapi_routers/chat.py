"""
RAG API - FastAPI对话路由

极简设计：只提供两个核心接口
- 流式对话（自动创建/使用会话）
- 获取会话历史
"""

import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.business.rag_api.fastapi_dependencies import get_rag_service
from src.business.rag_api.rag_service import RAGService
from src.business.rag_api.models import (
    ChatRequest,
    SessionHistoryResponse,
)
from src.infrastructure.logger import get_logger

logger = get_logger('rag_api_chat_router')

router = APIRouter(prefix="/chat", tags=["对话"])


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service),
):
    """流式对话接口
    
    创建会话并发送消息，使用 Server-Sent Events (SSE) 实时返回答案
    
    - 如果提供了 session_id，使用该会话
    - 如果没有提供 session_id，自动创建新会话
    - 流式返回答案，包含 token、sources 和 done 事件
    """
    logger.info(
        "收到流式对话请求",
        message=request.message[:50] if len(request.message) > 50 else request.message,
        session_id=request.session_id
    )
    
    async def generate_stream():
        """生成 SSE 流"""
        try:
            # 确保会话存在（如果 session_id 为空，stream_chat 会自动创建）
            async for chunk in rag_service.stream_chat(
                message=request.message,
                session_id=request.session_id
            ):
                # 格式化为 SSE 格式
                data = json.dumps(chunk, ensure_ascii=False)
                yield f"data: {data}\n\n"
        except Exception as e:
            logger.error("流式对话失败", error=str(e), exc_info=True)
            error_chunk = {
                "type": "error",
                "data": {"message": str(e)}
            }
            data = json.dumps(error_chunk, ensure_ascii=False)
            yield f"data: {data}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/sessions/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history(
    session_id: str,
    rag_service: RAGService = Depends(get_rag_service),
):
    """获取指定会话的历史记录"""
    logger.info("获取会话历史", session_id=session_id)
    try:
        return await asyncio.to_thread(rag_service.get_session_history, session_id)
    except FileNotFoundError as e:
        logger.warning("会话不存在", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": str(e)}
        )
    except Exception as e:
        logger.error("获取会话历史失败", session_id=session_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "HISTORY_FETCH_FAILED", "message": f"获取会话历史失败: {str(e)}"}
        )
