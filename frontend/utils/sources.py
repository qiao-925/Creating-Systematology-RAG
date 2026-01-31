"""
来源处理工具模块
格式化答案引用和显示引用来源

主要功能：
- convert_sources_to_dict()：将SourceModel对象列表转换为字典列表
- inject_citation_script()：返回引用跳转用全局 script，供 chat_display 注入一次
- format_answer_with_citation_links()：将答案中的引用标签转换为可点击的超链接

注意：文件查看功能已迁移到弹窗实现，不再使用URL跳转
"""

import streamlit as st
import re
from pathlib import Path
from typing import List, Dict, Any, Union, Optional

from backend.infrastructure.logger import get_logger

logger = get_logger('frontend.sources')


def extract_file_info(source: Dict[str, Any]) -> tuple[str, str]:
    """从source中提取文件路径和标题
    
    Args:
        source: 来源字典
        
    Returns:
        (file_path, title) 元组
    """
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
    
    return file_path, title


def convert_sources_to_dict(sources: Union[List[Dict[str, Any]], List[Any]]) -> List[Dict[str, Any]]:
    """将SourceModel对象列表转换为字典列表
    
    Args:
        sources: SourceModel对象列表或字典列表
        
    Returns:
        字典列表
    """
    if not sources:
        return []
    
    result = []
    for idx, source in enumerate(sources):
        if isinstance(source, dict):
            # 已经是字典，添加index字段
            source_dict = source.copy()
            source_dict['index'] = idx + 1
            result.append(source_dict)
        else:
            # 是SourceModel对象，转换为字典
            source_dict = source.model_dump() if hasattr(source, 'model_dump') else dict(source)
            source_dict['index'] = idx + 1
            result.append(source_dict)
    
    return result


def inject_citation_script() -> str:
    """返回用于引用跳转的全局 script（仅注入一次，供 chat_display 使用）"""
    return """
    <script>
    function scrollToCitation(citationId) {
        const rootStyle = getComputedStyle(document.documentElement);
        const primaryColor = rootStyle.getPropertyValue('--primary-color').trim() || '#2563EB';
        const highlightColor = 'rgba(245, 158, 11, 0.35)';
        const element = document.getElementById(citationId);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth', block: 'center' });
            element.style.backgroundColor = highlightColor;
            element.style.border = '2px solid ' + primaryColor;
            setTimeout(() => {
                element.style.backgroundColor = '';
                element.style.border = '';
            }, 2000);
        } else {
            setTimeout(() => {
                const targetElement = document.getElementById(citationId);
                if (targetElement) {
                    targetElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    targetElement.style.backgroundColor = highlightColor;
                    targetElement.style.border = '2px solid ' + primaryColor;
                    setTimeout(() => {
                        targetElement.style.backgroundColor = '';
                        targetElement.style.border = '';
                    }, 2000);
                }
            }, 100);
        }
    }
    </script>
    """


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
        from frontend.utils.helpers import generate_default_message_id
        message_id = generate_default_message_id()
    
    # 提取所有引用标签 [1], [2], [3] 等
    citation_pattern = r'\[(\d+)\]'
    
    def replace_citation(match):
        citation_num = int(match.group(1))
        citation_id = f"citation_{message_id}_{citation_num}"
        
        # 检查该引用是否存在
        if citation_num <= len(sources):
            # 使用 CSS 类而不是内联样式，让 CSS 变量自动适配主题
            return f'<a href="#{citation_id}" onclick="event.preventDefault(); scrollToCitation(\'{citation_id}\'); return false;" class="citation-link" title="点击查看引用来源 {citation_num}">[{citation_num}]</a>'
        else:
            return match.group(0)
    
    # 替换所有引用标签
    formatted_answer = re.sub(citation_pattern, replace_citation, answer)

    return formatted_answer


