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
        st.session_state[f"show_file_{dialog_key}"] = file_path
    return callback


def display_sources_below_message(sources: List[Dict[str, Any]], message_id: Optional[str] = None) -> None:
    """在消息下方显示引用来源（使用原生组件）
    
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
    
    # 记录需要打开的对话框（只打开第一个）
    dialog_to_open = None
    
    # 单次遍历：显示来源并检查对话框状态
    for idx, source in enumerate(sources):
        citation_num = source.get('index', idx + 1)
        dialog_key = f"file_viewer_below_{message_id}_{citation_num}"
        file_path, title = extract_file_info(source)
        
        # 显示来源
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**[{citation_num}]** {title}")
            with col2:
                # 使用 on_click 回调
                st.button(
                    "📖 查看", 
                    key=dialog_key, 
                    use_container_width=True,
                    on_click=_create_view_file_callback(dialog_key, file_path)
                )
            
            text = source.get('text', '')
            if len(text) > 200:
                with st.expander(f"查看完整内容 ({len(text)} 字符)", expanded=False):
                    st.text(text)
                st.caption(text[:200] + "...")
            else:
                st.caption(text)
        
        # 检查是否需要打开对话框（只记录第一个）
        if dialog_to_open is None and st.session_state.get(f"show_file_{dialog_key}"):
            dialog_to_open = (dialog_key, st.session_state[f"show_file_{dialog_key}"])
    
    # 打开对话框（如果有）
    if dialog_to_open:
        dialog_key, file_path = dialog_to_open
        show_file_viewer_dialog(file_path)
        # 对话框关闭后清理状态（不需要 rerun，对话框组件会自动处理）
        if st.session_state.get(f"close_file_{dialog_key}", False):
            st.session_state[f"show_file_{dialog_key}"] = None
            st.session_state[f"close_file_{dialog_key}"] = False
