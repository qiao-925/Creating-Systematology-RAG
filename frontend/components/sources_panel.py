"""
引用来源右侧面板显示组件
在右侧面板显示引用来源

主要功能：
- display_sources_right_panel()：在右侧面板显示引用来源
- display_sources_below_message()：在消息下方显示引用来源
- display_hybrid_sources()：显示混合检索的引用来源（兼容函数）
"""

import streamlit as st
import uuid
import urllib.parse
from pathlib import Path
from typing import List, Optional, Any, Dict


def display_sources_right_panel(sources: List[Dict[str, Any]], message_id: Optional[str] = None, container: Optional[Any] = None) -> None:
    """在右侧面板显示引用来源（固定位置，每个来源都有唯一的锚点ID）
    
    Args:
        sources: 引用来源列表
        message_id: 消息唯一ID（用于生成锚点）
        container: Streamlit容器对象（如column），如果为None则使用当前上下文
    """
    # 导入文件查看器对话框
    from frontend.components.file_viewer import show_file_viewer_dialog
    
    if not message_id:
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
    
    if not sources:
        st.info("💡 暂无引用来源")
        return
    
    # 直接使用当前上下文，不额外嵌套容器
    for idx, source in enumerate(sources):
            citation_num = source.get('index', idx + 1)  # 如果没有index，使用循环索引+1
            citation_id = f"citation_{message_id}_{citation_num}"
            
            # 获取文件路径和标题
            metadata = source.get('metadata', {})
            file_path = (
                metadata.get('file_path') or 
                metadata.get('file_name') or 
                metadata.get('source') or 
                metadata.get('url') or
                metadata.get('filename') or
                source.get('file_name') or  # 也检查source顶层
                ''
            )
            
            # 获取页码信息
            page_number = (
                source.get('page_number') or
                metadata.get('page_number') or
                metadata.get('page') or
                None
            )
            
            title = (
                metadata.get('title') or 
                metadata.get('file_name') or 
                metadata.get('filename') or
                source.get('file_name') or
                Path(file_path).name if file_path else 'Unknown'
            )
            
            if '/' in title or '\\' in title:
                title = Path(title).name if title else 'Unknown'
            
            # 判断是否为PDF文件
            is_pdf = file_path.lower().endswith('.pdf') if file_path else False
            
            # 使用卡片样式显示
            st.markdown(
                f'<div id="{citation_id}" style="'
                f'padding: 1rem; '
                f'margin-bottom: 1rem; '
                f'border: 1px solid var(--color-border); '
                f'border-radius: 8px; '
                f'background-color: var(--color-bg-card); '
                f'">',
                unsafe_allow_html=True
            )
            
            # 显示文件信息（如果有文件路径）
            if file_path:
                # 文件信息区域
                file_info_col1, file_info_col2 = st.columns([3, 1])
                with file_info_col1:
                    st.markdown(
                        f'<div style="margin-bottom: 0.75rem; padding: 0.5rem; background-color: var(--color-bg-secondary); border-radius: 4px;">'
                        f'<div style="font-weight: 600; font-size: 0.95rem; color: var(--color-accent); margin-bottom: 0.25rem;">'
                        f'📄 来源文件: {title}'
                        f'</div>'
                        f'{"<div style=\"font-size: 0.85rem; color: var(--color-text-secondary);\">📑 页码: " + str(page_number) + "</div>" if page_number else ""}'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                with file_info_col2:
                    # 使用按钮触发弹窗
                    dialog_key = f"file_viewer_{message_id}_{citation_num}"
                    if st.button("📖 查看文件", key=dialog_key, use_container_width=True):
                        st.session_state[f"show_file_{dialog_key}"] = file_path
            
            # 显示引用编号和相似度
            metadata_parts = []
            metadata_parts.append(f"引用 [{citation_num}]")
            if source.get('score') is not None:
                metadata_parts.append(f"相似度: {source['score']:.2f}")
            
            if metadata_parts:
                st.caption(" | ".join(metadata_parts))
            
            # 显示文本块内容（被引用的具体文本）
            st.markdown("**📝 引用文本块:**", unsafe_allow_html=True)
            text = source.get('text', '')
            if len(text) > 300:
                with st.expander("查看完整内容", expanded=False):
                    st.text(text)
                st.text(text[:300] + "...")
            else:
                st.text(text)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            if source != sources[-1]:
                st.divider()
    
    # 在循环外部统一处理对话框打开（确保同一时间只打开一个对话框）
    # 遍历所有可能的对话框键，只打开第一个需要打开的对话框
    for idx, source in enumerate(sources):
        citation_num = source.get('index', idx + 1)
        dialog_key = f"file_viewer_{message_id}_{citation_num}"
        
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


def display_sources_below_message(sources: List[Dict[str, Any]], message_id: Optional[str] = None) -> None:
    """在消息下方显示引用来源（简化版，用于消息下方显示）
    
    Args:
        sources: 引用来源列表
        message_id: 消息唯一ID（用于生成锚点）
    """
    # 导入文件查看器对话框
    from frontend.components.file_viewer import show_file_viewer_dialog
    
    if not message_id:
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
    
    if not sources:
        return
    
    # 使用更紧凑的样式显示在消息下方
    for idx, source in enumerate(sources):
        citation_num = source.get('index', idx + 1)
        citation_id = f"citation_{message_id}_{citation_num}"
        
        # 获取文件路径和标题
        metadata = source.get('metadata', {})
        file_path = (
            metadata.get('file_path') or 
            metadata.get('file_name') or 
            metadata.get('source') or 
            metadata.get('url') or
            metadata.get('filename') or
            source.get('file_name') or
            ''
        )
        
        title = (
            metadata.get('title') or 
            metadata.get('file_name') or 
            metadata.get('filename') or
            source.get('file_name') or
            Path(file_path).name if file_path else 'Unknown'
        )
        
        if '/' in title or '\\' in title:
            title = Path(title).name if title else 'Unknown'
        
        # 使用卡片样式显示（紧凑版）
        with st.container():
            st.markdown(
                f'<div id="{citation_id}" style="'
                f'padding: 0.75rem; '
                f'margin: 0.5rem 0; '
                f'border: 1px solid var(--color-border); '
                f'border-radius: 6px; '
                f'background-color: var(--color-bg-card); '
                f'">',
                unsafe_allow_html=True
            )
            
            # 显示标题和查看按钮
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(
                    f'<div style="margin-bottom: 0.5rem;"><strong style="color: var(--color-accent);">[{citation_num}]</strong> {title}</div>',
                    unsafe_allow_html=True
                )
            with col2:
                # 使用按钮触发弹窗
                dialog_key = f"file_viewer_below_{message_id}_{citation_num}"
                if st.button("📖 查看", key=dialog_key, use_container_width=True):
                    st.session_state[f"show_file_{dialog_key}"] = file_path
            
            # 显示文本内容（限制长度）
            text = source.get('text', '')
            if len(text) > 200:
                with st.expander(f"查看完整内容", expanded=False):
                    st.text(text)
                st.caption(text[:200] + "...")
            else:
                st.caption(text)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
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


def display_hybrid_sources(sources: List[Dict[str, Any]], message_id: Optional[str] = None, container: Optional[Any] = None) -> None:
    """显示混合检索的引用来源（兼容函数，功能同 display_sources_right_panel）
    
    Args:
        sources: 引用来源列表
        message_id: 消息唯一ID（用于生成锚点）
        container: Streamlit容器对象（如column），如果为None则使用当前上下文
    """
    display_sources_right_panel(sources, message_id, container)

