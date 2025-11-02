"""
对话管理模块 - 向后兼容层
保持向后兼容的接口导出
"""

from src.chat.session import ChatTurn, ChatSession
from src.chat.manager import ChatManager
from src.chat.utils import get_user_sessions_metadata, load_session_from_file

__all__ = [
    'ChatTurn',
    'ChatSession',
    'ChatManager',
    'get_user_sessions_metadata',
    'load_session_from_file',
]

