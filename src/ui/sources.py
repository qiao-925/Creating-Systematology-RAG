"""
UI组件 - 引用来源显示模块
格式化答案引用和显示引用来源
"""

import streamlit as st
import re
import uuid
import urllib.parse
from pathlib import Path
from typing import List

from src.logger import setup_logger

logger = setup_logger('ui_components')


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
        URL字符串
    """
    # 对文件路径进行URL编码
    encoded_path = urllib.parse.quote(str(file_path), safe='')
    
    # 页面名称：Streamlit pages 目录下的文件名（不含.py）
    page_name = "2_📄_文件查看"
    
    return f"/{page_name}?path={encoded_path}"


def display_sources_with_anchors(sources: list, message_id: str = None, expanded: bool = True):
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
            for source in sources:
                citation_num = source.get('index', 0)
                citation_id = f"citation_{message_id}_{citation_num}"
                
                # 获取文件路径和标题
                metadata = source.get('metadata', {})
                file_path = (
                    metadata.get('file_path') or 
                    metadata.get('file_name') or 
                    metadata.get('source') or 
                    metadata.get('url') or
                    metadata.get('filename') or
                    ''
                )
                
                title = (
                    metadata.get('title') or 
                    metadata.get('file_name') or 
                    metadata.get('filename') or
                    'Unknown'
                )
                
                if '/' in title or '\\' in title:
                    title = Path(title).name if title else 'Unknown'
                
                file_url = None
                if file_path:
                    file_url = get_file_viewer_url(file_path)
                
                # 构建标题HTML
                if file_url:
                    page_name = "2_📄_文件查看"
                    encoded_path = urllib.parse.quote(str(file_path), safe='')
                    full_url = f"/{page_name}?path={encoded_path}"
                    title_html = (
                        f'<div id="{citation_id}" style="padding-top: 0.5rem; padding-bottom: 0.5rem;">'
                        f'<strong>'
                        f'<a href="{full_url}" '
                        f'style="color: var(--color-accent); text-decoration: underline; font-weight: 600; cursor: pointer;" '
                        f'title="点击查看完整文件">'
                        f'[{citation_num}] {title} 🔗'
                        f'</a>'
                        f'</strong>'
                    )
                    st.markdown(title_html, unsafe_allow_html=True)
                else:
                    st.markdown(f'<div id="{citation_id}"><strong>[{citation_num}] {title}</strong></div>', unsafe_allow_html=True)
                
                # 显示元数据
                metadata_parts = []
                if source['score'] is not None:
                    metadata_parts.append(f"相似度: {source['score']:.2f}")
                if 'file_name' in source['metadata']:
                    metadata_parts.append(f"📁 {source['metadata']['file_name']}")
                
                if metadata_parts:
                    st.caption(" | ".join(metadata_parts))
                
                # 显示文本内容
                text = source['text']
                if len(text) > 300:
                    with st.expander("查看完整内容", expanded=False):
                        st.text(text)
                    st.text(text[:300] + "...")
                else:
                    st.text(text)
                
                if source != sources[-1]:
                    st.divider()

