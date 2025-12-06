"""
认证相关 Pydantic 模型
"""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """登录请求"""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """注册请求"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"
    email: str
    collection_name: str


class UserInfo(BaseModel):
    """用户信息"""
    email: str
    collection_name: str




