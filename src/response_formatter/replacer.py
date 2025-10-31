"""
引用替换器
将文本中的引用标记转换为可点击的链接
"""

import re
from typing import List, Dict, Optional


class CitationReplacer:
    """引用替换器"""
    
    def replace_citations(self, text: str, sources: Optional[List[Dict]] = None) -> str:
        """将文本中的 [1] 格式替换为可点击链接
        
        Args:
            text: 待处理的文本
            sources: 引用来源列表
            
        Returns:
            str: 替换后的文本
        """
        if not text or not sources:
            return text
        
        # 匹配 [数字] 格式
        pattern = r'\[(\d+)\]'
        
        def replace_func(match):
            num = int(match.group(1))
            if 1 <= num <= len(sources):
                # 生成可点击链接（Markdown 格式）
                return f"[{num}](#citation_{num})"
            return match.group(0)
        
        return re.sub(pattern, replace_func, text)
    
    def add_citation_anchors(self, sources: List[Dict]) -> str:
        """生成引用来源的锚点标记
        
        Args:
            sources: 引用来源列表
            
        Returns:
            str: Markdown 格式的引用来源列表
        """
        if not sources:
            return ""
        
        lines = ["\n\n---\n\n## 📚 参考来源\n"]
        
        for source in sources:
            idx = source.get('index', 0)
            metadata = source.get('metadata', {})
            score = source.get('score')
            
            # 提取文件信息
            file_path = (
                metadata.get('file_path') or
                metadata.get('file_name') or
                metadata.get('source') or
                metadata.get('url') or
                '未知来源'
            )
            file_name = file_path.split('/')[-1] if '/' in file_path else file_path.split('\\')[-1]
            
            # 生成锚点
            anchor = f'<span id="citation_{idx}"></span>'
            
            # 生成引用条目
            lines.append(f"{anchor}\n\n**[{idx}]** {file_name}")
            
            # 添加相似度分数
            if score is not None:
                lines.append(f" (相似度: {score:.2f})")
            
            # 添加文本预览
            text = source.get('text', '')
            if text:
                preview = text[:200] + '...' if len(text) > 200 else text
                lines.append(f"\n> {preview}\n")
            
            lines.append("\n")
        
        return ''.join(lines)

