"""
用户管理模块单元测试
"""

import pytest
from pathlib import Path
import tempfile
import json
from src.user_manager import UserManager


class TestUserManager:
    """用户管理器测试"""
    
    @pytest.fixture
    def temp_users_file(self, tmp_path):
        """临时用户数据文件"""
        return tmp_path / "test_users.json"
    
    @pytest.fixture
    def user_manager(self, temp_users_file):
        """创建用户管理器实例"""
        return UserManager(users_file=temp_users_file)
    
    def test_register_new_user(self, user_manager):
        """测试注册新用户"""
        result = user_manager.register("test@example.com", "password123")
        
        assert result == True
        assert user_manager.get_user_count() == 1
        assert "test@example.com" in user_manager.users
    
    def test_register_duplicate_user(self, user_manager):
        """测试重复注册"""
        user_manager.register("test@example.com", "password123")
        result = user_manager.register("test@example.com", "password456")
        
        assert result == False
        assert user_manager.get_user_count() == 1
    
    def test_login_success(self, user_manager):
        """测试登录成功"""
        user_manager.register("test@example.com", "password123")
        collection = user_manager.login("test@example.com", "password123")
        
        assert collection is not None
        assert collection.startswith("user_")
        assert len(collection) == 13  # "user_" + 8位哈希
    
    def test_login_wrong_password(self, user_manager):
        """测试密码错误"""
        user_manager.register("test@example.com", "password123")
        collection = user_manager.login("test@example.com", "wrongpassword")
        
        assert collection is None
    
    def test_login_nonexistent_user(self, user_manager):
        """测试不存在的用户"""
        collection = user_manager.login("nonexist@example.com", "password")
        
        assert collection is None
    
    def test_collection_name_consistency(self, user_manager):
        """测试同一用户的 collection_name 一致性"""
        user_manager.register("test@example.com", "password")
        collection1 = user_manager.login("test@example.com", "password")
        collection2 = user_manager.login("test@example.com", "password")
        
        assert collection1 == collection2
    
    def test_different_users_different_collections(self, user_manager):
        """测试不同用户有不同的 collection"""
        user_manager.register("user1@example.com", "password")
        user_manager.register("user2@example.com", "password")
        
        collection1 = user_manager.login("user1@example.com", "password")
        collection2 = user_manager.login("user2@example.com", "password")
        
        assert collection1 != collection2
    
    def test_persistence(self, temp_users_file):
        """测试数据持久化"""
        # 创建用户管理器并注册用户
        um1 = UserManager(users_file=temp_users_file)
        um1.register("test@example.com", "password123")
        collection1 = um1.login("test@example.com", "password123")
        
        # 创建新的用户管理器实例（模拟重启）
        um2 = UserManager(users_file=temp_users_file)
        collection2 = um2.login("test@example.com", "password123")
        
        # collection 应该相同
        assert collection1 == collection2
        assert um2.get_user_count() == 1
    
    def test_user_metadata(self, user_manager, temp_users_file):
        """测试用户元数据"""
        user_manager.register("test@example.com", "password")
        
        # 读取文件检查元数据
        with open(temp_users_file, 'r', encoding='utf-8') as f:
            users = json.load(f)
        
        assert "test@example.com" in users
        assert "password_hash" in users["test@example.com"]
        assert "collection_name" in users["test@example.com"]
        assert "created_at" in users["test@example.com"]
    
    def test_password_hash_security(self, user_manager):
        """测试密码哈希（不存储明文）"""
        user_manager.register("test@example.com", "password123")
        
        # 密码不应该以明文存储
        user_data = user_manager.users["test@example.com"]
        assert user_data["password_hash"] != "password123"
        assert len(user_data["password_hash"]) == 64  # SHA256 哈希长度
    
    def test_multiple_users(self, user_manager):
        """测试多个用户"""
        users = [
            ("user1@example.com", "pass1"),
            ("user2@example.com", "pass2"),
            ("user3@example.com", "pass3"),
        ]
        
        # 批量注册
        for email, password in users:
            assert user_manager.register(email, password) == True
        
        assert user_manager.get_user_count() == 3
        
        # 验证每个用户都能登录
        for email, password in users:
            collection = user_manager.login(email, password)
            assert collection is not None


