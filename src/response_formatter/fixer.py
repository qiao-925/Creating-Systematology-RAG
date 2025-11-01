"""
Markdown 格式修复器
修复常见的格式问题，确保 Markdown 语法正确
"""

import re


class MarkdownFixer:
    """Markdown 格式修复器"""
    
    def fix(self, text: str) -> str:
        """修复常见的格式问题
        
        Args:
            text: 待修复的文本
            
        Returns:
            str: 修复后的文本
        """
        if not text or not text.strip():
            return text
        
        fixed = text
        
        # 1. 确保标题前后有空行
        fixed = self._fix_heading_spacing(fixed)
        
        # 2. 确保列表前后有空行
        fixed = self._fix_list_spacing(fixed)
        
        # 3. 统一列表符号（统一使用 -）
        fixed = self._normalize_list_markers(fixed)
        
        # 4. 修复过度换行
        fixed = self._fix_excessive_newlines(fixed)
        
        # 5. 确保文本末尾只有一个换行
        fixed = fixed.rstrip() + '\n'
        
        return fixed
    
    def _fix_heading_spacing(self, text: str) -> str:
        """确保标题前后有空行"""
        # 标题前加空行（除非是文档开头）
        text = re.sub(r'([^\n])\n(^#+\s)', r'\1\n\n\2', text, flags=re.MULTILINE)
        
        # 标题后加空行
        text = re.sub(r'(^#+\s[^\n]+)\n([^\n#])', r'\1\n\n\2', text, flags=re.MULTILINE)
        
        return text
    
    def _fix_list_spacing(self, text: str) -> str:
        """确保列表前后有空行"""
        # 列表前加空行（除非是文档开头或另一个列表项）
        text = re.sub(
            r'([^\n])\n(^\s*[-*+]\s|^\s*\d+\.\s)',
            r'\1\n\n\2',
            text,
            flags=re.MULTILINE
        )
        
        # 列表后加空行（如果下一行不是列表项）
        # 修复：字符类中的 - 需要转义或放在最后
        text = re.sub(
            r'(^\s*[-*+]\s[^\n]+|^\s*\d+\.\s[^\n]+)\n([^\n\s*+\d-])',
            r'\1\n\n\2',
            text,
            flags=re.MULTILINE
        )
        
        return text
    
    def _normalize_list_markers(self, text: str) -> str:
        """统一列表符号（使用 -）"""
        # 将 * 和 + 统一替换为 -
        text = re.sub(r'^\s*[*+]\s', '- ', text, flags=re.MULTILINE)
        
        return text
    
    def _fix_excessive_newlines(self, text: str) -> str:
        """修复过度换行（最多保留两个换行）"""
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text

