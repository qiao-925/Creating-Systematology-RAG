"""
FastAPI 依赖注入
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.user_manager import UserManager
from src.business.services.rag_service import RAGService
from src.api.auth import verify_token
from src.logger import setup_logger

logger = setup_logger('api_dependencies')

# HTTP Bearer Token 安全方案
security = HTTPBearer()


def get_user_manager() -> UserManager:
    """获取 UserManager 实例（单例）"""
    if not hasattr(get_user_manager, '_instance'):
        get_user_manager._instance = UserManager()
    return get_user_manager._instance


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_manager: UserManager = Depends(get_user_manager)
) -> dict:
    """获取当前认证用户
    
    Args:
        credentials: HTTP Bearer Token
        user_manager: UserManager 实例
        
    Returns:
        用户信息字典
        
    Raises:
        HTTPException: Token 无效或用户不存在
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN",
                "message": "无效的认证令牌",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email = payload.get("sub")  # JWT 标准使用 "sub" 作为用户标识
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "MISSING_USER_INFO",
                "message": "Token 中缺少用户信息",
            },
        )
    
    # 验证用户是否仍然存在
    if email not in user_manager.users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "USER_NOT_FOUND",
                "message": "用户不存在",
            },
        )
    
    user_data = user_manager.users[email]
    return {
        "email": email,
        "collection_name": user_data.get("collection_name"),
    }


def get_rag_service(
    current_user: dict = Depends(get_current_user)
) -> RAGService:
    """获取 RAGService 实例（按用户隔离）
    
    Args:
        current_user: 当前认证用户
        
    Returns:
        RAGService 实例（使用用户的 collection_name）
    """
    collection_name = current_user.get("collection_name")
    return RAGService(collection_name=collection_name)




