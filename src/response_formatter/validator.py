"""
Markdown 格式校验器
检测文本是否包含有效的 Markdown 语法
"""

import re
from typing import Dict


class MarkdownValidator:
    """Markdown 格式校验器"""
    
    def validate(self, text: str) -> bool:
        """检查是否包含 Markdown 语法
        
        Args:
            text: 待检查的文本
            
        Returns:
            bool: 是否包含有效的 Markdown 格式
        """
        if not text or not text.strip():
            return False
        
        # 检测标题
        has_title = bool(re.search(r'^#+\s', text, re.MULTILINE))
        
        # 检测列表
        has_list = bool(re.search(r'^\s*[-*+]\s|^\s*\d+\.\s', text, re.MULTILINE))
        
        # 检测粗体
        has_bold = bool(re.search(r'\*\*[^*]+\*\*', text))
        
        # 至少包含一种格式
        return has_title or has_list or has_bold
    
    def get_format_score(self, text: str) -> float:
        """计算格式完整度分数（0-1）
        
        Args:
            text: 待评分的文本
            
        Returns:
            float: 格式完整度分数
        """
        if not text or not text.strip():
            return 0.0
        
        scores = []
        
        # 检查标题（权重 0.3）
        if re.search(r'^#+\s', text, re.MULTILINE):
            scores.append(0.3)
        
        # 检查列表（权重 0.3）
        if re.search(r'^\s*[-*+]\s|^\s*\d+\.\s', text, re.MULTILINE):
            scores.append(0.3)
        
        # 检查粗体（权重 0.2）
        if re.search(r'\*\*[^*]+\*\*', text):
            scores.append(0.2)
        
        # 检查引用块（权重 0.1）
        if re.search(r'^>\s', text, re.MULTILINE):
            scores.append(0.1)
        
        # 检查分割线（权重 0.1）
        if re.search(r'^---+\s*$', text, re.MULTILINE):
            scores.append(0.1)
        
        return sum(scores)
    
    def get_format_details(self, text: str) -> Dict[str, bool]:
        """获取格式详情
        
        Args:
            text: 待分析的文本
            
        Returns:
            dict: 包含各种格式元素的检测结果
        """
        if not text or not text.strip():
            return {
                'has_title': False,
                'has_list': False,
                'has_bold': False,
                'has_quote': False,
                'has_divider': False,
                'has_code': False,
                'has_link': False,
            }
        
        return {
            'has_title': bool(re.search(r'^#+\s', text, re.MULTILINE)),
            'has_list': bool(re.search(r'^\s*[-*+]\s|^\s*\d+\.\s', text, re.MULTILINE)),
            'has_bold': bool(re.search(r'\*\*[^*]+\*\*', text)),
            'has_quote': bool(re.search(r'^>\s', text, re.MULTILINE)),
            'has_divider': bool(re.search(r'^---+\s*$', text, re.MULTILINE)),
            'has_code': bool(re.search(r'`[^`]+`', text)),
            'has_link': bool(re.search(r'\[([^\]]+)\]\(([^)]+)\)', text)),
        }

