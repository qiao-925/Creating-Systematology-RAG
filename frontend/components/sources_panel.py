"""
引用来源显示组件
在消息下方显示引用来源

主要功能：
- display_sources_below_message()：在消息下方显示引用来源
"""

import streamlit as st
from pathlib import Path
from typing import List, Optional, Dict, Any


def display_sources_below_message(sources: List[Dict[str, Any]], message_id: Optional[str] = None) -> None:
    """在消息下方显示引用来源（使用原生组件）
    
    Args:
        sources: 引用来源列表
        message_id: 消息唯一ID（用于生成锚点）
    """
    # 导入文件查看器对话框
    from frontend.components.file_viewer import show_file_viewer_dialog
    from frontend.utils.helpers import generate_default_message_id
    
    if not message_id:
        message_id = generate_default_message_id()
    
    if not sources:
        return
    
    # 使用原生组件显示引用来源
    for idx, source in enumerate(sources):
        citation_num = source.get('index', idx + 1)
        citation_id = f"citation_{message_id}_{citation_num}"
        
        # 获取文件路径和标题
        from frontend.utils.sources import extract_file_info
        file_path, title = extract_file_info(source)
        
        # 使用容器和原生组件显示
        with st.container():
            # 显示标题和查看按钮
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**[{citation_num}]** {title}")
            with col2:
                # 使用按钮触发弹窗
                dialog_key = f"file_viewer_below_{message_id}_{citation_num}"
                if st.button("📖 查看", key=dialog_key, use_container_width=True):
                    st.session_state[f"show_file_{dialog_key}"] = file_path
            
            # 显示文本内容（限制长度）
            text = source.get('text', '')
            if len(text) > 200:
                with st.expander(f"查看完整内容 ({len(text)} 字符)", expanded=False):
                    st.text(text)
                st.caption(text[:200] + "...")
            else:
                st.caption(text)
    
    # 在循环外部统一处理对话框打开（确保同一时间只打开一个对话框）
    # 遍历所有可能的对话框键，只打开第一个需要打开的对话框
    for idx, source in enumerate(sources):
        citation_num = source.get('index', idx + 1)
        dialog_key = f"file_viewer_below_{message_id}_{citation_num}"
        
        # 检查是否需要显示弹窗
        if st.session_state.get(f"show_file_{dialog_key}"):
            show_file_viewer_dialog(st.session_state[f"show_file_{dialog_key}"])
            # 检查是否需要关闭弹窗
            if st.session_state.get(f"close_file_{dialog_key}", False):
                st.session_state[f"show_file_{dialog_key}"] = None
                st.session_state[f"close_file_{dialog_key}"] = False
                st.rerun()
            # 只打开第一个对话框，避免同时打开多个
            break
