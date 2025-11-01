"""
响应格式化器主模块
整合校验、修复、替换等功能
"""

from typing import List, Dict, Optional
from src.logger import setup_logger
from .validator import MarkdownValidator
from .fixer import MarkdownFixer
from .replacer import CitationReplacer

logger = setup_logger('response_formatter')


class ResponseFormatter:
    """响应格式化器"""
    
    def __init__(
        self,
        enable_formatting: bool = True,
        min_format_score: float = 0.3,
        enable_citation_replacement: bool = True,
    ):
        """初始化格式化器
        
        Args:
            enable_formatting: 是否启用格式化
            min_format_score: 最低格式分数（低于此值不格式化）
            enable_citation_replacement: 是否启用引用替换
        """
        self.enable_formatting = enable_formatting
        self.min_format_score = min_format_score
        self.enable_citation_replacement = enable_citation_replacement
        
        self.validator = MarkdownValidator()
        self.fixer = MarkdownFixer()
        self.replacer = CitationReplacer()
    
    def format(
        self,
        raw_answer: str,
        sources: Optional[List[Dict]] = None
    ) -> str:
        """格式化回答
        
        Args:
            raw_answer: 原始回答文本
            sources: 引用来源列表
            
        Returns:
            str: 格式化后的文本
        """
        if not self.enable_formatting:
            logger.debug("格式化功能已禁用，返回原文")
            return raw_answer
        
        if not raw_answer or not raw_answer.strip():
            logger.warning("输入文本为空，返回原文")
            return raw_answer
        
        # Step 1: 校验格式
        if not self.validator.validate(raw_answer):
            logger.warning("Markdown 格式校验失败，返回原文")
            logger.debug(f"原文预览: {raw_answer[:200]}...")
            return raw_answer
        
        # 获取格式分数
        score = self.validator.get_format_score(raw_answer)
        logger.debug(f"格式完整度分数: {score:.2f}")
        
        if score < self.min_format_score:
            logger.warning(
                f"格式质量过低 ({score:.2f} < {self.min_format_score})，返回原文"
            )
            return raw_answer
        
        # Step 2: 格式修复
        try:
            fixed_answer = self.fixer.fix(raw_answer)
            logger.debug("格式修复完成")
        except Exception as e:
            logger.error(f"格式修复失败: {e}，返回原文")
            return raw_answer
        
        # Step 3: 引用替换
        final_answer = fixed_answer
        if self.enable_citation_replacement and sources:
            try:
                final_answer = self.replacer.replace_citations(fixed_answer, sources)
                logger.debug(f"引用替换完成，共 {len(sources)} 个来源")
            except Exception as e:
                logger.error(f"引用替换失败: {e}，使用修复后的文本")
                final_answer = fixed_answer
        
        # Step 4: 最终校验
        final_score = self.validator.get_format_score(final_answer)
        if final_score < self.min_format_score:
            logger.warning(
                f"格式化后质量下降 ({final_score:.2f})，返回原文"
            )
            return raw_answer
        
        logger.info(f"格式化成功 (分数: {score:.2f} → {final_score:.2f})")
        return final_answer
    
    def format_with_sources_section(
        self,
        raw_answer: str,
        sources: Optional[List[Dict]] = None
    ) -> str:
        """格式化回答并添加引用来源区域
        
        Args:
            raw_answer: 原始回答文本
            sources: 引用来源列表
            
        Returns:
            str: 格式化后的文本（包含引用来源区域）
        """
        # 先格式化主体内容
        formatted = self.format(raw_answer, sources)
        
        # 添加引用来源区域
        if sources:
            try:
                citations_section = self.replacer.add_citation_anchors(sources)
                formatted += citations_section
                logger.debug("已添加引用来源区域")
            except Exception as e:
                logger.error(f"添加引用来源区域失败: {e}")
        
        return formatted

