"""
统一错误响应模型
"""

from pydantic import BaseModel
from typing import Optional


class ErrorDetail(BaseModel):
    """错误详情"""
    code: str
    message: str
    detail: Optional[str] = None


class ErrorResponse(BaseModel):
    """统一错误响应格式"""
    error: ErrorDetail




