"""
JWT 认证模块
与现有 UserManager 集成，提供 JWT Token 认证
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.user_manager import UserManager
from src.logger import setup_logger
from src.config import config

logger = setup_logger('api_auth')

# 密码加密上下文（使用 bcrypt）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 配置（从 config 读取，默认值仅用于开发）
SECRET_KEY = config.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码（可能是旧格式或新格式）
        
    Returns:
        True: 密码正确
        False: 密码错误
    """
    # 兼容旧格式（SHA256）和新格式（bcrypt）
    if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
        # bcrypt 格式
        return pwd_context.verify(plain_password, hashed_password)
    else:
        # 旧格式 SHA256（向后兼容）
        import hashlib
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def get_password_hash(password: str) -> str:
    """生成密码哈希（使用 bcrypt）
    
    Args:
        password: 明文密码
        
    Returns:
        bcrypt 哈希值
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT Token
    
    Args:
        data: Token 数据（通常包含 user_id, email 等）
        expires_delta: 过期时间（可选）
        
    Returns:
        JWT Token 字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(user_manager: UserManager, email: str, password: str) -> Optional[dict]:
    """验证用户并返回用户信息
    
    Args:
        user_manager: UserManager 实例
        email: 用户邮箱
        password: 密码
        
    Returns:
        用户信息字典（包含 email, collection_name）或 None
    """
    if email not in user_manager.users:
        logger.warning(f"认证失败：用户不存在 {email}")
        return None
    
    user_data = user_manager.users[email]
    stored_hash = user_data.get("password_hash")
    
    if not stored_hash:
        logger.warning(f"认证失败：用户数据异常 {email}")
        return None
    
    # 验证密码（兼容旧格式和新格式）
    if not verify_password(password, stored_hash):
        logger.warning(f"认证失败：密码错误 {email}")
        return None
    
    logger.info(f"用户认证成功: {email}")
    return {
        "email": email,
        "collection_name": user_data.get("collection_name"),
    }


def verify_token(token: str) -> Optional[dict]:
    """验证 JWT Token
    
    Args:
        token: JWT Token 字符串
        
    Returns:
        Token 载荷（包含用户信息）或 None
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token 验证失败: {e}")
        return None

