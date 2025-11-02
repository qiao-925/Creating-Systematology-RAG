"""
UI组件 - 引用来源右侧面板显示模块
在右侧面板显示引用来源
"""

import streamlit as st
import uuid
import urllib.parse
from pathlib import Path
from typing import List, Optional

from src.ui.sources import get_file_viewer_url


def display_sources_right_panel(sources: list, message_id: str = None, container=None):
    """在右侧面板显示引用来源（固定位置，每个来源都有唯一的锚点ID）
    
    Args:
        sources: 引用来源列表
        message_id: 消息唯一ID（用于生成锚点）
        container: Streamlit容器对象（如column），如果为None则使用当前上下文
    """
    if not message_id:
        message_id = f"msg_{uuid.uuid4().hex[:8]}"
    
    if not sources:
        if container:
            with container:
                st.info("💡 暂无引用来源")
        else:
            st.info("💡 暂无引用来源")
        return
    
    # 使用传入的container或当前上下文
    context = container if container else st
    
    with context:
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
                    f'<a href="{full_url}" '
                    f'style="color: var(--color-accent); text-decoration: underline; font-weight: 600; cursor: pointer;" '
                    f'title="点击查看完整文件">'
                    f'[{citation_num}] {title} 🔗'
                    f'</a>'
                )
            else:
                title_html = f'<span style="font-weight: 600; font-size: 1rem; color: var(--color-accent);">[{citation_num}] {title}</span>'
            
            # 使用卡片样式显示
            st.markdown(
                f'<div id="{citation_id}" style="'
                f'padding: 1rem; '
                f'margin-bottom: 1rem; '
                f'border: 1px solid var(--color-border); '
                f'border-radius: 8px; '
                f'background-color: var(--color-bg-card); '
                f'">'
                f'<div style="margin-bottom: 0.5rem;">'
                f'{title_html}'
                f'</div>',
                unsafe_allow_html=True
            )
            
            # 显示元数据
            metadata_parts = []
            if source['score'] is not None:
                metadata_parts.append(f"相似度: {source['score']:.2f}")
            if 'file_name' in source['metadata']:
                metadata_parts.append(f"📁 {source['metadata']['file_name']}")
            
            if metadata_parts:
                st.caption(" | ".join(metadata_parts))
            
            # 显示文本内容（限制长度，可展开）
            text = source['text']
            if len(text) > 300:
                with st.expander("查看完整内容", expanded=False):
                    st.text(text)
                st.text(text[:300] + "...")
            else:
                st.text(text)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            if source != sources[-1]:
                st.divider()


def display_hybrid_sources(local_sources, wikipedia_sources):
    """分区展示混合查询的来源
    
    Args:
        local_sources: 本地知识库来源列表
        wikipedia_sources: 维基百科来源列表
    """
    import urllib.parse
    
    # 本地知识库来源
    if local_sources:
        with st.expander(f"📚 本地知识库 ({len(local_sources)})", expanded=True):
            for i, source in enumerate(local_sources, 1):
                metadata = source.get('metadata', {})
                title = (
                    metadata.get('title') or 
                    metadata.get('file_name') or 
                    metadata.get('filename') or
                    'Unknown'
                )
                
                file_path = (
                    metadata.get('file_path') or 
                    metadata.get('file_name') or 
                    ''
                )
                
                if file_path:
                    file_url = get_file_viewer_url(file_path)
                    page_name = "2_📄_文件查看"
                    encoded_path = urllib.parse.quote(str(file_path), safe='')
                    full_url = f"/{page_name}?path={encoded_path}"
                    title_html = (
                        f'<strong>'
                        f'<a href="{full_url}" '
                        f'style="color: var(--color-accent); text-decoration: underline; font-weight: 600; cursor: pointer;" '
                        f'title="点击查看完整文件">'
                        f'[{i}] {title} 🔗'
                        f'</a>'
                        f'</strong>'
                    )
                    st.markdown(title_html, unsafe_allow_html=True)
                else:
                    st.markdown(f"**[{i}] {title}**")
                
                # 显示元数据
                metadata_parts = []
                if 'file_name' in source['metadata']:
                    metadata_parts.append(f"📁 {source['metadata']['file_name']}")
                if source.get('score') is not None:
                    metadata_parts.append(f"相似度: {source['score']:.2f}")
                if metadata_parts:
                    st.caption(" | ".join(metadata_parts))
                
                # 显示完整内容
                st.text(source['text'])
                
                if i < len(local_sources):
                    st.divider()
    
    # 维基百科来源
    if wikipedia_sources:
        with st.expander(f"🌐 维基百科补充 ({len(wikipedia_sources)})", expanded=False):
            for i, source in enumerate(wikipedia_sources, 1):
                title = source['metadata'].get('title', 'Unknown')
                st.markdown(f"**[W{i}] {title}**")
                
                # 显示维基百科链接和相似度
                wiki_url = source['metadata'].get('wikipedia_url', '#')
                metadata_parts = [f"🔗 [{wiki_url}]({wiki_url})"]
                if source.get('score') is not None:
                    metadata_parts.append(f"相似度: {source['score']:.2f}")
                st.caption(" | ".join(metadata_parts))
                
                # 显示完整内容
                st.text(source['text'])
                
                if i < len(wikipedia_sources):
                    st.divider()

