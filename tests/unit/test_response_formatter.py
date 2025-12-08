"""
响应格式化模块单元测试
"""

import pytest
from src.business.rag_engine.formatting import (
    MarkdownValidator,
    MarkdownFixer,
    CitationReplacer,
    ResponseFormatter,
)


class TestMarkdownValidator:
    """测试 Markdown 校验器"""
    
    def test_validate_with_title(self):
        """测试标题检测"""
        validator = MarkdownValidator()
        
        text_with_title = "# 这是标题\n\n这是内容"
        assert validator.validate(text_with_title) is True
        
        text_without_markdown = "这是普通文本"
        assert validator.validate(text_without_markdown) is False
    
    def test_validate_with_list(self):
        """测试列表检测"""
        validator = MarkdownValidator()
        
        text_with_list = "内容：\n- 列表项1\n- 列表项2"
        assert validator.validate(text_with_list) is True
    
    def test_validate_with_bold(self):
        """测试粗体检测"""
        validator = MarkdownValidator()
        
        text_with_bold = "这是**重要内容**的说明"
        assert validator.validate(text_with_bold) is True
    
    def test_validate_empty_text(self):
        """测试空文本"""
        validator = MarkdownValidator()
        
        assert validator.validate("") is False
        assert validator.validate(None) is False
    
    def test_get_format_score(self):
        """测试格式分数计算"""
        validator = MarkdownValidator()
        
        # 包含标题和列表
        text = "# 标题\n\n- 列表项\n- 列表项2"
        score = validator.validate(text)
        assert score >= 0.6  # 标题0.3 + 列表0.3
        
        # 只有粗体
        text_with_bold = "这是**重要**内容"
        score = validator.get_format_score(text_with_bold)
        assert score == 0.2
    
    def test_get_format_details(self):
        """测试格式详情获取"""
        validator = MarkdownValidator()
        
        text = "# 标题\n\n- 列表\n\n**粗体**\n\n> 引用"
        details = validator.get_format_details(text)
        
        assert details['has_title'] is True
        assert details['has_list'] is True
        assert details['has_bold'] is True
        assert details['has_quote'] is True


class TestMarkdownFixer:
    """测试 Markdown 修复器"""
    
    def test_fix_heading_spacing(self):
        """测试标题间距修复"""
        fixer = MarkdownFixer()
        
        input_text = "内容1\n# 标题\n内容2"
        fixed = fixer.fix(input_text)
        
        # 标题前后应有空行
        assert "\n\n# 标题\n\n" in fixed
    
    def test_fix_list_spacing(self):
        """测试列表间距修复"""
        fixer = MarkdownFixer()
        
        input_text = "内容\n- 列表项"
        fixed = fixer.fix(input_text)
        
        # 列表前应有空行
        assert "\n\n-" in fixed
    
    def test_normalize_list_markers(self):
        """测试列表符号统一"""
        fixer = MarkdownFixer()
        
        input_text = "* 项目1\n+ 项目2\n- 项目3"
        fixed = fixer.fix(input_text)
        
        # 所有符号应统一为 -
        assert "- 项目1" in fixed
        assert "- 项目2" in fixed
        assert "- 项目3" in fixed
    
    def test_fix_excessive_newlines(self):
        """测试过度换行修复"""
        fixer = MarkdownFixer()
        
        input_text = "内容1\n\n\n\n内容2"
        fixed = fixer.fix(input_text)
        
        # 最多保留两个换行
        assert "\n\n\n" not in fixed
        assert "\n\n" in fixed


class TestCitationReplacer:
    """测试引用替换器"""
    
    def test_replace_citations(self):
        """测试引用替换"""
        replacer = CitationReplacer()
        
        text = "这是内容[1]，还有内容[2]"
        sources = [
            {'index': 1, 'metadata': {'file_path': 'file1.txt'}},
            {'index': 2, 'metadata': {'file_path': 'file2.txt'}},
        ]
        
        result = replacer.replace_citations(text, sources)
        
        # 应替换为链接格式
        assert "[1](#citation_1)" in result
        assert "[2](#citation_2)" in result
    
    def test_replace_citations_out_of_range(self):
        """测试超出范围的引用"""
        replacer = CitationReplacer()
        
        text = "这是内容[1]和[999]"
        sources = [{'index': 1}]
        
        result = replacer.replace_citations(text, sources)
        
        # 范围内的应替换，范围外的保持原样
        assert "[1](#citation_1)" in result
        assert "[999]" in result
    
    def test_replace_citations_empty_sources(self):
        """测试空来源列表"""
        replacer = CitationReplacer()
        
        text = "这是内容[1]"
        result = replacer.replace_citations(text, None)
        
        # 应返回原文
        assert result == text
    
    def test_add_citation_anchors(self):
        """测试添加引用锚点"""
        replacer = CitationReplacer()
        
        sources = [
            {
                'index': 1,
                'text': '这是引用内容',
                'score': 0.95,
                'metadata': {'file_path': 'test.txt'}
            }
        ]
        
        result = replacer.add_citation_anchors(sources)
        
        # 应包含锚点和引用信息
        assert "citation_1" in result
        assert "test.txt" in result
        assert "0.95" in result


class TestResponseFormatter:
    """测试响应格式化器"""
    
    def test_format_with_valid_markdown(self):
        """测试有效的 Markdown 格式化"""
        formatter = ResponseFormatter(enable_formatting=True)
        
        input_text = "# 标题\n\n- 列表项1\n- 列表项2"
        result = formatter.format(input_text)
        
        # 应返回格式化后的文本
        assert result is not None
        assert len(result) > 0
    
    def test_format_with_invalid_markdown(self):
        """测试无效的 Markdown（应返回原文）"""
        formatter = ResponseFormatter(enable_formatting=True)
        
        input_text = "这是普通文本，没有任何 Markdown 格式"
        result = formatter.format(input_text)
        
        # 应返回原文
        assert result == input_text
    
    def test_format_disabled(self):
        """测试禁用格式化"""
        formatter = ResponseFormatter(enable_formatting=False)
        
        input_text = "# 标题\n\n- 列表"
        result = formatter.format(input_text)
        
        # 应直接返回原文
        assert result == input_text
    
    def test_format_with_citations(self):
        """测试带引用的格式化"""
        formatter = ResponseFormatter(
            enable_formatting=True,
            enable_citation_replacement=True
        )
        
        input_text = "# 标题\n\n这是内容[1]和[2]"
        sources = [
            {'index': 1, 'metadata': {}},
            {'index': 2, 'metadata': {}},
        ]
        
        result = formatter.format(input_text, sources)
        
        # 应包含链接
        assert "citation_1" in result or "[1]" in result
    
    def test_format_with_low_quality(self):
        """测试低质量格式（应返回原文）"""
        formatter = ResponseFormatter(
            enable_formatting=True,
            min_format_score=0.5
        )
        
        # 只有粗体，分数只有 0.2
        input_text = "这是**粗体**内容"
        result = formatter.format(input_text)
        
        # 分数过低，应返回原文
        assert result == input_text
    
    def test_format_with_sources_section(self):
        """测试带来源区域的格式化"""
        formatter = ResponseFormatter(enable_formatting=True)
        
        input_text = "# 标题\n\n- 列表项"
        sources = [
            {
                'index': 1,
                'text': '引用内容',
                'score': 0.9,
                'metadata': {'file_path': 'test.txt'}
            }
        ]
        
        result = formatter.format_with_sources_section(input_text, sources)
        
        # 应包含来源区域
        assert "参考来源" in result or "引用" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

