"""
UI共用组件模块 - 向后兼容层
已模块化拆分，此文件保持向后兼容
"""

# 从新模块导入所有公开接口
from src.ui import (
    init_session_state,
    preload_embedding_model,
    load_rag_service,
    load_index,
    load_chat_manager,
    load_hybrid_query_engine,
    format_answer_with_citation_links,
    display_sources_with_anchors,
    get_file_viewer_url,
    display_sources_right_panel,
    display_hybrid_sources,
    display_model_status,
    group_sessions_by_time,
    display_session_history,
)

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
]
