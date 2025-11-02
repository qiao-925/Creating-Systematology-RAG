"""
数据加载器工具函数模块
包含安全打印等辅助函数
"""

import re
from typing import List, Optional

from llama_index.core.schema import Document as LlamaDocument

from src.logger import setup_logger

logger = setup_logger('data_loader')


def safe_print(text: str):
    """安全打印（处理编码问题）"""
    try:
        print(text)
    except UnicodeEncodeError:
        # 在 Windows GBK 编码下，回退到 ASCII 友好的输出
        text = text.encode('ascii', 'replace').decode('ascii')
        print(text)


class DocumentProcessor:
    """文档预处理器"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            清理后的文本
        """
        # 移除多余的空白字符
        text = re.sub(r'[ \t]+', ' ', text)
        
        # 移除行首行尾空白
        lines = [line.strip() for line in text.split('\n')]
        
        # 移除多余的空行（保留最多一个空行）
        cleaned_lines = []
        prev_empty = False
        for line in lines:
            if line:  # 非空行
                cleaned_lines.append(line)
                prev_empty = False
            else:  # 空行
                if not prev_empty:  # 只保留第一个空行
                    cleaned_lines.append(line)
                    prev_empty = True
        
        text = '\n'.join(cleaned_lines)
        return text.strip()
    
    @staticmethod
    def enrich_metadata(document: LlamaDocument, additional_metadata: dict) -> LlamaDocument:
        """为文档添加额外的元数据
        
        Args:
            document: 原始文档
            additional_metadata: 要添加的元数据
            
        Returns:
            更新后的文档
        """
        document.metadata.update(additional_metadata)
        return document
    
    @staticmethod
    def filter_by_length(documents: List[LlamaDocument], 
                        min_length: int = 50) -> List[LlamaDocument]:
        """过滤掉太短的文档
        
        Args:
            documents: 文档列表
            min_length: 最小长度
            
        Returns:
            过滤后的文档列表
        """
        filtered = [doc for doc in documents if len(doc.text) >= min_length]
        
        removed_count = len(documents) - len(filtered)
        if removed_count > 0:
            safe_print(f"⚠️  过滤掉 {removed_count} 个过短的文档")
        
        return filtered
    
    @staticmethod
    def extract_title_from_markdown(content: str) -> Optional[str]:
        """从Markdown内容中提取标题（第一个一级标题）
        
        Args:
            content: Markdown 文本内容
            
        Returns:
            提取的标题，如果没有则返回 None
        """
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return None

