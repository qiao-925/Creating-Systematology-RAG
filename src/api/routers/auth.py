"""
认证路由（登录、注册）
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
import hashlib

from src.api.models.auth import LoginRequest, RegisterRequest, TokenResponse, UserInfo
from src.api.dependencies import get_user_manager, get_current_user
from src.api.auth import authenticate_user, create_access_token, get_password_hash
from src.logger import setup_logger

logger = setup_logger('api_auth_router')

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    user_manager = Depends(get_user_manager)
):
    """用户登录
    
    Returns:
        TokenResponse: 包含 access_token 和用户信息
    """
    user = authenticate_user(user_manager, request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "邮箱或密码错误",
            },
        )
    
    # 创建 JWT Token
    access_token = create_access_token(data={"sub": user["email"]})
    
    logger.info(f"用户登录成功: {user['email']}")
    return TokenResponse(
        access_token=access_token,
        email=user["email"],
        collection_name=user["collection_name"],
    )


@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    user_manager = Depends(get_user_manager)
):
    """用户注册
    
    Returns:
        TokenResponse: 包含 access_token 和用户信息
    """
    if request.email in user_manager.users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EMAIL_EXISTS",
                "message": "邮箱已被注册",
            },
        )
    
    # 使用 bcrypt 哈希密码
    password_hash = get_password_hash(request.password)
    
    # 生成用户专属的 collection_name
    collection_name = f"user_{hashlib.md5(request.email.encode()).hexdigest()[:8]}"
    
    # 注册用户
    user_manager.users[request.email] = {
        "password_hash": password_hash,
        "collection_name": collection_name,
        "created_at": datetime.now().isoformat(),
        "active_session_id": None,
        "sessions": []
    }
    user_manager._save()
    
    logger.info(f"用户注册成功: {request.email}, collection: {collection_name}")
    
    # 创建 JWT Token
    access_token = create_access_token(data={"sub": request.email})
    
    return TokenResponse(
        access_token=access_token,
        email=request.email,
        collection_name=collection_name,
    )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """获取当前用户信息"""
    return UserInfo(
        email=current_user["email"],
        collection_name=current_user["collection_name"],
    )




