"""
UI组件模块 - 向后兼容层（已废弃）
此文件仅用于向后兼容，新代码请使用 src.ui 模块

主要功能：
- 从 src.ui 重新导出所有函数，保持向后兼容
"""

# 从新模块导入并重新导出
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
