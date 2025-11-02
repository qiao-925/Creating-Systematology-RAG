"""
多轮对话管理模块 - 向后兼容层
已模块化拆分，此文件保持向后兼容
"""

from src.chat import (
    ChatTurn,
    ChatSession,
    ChatManager,
    get_user_sessions_metadata,
    load_session_from_file,
)

__all__ = [
    'ChatTurn',
    'ChatSession',
    'ChatManager',
    'get_user_sessions_metadata',
    'load_session_from_file',
]

