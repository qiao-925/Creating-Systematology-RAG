"""
引用来源显示组件
在消息下方显示引用来源
使用 on_click 回调优化，避免不必要的 st.rerun()

主要功能：
- display_sources_below_message()：在消息下方显示引用来源
"""

import streamlit as st
from typing import List, Optional, Dict, Any


def _create_view_file_callback(dialog_key: str, file_path: str):
    """创建查看文件按钮的回调"""
    def callback():
        # 分离“是否打开弹窗”与“文件路径”，避免空路径时按钮失效
        st.session_state[f"show_file_{dialog_key}"] = True
        st.session_state[f"show_file_path_{dialog_key}"] = file_path
    return callback


def display_sources_below_message(sources: List[Dict[str, Any]], message_id: Optional[str] = None) -> None:
    """在消息下方显示引用来源（精简无边框样式）
    
    格式：
    [1] 文档标题.md                         📖
        预览内容前200字...
    
    Args:
        sources: 引用来源列表
        message_id: 消息唯一ID（用于生成锚点）
    """
    from frontend.components.file_viewer import show_file_viewer_dialog
    from frontend.utils.helpers import generate_default_message_id
    from frontend.utils.sources import extract_file_info
    
    if not message_id:
        message_id = generate_default_message_id()
    
    if not sources:
        return
    
    # 记录需要打开的对话框
    dialog_to_open = None
    
    # 渲染来源列表
    for idx, source in enumerate(sources):
        citation_num = source.get('index', idx + 1)
        dialog_key = f"file_viewer_below_{message_id}_{idx}_{citation_num}"
        file_path, title = extract_file_info(source)
        text = source.get('text', '')
        preview = text[:200] + "..." if len(text) > 200 else text
        
        # 紧凑布局：标题 + 小图标按钮
        col1, col2 = st.columns([10, 1])
        with col1:
            st.markdown(
                f'<span class="source-title">[{citation_num}] {title}</span>',
                unsafe_allow_html=True
            )
        with col2:
            st.button(
                "📖",
                key=dialog_key,
                help="查看完整内容",
                on_click=_create_view_file_callback(dialog_key, file_path)
            )
        
        # 预览内容（浅色小字）
        st.markdown(
            f'<p class="source-preview">{preview}</p>',
            unsafe_allow_html=True
        )
        
        # 检查是否需要打开对话框
        if dialog_to_open is None and st.session_state.get(f"show_file_{dialog_key}", False):
            dialog_to_open = (dialog_key, st.session_state.get(f"show_file_path_{dialog_key}", ""))
    
    # 打开对话框（如果有）
    if dialog_to_open:
        dialog_key, file_path = dialog_to_open
        show_file_viewer_dialog(file_path)
        # 每次触发后立即复位，防止弹窗在后续 rerun 中反复自动打开
        st.session_state[f"show_file_{dialog_key}"] = False
        st.session_state[f"show_file_path_{dialog_key}"] = None
        if st.session_state.get(f"close_file_{dialog_key}", False):
            st.session_state[f"close_file_{dialog_key}"] = False
