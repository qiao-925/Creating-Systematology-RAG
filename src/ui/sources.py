"""
UI组件 - 引用来源显示模块
格式化答案引用和显示引用来源
"""

import streamlit as st
import re
import uuid
import urllib.parse
from pathlib import Path
from typing import List, Optional, Any, Dict

from src.infrastructure.logger import get_logger
from .file_viewer import show_file_viewer_dialog

logger = get_logger('ui_components')


def format_answer_with_citation_links(answer: str, sources: list, message_id: str = None) -> str:
    """将答案中的引用标签[1][2][3]转换为可点击的超链接
    
    Args:
        answer: 包含引用标签的答案文本
        sources: 引用来源列表
        message_id: 消息唯一ID（用于生成锚点）
        
    Returns:
        处理后的HTML字符串（包含可点击的引用链接）
    """
    if not message_id:
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
    
    # 提取所有引用标签 [1], [2], [3] 等
    citation_pattern = r'\[(\d+)\]'
    
    def replace_citation(match):
        citation_num = int(match.group(1))
        citation_id = f"citation_{message_id}_{citation_num}"
        
        # 检查该引用是否存在
        if citation_num <= len(sources):
            return f'<a href="#{citation_id}" onclick="event.preventDefault(); scrollToCitation(\'{citation_id}\'); return false;" style="color: #2563EB; text-decoration: none; font-weight: 500; cursor: pointer;" title="点击查看引用来源 {citation_num}">[{citation_num}]</a>'
        else:
            return match.group(0)
    
    # 替换所有引用标签
    formatted_answer = re.sub(citation_pattern, replace_citation, answer)
    
    # 添加JavaScript代码用于滚动到右侧引用来源
    js_code = f"""
    <script>
    function scrollToCitation(citationId) {{
        const element = document.getElementById(citationId);
        if (element) {{
            element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
            element.style.backgroundColor = '#FFF9C4';
            element.style.border = '2px solid #2563EB';
            setTimeout(() => {{
                element.style.backgroundColor = '';
                element.style.border = '';
            }}, 2000);
        }} else {{
            setTimeout(() => {{
                const targetElement = document.getElementById(citationId);
                if (targetElement) {{
                    targetElement.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    targetElement.style.backgroundColor = '#FFF9C4';
                    targetElement.style.border = '2px solid #2563EB';
                    setTimeout(() => {{
                        targetElement.style.backgroundColor = '';
                        targetElement.style.border = '';
                    }}, 2000);
                }}
            }}, 100);
        }}
    }}
    </script>
    """
    
    return formatted_answer + js_code


def get_file_viewer_url(file_path: str) -> str:
    """生成文件查看页面的URL
    
    Args:
        file_path: 文件路径
        
    Returns:
        URL字符串（已编码，可直接用于 HTML 链接）
    """
    # 对文件路径进行URL编码
    encoded_path = urllib.parse.quote(str(file_path), safe='')
    
    # 页面名称：Streamlit pages 目录下的文件名（不含.py）
    # 对页面名称进行 URL 编码，确保中文字符正确传递
    page_name = "2_文件查看"
    encoded_page_name = urllib.parse.quote(page_name, safe='/')
    
    return f"/{encoded_page_name}?path={encoded_path}"


def display_sources_with_anchors(sources: List[Dict[str, Any]], message_id: Optional[str] = None, expanded: bool = True) -> None:
    """显示引用来源，每个来源都有唯一的锚点ID
    
    Args:
        sources: 引用来源列表
        message_id: 消息唯一ID（用于生成锚点）
        expanded: 是否默认展开
    """
    if not message_id:
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
    
    if sources:
        with st.expander("📚 查看引用来源", expanded=expanded):
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
                
                # 构建标题HTML（包含文件信息）
                title_html = f'<div id="{citation_id}" style="padding-top: 0.5rem; padding-bottom: 0.5rem;">'
                
                # 如果有文件路径，显示文件信息和查看按钮
                if file_path:
                    # 文件信息区域（使用列布局）
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        title_html += (
                            f'<div style="margin-bottom: 0.5rem; padding: 0.5rem; background-color: var(--color-bg-secondary); border-radius: 4px;">'
                            f'<div style="font-weight: 600; font-size: 0.95rem; color: var(--color-accent);">'
                            f'📄 来源文件: {title}'
                            f'</div>'
                        )
                        if page_number:
                            title_html += f'<div style="font-size: 0.85rem; color: var(--color-text-secondary);">📑 页码: {page_number}</div>'
                        title_html += f'</div>'
                        st.markdown(title_html, unsafe_allow_html=True)
                    with col2:
                        # 使用按钮触发弹窗
                        dialog_key = f"file_viewer_anchor_{message_id}_{citation_num}"
                        if st.button("📖 查看文件", key=dialog_key, use_container_width=True):
                            st.session_state[f"show_file_{dialog_key}"] = file_path
                else:
                    title_html += f'<strong>[{citation_num}]</strong></div>'
                    st.markdown(title_html, unsafe_allow_html=True)
                
                # 显示元数据
                metadata_parts = []
                if source.get('score') is not None:
                    metadata_parts.append(f"相似度: {source['score']:.2f}")
                
                if metadata_parts:
                    st.caption(" | ".join(metadata_parts))
                
                # 显示文本内容（被引用的具体文本）
                st.markdown("**📝 引用文本块:**", unsafe_allow_html=True)
                text = source.get('text', '')
                if len(text) > 300:
                    with st.expander("查看完整内容", expanded=False):
                        st.text(text)
                    st.text(text[:300] + "...")
                else:
                    st.text(text)
                
                if source != sources[-1]:
                    st.divider()
        
        # 在expander外部检查并显示弹窗（避免嵌套问题）
        for idx, source in enumerate(sources):
            citation_num = source.get('index', idx + 1)
            dialog_key = f"file_viewer_anchor_{message_id}_{citation_num}"
            if st.session_state.get(f"show_file_{dialog_key}"):
                show_file_viewer_dialog(st.session_state[f"show_file_{dialog_key}"])
                # 检查是否需要关闭弹窗
                if st.session_state.get(f"close_file_{dialog_key}", False):
                    st.session_state[f"show_file_{dialog_key}"] = None
                    st.session_state[f"close_file_{dialog_key}"] = False
                    st.rerun()

