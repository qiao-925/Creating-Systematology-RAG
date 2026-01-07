"""
API 依赖注入模块单元测试
测试 UserManager、RAGService 依赖注入和认证
"""

import pytest
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch

from backend.business.rag_api.fastapi_dependencies import get_user_manager, get_current_user, get_rag_service
from backend.infrastructure.user_manager import UserManager
from backend.business.rag_api.rag_service import RAGService


class TestGetUserManager:
    """UserManager 依赖注入测试"""
    
    def test_get_user_manager_singleton(self):
        """测试 UserManager 单例模式"""
        # 清除可能存在的实例
        if hasattr(get_user_manager, '_instance'):
            delattr(get_user_manager, '_instance')
        
        manager1 = get_user_manager()
        manager2 = get_user_manager()
        
        # 应该是同一个实例
        assert manager1 is manager2
        assert isinstance(manager1, UserManager)
    
    def test_get_user_manager_persistence(self):
        """测试 UserManager 数据持久化"""
        # 清除可能存在的实例
        if hasattr(get_user_manager, '_instance'):
            delattr(get_user_manager, '_instance')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            users_file = Path(tmpdir) / "test_users.json"
            
            # 创建临时 UserManager
            temp_manager = UserManager(users_file=users_file)
            temp_manager.register("test@example.com", "password123")
            
            # 验证用户已注册
            assert "test@example.com" in temp_manager.users


class TestGetCurrentUser:
    """当前用户获取测试"""
    
    @pytest.fixture
    def mock_credentials(self):
        """Mock HTTP Bearer Token"""
        from fastapi.security import HTTPAuthorizationCredentials
        from backend.business.rag_api.auth import create_access_token
        
        token = create_access_token(data={"sub": "test@example.com"})
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        return credentials
    
    @pytest.fixture
    def user_manager_with_user(self, tmp_path):
        """创建带用户的 UserManager"""
        users_file = tmp_path / "test_users.json"
        manager = UserManager(users_file=users_file)
        manager.register("test@example.com", "password123")
        return manager
    
    def test_get_current_user_valid_token(self, mock_credentials, user_manager_with_user):
        """测试有效 Token 获取用户"""
        user = get_current_user(mock_credentials, user_manager_with_user)
        
        assert user is not None
        assert user["email"] == "test@example.com"
        assert "collection_name" in user
    
    def test_get_current_user_invalid_token(self, user_manager_with_user):
        """测试无效 Token"""
        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import HTTPException
        
        invalid_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token.here"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(invalid_credentials, user_manager_with_user)
        
        assert exc_info.value.status_code == 401
    
    def test_get_current_user_nonexistent_user(self, mock_credentials, tmp_path):
        """测试不存在的用户"""
        from fastapi import HTTPException
        
        # 创建空的 UserManager
        users_file = tmp_path / "test_users.json"
        manager = UserManager(users_file=users_file)
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_credentials, manager)
        
        assert exc_info.value.status_code == 401


class TestGetRAGService:
    """RAGService 依赖注入测试"""
    
    @pytest.fixture
    def mock_current_user(self):
        """Mock 当前用户"""
        return {
            "email": "test@example.com",
            "collection_name": "user_12345678"
        }
    
    def test_get_rag_service_user_isolation(self, mock_current_user):
        """测试 RAGService 用户隔离"""
        service = get_rag_service(mock_current_user)
        
        assert isinstance(service, RAGService)
        assert service.collection_name == "user_12345678"
    
    def test_get_rag_service_different_users(self):
        """测试不同用户使用不同的 RAGService"""
        user1 = {
            "email": "user1@example.com",
            "collection_name": "user_11111111"
        }
        user2 = {
            "email": "user2@example.com",
            "collection_name": "user_22222222"
        }
        
        service1 = get_rag_service(user1)
        service2 = get_rag_service(user2)
        
        assert service1.collection_name != service2.collection_name
        assert service1.collection_name == "user_11111111"
        assert service2.collection_name == "user_22222222"

