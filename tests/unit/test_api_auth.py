"""
API 认证模块单元测试
测试 JWT Token 创建、验证、密码哈希等功能
"""

import pytest
from datetime import timedelta
from pathlib import Path
import tempfile

from src.business.rag_api.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    authenticate_user,
    verify_token,
)
from src.infrastructure.user_manager import UserManager


class TestPasswordHashing:
    """密码哈希测试"""
    
    def test_get_password_hash(self):
        """测试密码哈希生成"""
        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # bcrypt 每次生成的哈希都不同（因为有盐值）
        assert hash1 != hash2
        # 但都应该以 $2b$ 或 $2a$ 开头（bcrypt 格式）
        assert hash1.startswith("$2b$") or hash1.startswith("$2a$")
        assert hash2.startswith("$2b$") or hash2.startswith("$2a$")
    
    def test_verify_password_bcrypt(self):
        """测试 bcrypt 密码验证"""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        # 正确密码应该验证通过
        assert verify_password(password, hashed) == True
        
        # 错误密码应该验证失败
        assert verify_password("wrong_password", hashed) == False
    
    def test_verify_password_sha256_compatibility(self):
        """测试 SHA256 密码验证（向后兼容）"""
        import hashlib
        password = "test_password_123"
        sha256_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # 旧格式 SHA256 应该仍然可以验证
        assert verify_password(password, sha256_hash) == True
        assert verify_password("wrong_password", sha256_hash) == False


class TestJWTToken:
    """JWT Token 测试"""
    
    def test_create_access_token(self):
        """测试 Token 创建"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        # Token 应该包含三个部分（用 . 分隔）
        assert len(token.split(".")) == 3
    
    def test_create_access_token_with_expires_delta(self):
        """测试带过期时间的 Token 创建"""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(minutes=60)
        token = create_access_token(data, expires_delta=expires_delta)
        
        assert isinstance(token, str)
        # 验证 Token 可以解码
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test@example.com"
    
    def test_verify_token_valid(self):
        """测试有效 Token 验证"""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert "exp" in payload
    
    def test_verify_token_invalid(self):
        """测试无效 Token 验证"""
        invalid_token = "invalid.token.here"
        payload = verify_token(invalid_token)
        
        assert payload is None
    
    def test_verify_token_expired(self):
        """测试过期 Token 验证"""
        from datetime import datetime, timedelta
        from jose import jwt
        from src.business.rag_api.auth import SECRET_KEY, ALGORITHM
        
        # 创建已过期的 Token
        data = {"sub": "test@example.com", "exp": datetime.utcnow() - timedelta(hours=1)}
        expired_token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
        
        payload = verify_token(expired_token)
        # 过期 Token 应该返回 None
        assert payload is None


class TestAuthenticateUser:
    """用户认证测试"""
    
    @pytest.fixture
    def temp_users_file(self, tmp_path):
        """临时用户数据文件"""
        return tmp_path / "test_users.json"
    
    @pytest.fixture
    def user_manager(self, temp_users_file):
        """创建用户管理器实例"""
        return UserManager(users_file=temp_users_file)
    
    def test_authenticate_user_success(self, user_manager):
        """测试成功认证"""
        email = "test@example.com"
        password = "password123"
        
        # 注册用户
        user_manager.register(email, password)
        
        # 认证用户
        user = authenticate_user(user_manager, email, password)
        
        assert user is not None
        assert user["email"] == email
        assert "collection_name" in user
    
    def test_authenticate_user_wrong_password(self, user_manager):
        """测试错误密码认证"""
        email = "test@example.com"
        password = "password123"
        
        # 注册用户
        user_manager.register(email, password)
        
        # 使用错误密码认证
        user = authenticate_user(user_manager, email, "wrong_password")
        
        assert user is None
    
    def test_authenticate_user_nonexistent(self, user_manager):
        """测试不存在的用户认证"""
        user = authenticate_user(user_manager, "nonexist@example.com", "password")
        
        assert user is None
    
    def test_authenticate_user_bcrypt_password(self, user_manager):
        """测试 bcrypt 密码认证（新注册用户）"""
        email = "newuser@example.com"
        password = "new_password"
        
        # 使用 API 注册（会使用 bcrypt）
        from src.business.rag_api.auth import get_password_hash
        password_hash = get_password_hash(password)
        import hashlib
        collection_name = f"user_{hashlib.md5(email.encode()).hexdigest()[:8]}"
        
        user_manager.users[email] = {
            "password_hash": password_hash,
            "collection_name": collection_name,
        }
        user_manager._save()
        
        # 认证应该成功
        user = authenticate_user(user_manager, email, password)
        assert user is not None
        assert user["email"] == email

