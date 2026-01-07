"""
用户行为日志模块：记录用户的查询、会话活动等行为数据（单用户模式）

主要功能：
- ActivityLogger类：用户行为日志记录器
- log_query()：记录查询活动
- log_session()：记录会话活动

执行流程：
1. 创建日志记录
2. 保存到JSON文件
3. 按用户和日期组织（单用户模式使用default目录）

特性：
- 用户行为追踪
- JSON格式存储
- 按日期组织
- 完整的活动记录
- 单用户模式支持（user_email可选）
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger('activity_logger')


class ActivityLogger:
    """用户行为日志记录器（单用户模式）"""
    
    def __init__(self, user_email: Optional[str] = None):
        """初始化行为日志记录器
        
        Args:
            user_email: 用户邮箱（单用户模式下可忽略，使用默认路径）
        """
        # 单用户模式：使用默认路径
        self.user_email = user_email or "default"
        
        # 为每个用户创建独立的日志目录（单用户模式使用default）
        self.log_dir = config.ACTIVITY_LOG_PATH / self.user_email
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 日志文件路径（JSONL格式）
        self.log_file = self.log_dir / "activity.jsonl"
    
    def _log(self, action: str, **kwargs):
        """记录一条行为日志
        
        Args:
            action: 行为类型（login, logout, query, load_session等）
            **kwargs: 额外的日志数据
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": self.user_email,
            "action": action,
            **kwargs
        }
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            logger.debug(f"记录行为日志: {action} - {self.user_email}")
        except Exception as e:
            logger.error(f"记录行为日志失败: {e}")
    
    def log_login(self):
        """记录登录"""
        self._log("login")
    
    def log_logout(self):
        """记录登出"""
        self._log("logout")
    
    def log_query(self, session_id: str, query: str, sources_count: int, response_length: int):
        """记录查询
        
        Args:
            session_id: 会话ID
            query: 查询内容
            sources_count: 引用来源数量
            response_length: 回答长度（字符数）
        """
        self._log(
            "query",
            session_id=session_id,
            query=query,
            sources_count=sources_count,
            response_length=response_length
        )
    
    def log_new_session(self, session_id: str):
        """记录创建新会话
        
        Args:
            session_id: 会话ID
        """
        self._log("new_session", session_id=session_id)
    
    def log_load_session(self, session_id: str, turns_count: int):
        """记录加载历史会话
        
        Args:
            session_id: 会话ID
            turns_count: 对话轮数
        """
        self._log("load_session", session_id=session_id, turns_count=turns_count)
    
    def log_document_upload(self, file_count: int, source_type: str):
        """记录文档上传
        
        Args:
            file_count: 文件数量
            source_type: 来源类型（upload, url, github）
        """
        self._log("document_upload", file_count=file_count, source_type=source_type)
    
    def log_index_clear(self):
        """记录清空索引"""
        self._log("index_clear")
    
    def get_recent_activities(self, limit: int = 50) -> list[Dict[str, Any]]:
        """获取最近的活动记录
        
        Args:
            limit: 返回记录数量
            
        Returns:
            活动记录列表（从新到旧）
        """
        if not self.log_file.exists():
            return []
        
        try:
            activities = []
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        activities.append(json.loads(line))
            
            # 返回最近的N条记录（倒序）
            return activities[-limit:][::-1]
        except Exception as e:
            logger.error(f"读取行为日志失败: {e}")
            return []
    
    def get_query_count(self, days: int = 7) -> int:
        """获取最近N天的查询次数
        
        Args:
            days: 天数
            
        Returns:
            查询次数
        """
        from datetime import timedelta
        
        if not self.log_file.exists():
            return 0
        
        cutoff_time = datetime.now() - timedelta(days=days)
        count = 0
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        if entry.get('action') == 'query':
                            timestamp = datetime.fromisoformat(entry['timestamp'])
                            if timestamp >= cutoff_time:
                                count += 1
            return count
        except Exception as e:
            logger.error(f"统计查询次数失败: {e}")
            return 0


if __name__ == "__main__":
    # 测试用户行为日志
    import tempfile
    import sys
    from pathlib import Path
    
    # 添加项目根目录到 path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    # 重新导入以确保路径正确
    from backend.infrastructure.config import config as cfg
    
    # 临时配置
    cfg.ACTIVITY_LOG_PATH = Path(tempfile.gettempdir()) / "test_activity_logs"
    config = cfg
    
    print("=== 测试用户行为日志 ===\n")
    
    # 创建日志记录器
    activity_logger = ActivityLogger("test@example.com")
    
    # 测试各种日志记录
    print("1. 记录登录")
    activity_logger.log_login()
    
    print("2. 记录创建新会话")
    activity_logger.log_new_session("session_001")
    
    print("3. 记录查询")
    activity_logger.log_query("session_001", "什么是系统科学？", 3, 150)
    activity_logger.log_query("session_001", "钱学森的贡献", 2, 200)
    
    print("4. 记录文档上传")
    activity_logger.log_document_upload(5, "upload")
    
    print("5. 记录加载历史会话")
    activity_logger.log_load_session("session_002", 8)
    
    print("6. 记录登出")
    activity_logger.log_logout()
    
    # 读取最近的活动
    print("\n7. 获取最近的活动记录")
    recent = activity_logger.get_recent_activities(limit=10)
    for i, activity in enumerate(recent, 1):
        print(f"   {i}. {activity['timestamp'][:19]} - {activity['action']}")
    
    # 统计查询次数
    print("\n8. 统计最近7天的查询次数")
    count = activity_logger.get_query_count(days=7)
    print(f"   查询次数: {count}")
    
    print(f"\n✅ 测试完成！日志文件: {activity_logger.log_file}")

