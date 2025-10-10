"""
用户管理模块
提供简单的用户注册和登录功能（仅用于反馈收集）

⚠️ 安全警告：
- 这是最简单的实现，仅用于反馈收集和演示
- 不适合生产环境（密码哈希算法简单，无盐值）
- 无密码强度验证、无会话管理、无邮箱验证
"""

import hashlib
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.logger import setup_logger

logger = setup_logger('user_manager')


class UserManager:
    """简单的用户管理（仅用于反馈收集）"""
    
    def __init__(self, users_file: Optional[Path] = None):
        """初始化用户管理器
        
        Args:
            users_file: 用户数据文件路径，默认为 data/users.json
        """
        if users_file is None:
            users_file = Path(__file__).parent.parent / "data" / "users.json"
        
        self.users_file = users_file
        self.users_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载或初始化用户数据
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
                logger.info(f"加载了 {len(self.users)} 个用户")
            except Exception as e:
                logger.error(f"加载用户数据失败: {e}")
                self.users = {}
        else:
            self.users = {}
            logger.info("创建新的用户数据库")
        
        # 确保默认测试账号存在
        self._ensure_test_account()
    
    def _hash_password(self, password: str) -> str:
        """简单密码哈希（仅用于演示）
        
        ⚠️ 生产环境应使用 bcrypt 或 argon2
        
        Args:
            password: 明文密码
            
        Returns:
            哈希后的密码
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _ensure_test_account(self):
        """确保默认测试账号存在
        
        默认测试账号：
        - 邮箱：test@example.com
        - 密码：123456
        - 用途：方便测试和演示
        """
        test_email = "test@example.com"
        test_password = "123456"
        
        if test_email not in self.users:
            # 生成用户专属的 collection_name
            collection_name = f"user_{hashlib.md5(test_email.encode()).hexdigest()[:8]}"
            
            self.users[test_email] = {
                "password_hash": self._hash_password(test_password),
                "collection_name": collection_name,
                "created_at": datetime.now().isoformat(),
                "is_test_account": True,  # 标记为测试账号
                "active_session_id": None,  # 当前活跃会话ID
                "sessions": [],  # 会话列表
                "github_token": ""  # 用户的 GitHub Token（每个用户独立）
            }
            
            self._save()
            logger.info(f"已创建默认测试账号: {test_email}, collection: {collection_name}")
        else:
            # 为旧账号添加新字段（向后兼容）
            updated = False
            if "sessions" not in self.users[test_email]:
                self.users[test_email]["sessions"] = []
                self.users[test_email]["active_session_id"] = None
                updated = True
            if "github_token" not in self.users[test_email]:
                self.users[test_email]["github_token"] = ""
                updated = True
            if updated:
                self._save()
            logger.debug(f"默认测试账号已存在: {test_email}")
    
    def register(self, email: str, password: str) -> bool:
        """注册新用户
        
        Args:
            email: 用户邮箱
            password: 密码
            
        Returns:
            True: 注册成功
            False: 邮箱已存在
        """
        if email in self.users:
            logger.warning(f"注册失败：邮箱已存在 {email}")
            return False
        
        # 生成用户专属的 collection_name
        collection_name = f"user_{hashlib.md5(email.encode()).hexdigest()[:8]}"
        
        self.users[email] = {
            "password_hash": self._hash_password(password),
            "collection_name": collection_name,
            "created_at": datetime.now().isoformat(),
            "active_session_id": None,
            "sessions": [],
            "github_token": ""  # 用户的 GitHub Token
        }
        
        self._save()
        logger.info(f"用户注册成功: {email}, collection: {collection_name}")
        return True
    
    def login(self, email: str, password: str) -> Optional[str]:
        """用户登录验证
        
        Args:
            email: 用户邮箱
            password: 密码
            
        Returns:
            collection_name: 登录成功，返回用户专属的集合名称
            None: 登录失败
        """
        if email not in self.users:
            logger.warning(f"登录失败：用户不存在 {email}")
            return None
        
        if self.users[email]["password_hash"] == self._hash_password(password):
            logger.info(f"用户登录成功: {email}")
            return self.users[email]["collection_name"]
        else:
            logger.warning(f"登录失败：密码错误 {email}")
            return None
    
    def get_user_count(self) -> int:
        """获取用户总数"""
        return len(self.users)
    
    def add_user_session(self, email: str, session_id: str):
        """关联用户和会话
        
        Args:
            email: 用户邮箱
            session_id: 会话ID
        """
        if email not in self.users:
            logger.warning(f"用户不存在: {email}")
            return
        
        # 确保会话字段存在（向后兼容）
        if "sessions" not in self.users[email]:
            self.users[email]["sessions"] = []
        
        # 添加到会话列表（避免重复）
        if session_id not in self.users[email]["sessions"]:
            self.users[email]["sessions"].append(session_id)
            logger.info(f"用户 {email} 添加会话: {session_id}")
        
        # 设置为活跃会话
        self.users[email]["active_session_id"] = session_id
        self._save()
    
    def get_user_sessions(self, email: str) -> list[str]:
        """获取用户的所有会话列表
        
        Args:
            email: 用户邮箱
            
        Returns:
            会话ID列表（从新到旧）
        """
        if email not in self.users:
            logger.warning(f"用户不存在: {email}")
            return []
        
        # 确保会话字段存在（向后兼容）
        if "sessions" not in self.users[email]:
            self.users[email]["sessions"] = []
            self._save()
        
        # 返回倒序列表（最新的在前面）
        return list(reversed(self.users[email]["sessions"]))
    
    def get_active_session(self, email: str) -> Optional[str]:
        """获取用户当前活跃的会话ID
        
        Args:
            email: 用户邮箱
            
        Returns:
            会话ID，如果没有活跃会话则返回None
        """
        if email not in self.users:
            logger.warning(f"用户不存在: {email}")
            return None
        
        # 确保字段存在（向后兼容）
        if "active_session_id" not in self.users[email]:
            self.users[email]["active_session_id"] = None
            self._save()
        
        return self.users[email].get("active_session_id")
    
    def set_active_session(self, email: str, session_id: Optional[str]):
        """设置用户当前活跃的会话
        
        Args:
            email: 用户邮箱
            session_id: 会话ID，None表示清除活跃会话
        """
        if email not in self.users:
            logger.warning(f"用户不存在: {email}")
            return
        
        self.users[email]["active_session_id"] = session_id
        self._save()
        logger.info(f"用户 {email} 设置活跃会话: {session_id}")
    
    def get_github_token(self, email: str) -> str:
        """获取用户的 GitHub Token
        
        Args:
            email: 用户邮箱
            
        Returns:
            用户的 GitHub Token，如果未设置则返回空字符串
        """
        if email not in self.users:
            return ""
        
        # 向后兼容：如果旧用户没有 github_token 字段
        if "github_token" not in self.users[email]:
            self.users[email]["github_token"] = ""
            self._save()
        
        return self.users[email].get("github_token", "")
    
    def set_github_token(self, email: str, token: str) -> bool:
        """设置用户的 GitHub Token
        
        Args:
            email: 用户邮箱
            token: GitHub Token
            
        Returns:
            True: 设置成功
            False: 用户不存在
        """
        if email not in self.users:
            logger.warning(f"用户不存在: {email}")
            return False
        
        self.users[email]["github_token"] = token
        self._save()
        logger.info(f"用户 {email} 的 GitHub Token 已更新")
        return True
    
    def _save(self):
        """保存用户数据到文件"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
            logger.debug(f"用户数据已保存: {self.users_file}")
        except Exception as e:
            logger.error(f"保存用户数据失败: {e}")


if __name__ == "__main__":
    # 测试用户管理
    import tempfile
    import sys
    
    # 添加项目根目录到 path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    test_file = Path(tempfile.gettempdir()) / "test_users.json"
    um = UserManager(users_file=test_file)
    
    print("=== 测试用户管理 ===")
    
    # 测试注册
    print("\n1. 测试注册")
    result = um.register("test@example.com", "password123")
    print(f"   注册结果: {result}")
    
    # 重复注册
    print("\n2. 测试重复注册")
    result = um.register("test@example.com", "password456")
    print(f"   重复注册结果: {result} (应该为 False)")
    
    # 测试登录
    print("\n3. 测试登录（正确密码）")
    collection = um.login("test@example.com", "password123")
    print(f"   登录成功，collection: {collection}")
    
    # 错误密码
    print("\n4. 测试登录（错误密码）")
    collection = um.login("test@example.com", "wrongpassword")
    print(f"   登录结果: {collection} (应该为 None)")
    
    # 不存在的用户
    print("\n5. 测试登录（不存在的用户）")
    collection = um.login("nonexist@example.com", "password")
    print(f"   登录结果: {collection} (应该为 None)")
    
    print(f"\n✅ 测试完成！用户数据文件: {test_file}")

