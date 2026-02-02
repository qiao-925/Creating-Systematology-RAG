"""
对话管理模块：统一的对话管理接口

主要功能：
- ChatTurn类：单轮对话数据模型
- ChatSession类：对话会话数据模型，支持文件持久化
- ChatManager类：对话管理器，管理对话会话和历史
- 工具函数：会话文件读写和元数据查询

执行流程：
1. 创建对话会话
2. 添加对话轮次
3. 保存/加载会话文件

特性：
- 会话管理（支持文件持久化）
- 推理链支持
"""

from backend.business.chat.session import ChatTurn, ChatSession
from backend.business.chat.manager import ChatManager

__all__ = [
    'ChatTurn',
    'ChatSession',
    'ChatManager',
]

