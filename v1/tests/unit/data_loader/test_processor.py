"""
文档处理器测试

测试文档处理功能（清理、元数据、过滤等）。
"""

import pytest
from backend.infrastructure.data_loader.processor import DocumentProcessor
from llama_index.core import Document


@pytest.mark.fast
class TestDocumentProcessor:
    """文档处理器测试"""
    
    def test_clean_text_removes_extra_spaces(self):
        """测试移除多余空格"""
        dirty_text = "这是    多余的    空格"
        clean = DocumentProcessor.clean_text(dirty_text)
        
        assert "    " not in clean
        assert "多余的 空格" in clean
    
    def test_clean_text_removes_extra_newlines(self):
        """测试移除多余换行"""
        dirty_text = "第一行\n\n\n\n第二行"
        clean = DocumentProcessor.clean_text(dirty_text)
        
        assert "\n\n\n" not in clean
        assert "第一行\n\n第二行" in clean
    
    def test_clean_text_strips_whitespace(self):
        """测试去除首尾空白"""
        dirty_text = "  \n  文本内容  \n  "
        clean = DocumentProcessor.clean_text(dirty_text)
        
        assert clean == "文本内容"
    
    def test_enrich_metadata(self, sample_documents):
        """测试添加元数据"""
        doc = sample_documents[0]
        original_metadata = doc.metadata.copy()
        
        additional = {"category": "科学", "author": "测试"}
        enriched = DocumentProcessor.enrich_metadata(doc, additional)
        
        assert enriched.metadata['category'] == '科学'
        assert enriched.metadata['author'] == '测试'
        for key in original_metadata:
            assert enriched.metadata[key] == original_metadata[key]
    
    def test_filter_by_length_default(self):
        """测试按长度过滤（默认最小长度）"""
        docs = [
            Document(text="短", metadata={}),
            Document(text="这是一个足够长的文档内容，确保长度超过50字符，这样才能通过过滤测试这是一个足够长的文档内容，确保长度超过50字符", metadata={}),
            Document(text="中等长度的文档内容", metadata={})
        ]
        
        filtered = DocumentProcessor.filter_by_length(docs, min_length=50)
        
        assert len(filtered) == 1
        assert len(filtered[0].text) >= 50
    
    def test_filter_by_length_custom(self):
        """测试自定义最小长度"""
        docs = [
            Document(text="a" * 10, metadata={}),
            Document(text="b" * 20, metadata={}),
            Document(text="c" * 30, metadata={})
        ]
        
        filtered = DocumentProcessor.filter_by_length(docs, min_length=25)
        
        assert len(filtered) == 1
        assert len(filtered[0].text) == 30
    
    def test_extract_title_from_markdown(self):
        """测试从Markdown提取标题"""
        content = "# 系统科学简介\n\n这是内容"
        title = DocumentProcessor.extract_title_from_markdown(content)
        
        assert title == "系统科学简介"
    
    def test_extract_title_from_markdown_no_title(self):
        """测试没有标题的Markdown"""
        content = "这是没有标题的内容"
        title = DocumentProcessor.extract_title_from_markdown(content)
        
        assert title is None
    
    def test_extract_title_ignores_lower_level_headers(self):
        """测试只提取一级标题"""
        content = "## 二级标题\n\n# 一级标题\n\n### 三级标题"
        title = DocumentProcessor.extract_title_from_markdown(content)
        
        assert title == "一级标题"
