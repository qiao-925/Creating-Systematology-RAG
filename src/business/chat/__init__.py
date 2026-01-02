"""
对话管理模块：统一的对话管理接口

主要功能：
- ChatTurn类：单轮对话数据模型
- ChatSession类：对话会话数据模型
- ChatManager类：对话管理器，管理对话会话和历史
- get_user_sessions_metadata()：获取用户会话元数据
- load_session_from_file()：从文件加载会话

执行流程：
1. 创建对话会话
2. 添加对话轮次
3. 保存会话历史
4. 加载历史会话

特性：
- 会话管理
- 历史记录持久化
- 推理链支持
"""

from src.business.chat.session import ChatTurn, ChatSession
from src.business.chat.manager import ChatManager
from src.business.chat.utils import (
    get_user_sessions_metadata,
    get_user_sessions_metadata_lazy,
    load_session_from_file
)

__all__ = [
    'ChatTurn',
    'ChatSession',
    'ChatManager',
    'get_user_sessions_metadata',
    'get_user_sessions_metadata_lazy',
    'load_session_from_file',
]

