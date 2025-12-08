"""
RAG API - FastAPI应用主入口

创建和配置FastAPI应用
"""

import os
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.business.rag_api.fastapi_routers import chat
from src.infrastructure.logger import get_logger

logger = get_logger('rag_api_fastapi_app')

# 创建 FastAPI 应用
app = FastAPI(
    title="RAG Chat API",
    description="极简对话 API - 流式对话与会话历史",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置 CORS（允许跨域请求）
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if "*" not in cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 统一错误处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """统一 HTTP 异常响应格式"""
    detail = exc.detail
    if isinstance(detail, dict):
        error_code = detail.get("code", "HTTP_ERROR")
        error_message = detail.get("message", str(detail))
        error_detail = detail.get("detail")
    else:
        error_code = "HTTP_ERROR"
        error_message = str(detail)
        error_detail = None
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": error_code,
                "message": error_message,
                "detail": error_detail,
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """统一验证错误响应格式"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求参数验证失败",
                "detail": str(exc.errors()),
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """统一通用异常响应格式"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误",
                "detail": str(exc) if os.getenv("DEBUG", "false").lower() == "true" else None,
            }
        }
    )


# 注册路由
# app.include_router(query.router)  # 已移除：只保留对话接口
app.include_router(chat.router)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
