"""
UI组件模块 - 向后兼容层：保持向后兼容的接口导出

主要功能：
- init_session_state()：初始化Streamlit会话状态
- 加载函数：preload_embedding_model()、load_rag_service()、load_index()、load_chat_manager()等
- 来源显示：format_answer_with_citation_links()、display_sources_with_anchors()等
- 历史管理：display_model_status()、display_session_history()等

执行流程：
1. 初始化会话状态
2. 加载模型和服务
3. 显示UI组件
4. 处理用户交互

特性：
- Streamlit UI组件
- 会话状态管理
- 模型和服务加载
- 来源和历史显示
"""

from .session import init_session_state
from .loading import (
    preload_embedding_model,
    load_rag_service,
    load_index,
    load_chat_manager,
    load_hybrid_query_engine,
)
from .sources import (
    format_answer_with_citation_links,
    display_sources_with_anchors,
    get_file_viewer_url
)
from .sources_panel import (
    display_sources_right_panel,
    display_hybrid_sources
)
from .history import (
    display_model_status,
    group_sessions_by_time,
    display_session_history
)
from .chat_input import deepseek_style_chat_input

__all__ = [
    'init_session_state',
    'preload_embedding_model',
    'load_rag_service',
    'load_index',
    'load_chat_manager',
    'load_hybrid_query_engine',
    'format_answer_with_citation_links',
    'display_sources_with_anchors',
    'get_file_viewer_url',
    'display_sources_right_panel',
    'display_hybrid_sources',
    'display_model_status',
    'group_sessions_by_time',
    'display_session_history',
    'deepseek_style_chat_input',
]

