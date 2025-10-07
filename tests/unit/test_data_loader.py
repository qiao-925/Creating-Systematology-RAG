"""
数据加载器模块单元测试
"""

import pytest
from pathlib import Path
from src.data_loader import (
    MarkdownLoader,
    WebLoader,
    DocumentProcessor,
    load_documents_from_directory
)


class TestMarkdownLoader:
    """Markdown加载器测试"""
    
    def test_load_single_file(self, sample_markdown_file):
        """测试加载单个Markdown文件"""
        loader = MarkdownLoader()
        doc = loader.load_file(sample_markdown_file)
        
        assert doc is not None, "应该成功加载文档"
        assert "系统科学" in doc.text, "文档内容应该包含'系统科学'"
        assert doc.metadata['file_name'] == 'test_doc.md'
        assert doc.metadata['source_type'] == 'markdown'
    
    def test_load_file_extracts_title(self, sample_markdown_file):
        """测试提取文档标题"""
        loader = MarkdownLoader()
        doc = loader.load_file(sample_markdown_file)
        
        assert 'title' in doc.metadata
        assert doc.metadata['title'] == '系统科学简介'
    
    def test_load_nonexistent_file(self, tmp_path):
        """测试加载不存在的文件"""
        loader = MarkdownLoader()
        doc = loader.load_file(tmp_path / "nonexistent.md")
        
        assert doc is None, "加载不存在的文件应该返回None"
    
    def test_load_wrong_extension(self, tmp_path):
        """测试加载错误扩展名的文件"""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("This is a text file")
        
        loader = MarkdownLoader()
        doc = loader.load_file(txt_file)
        
        assert doc is None, "非Markdown文件应该返回None"
    
    def test_load_directory_recursive(self, sample_markdown_dir):
        """测试递归加载目录"""
        loader = MarkdownLoader()
        docs = loader.load_directory(sample_markdown_dir, recursive=True)
        
        assert len(docs) == 3, "应该加载3个文档（包括子目录）"
        assert all(doc.metadata['source_type'] == 'markdown' for doc in docs)
    
    def test_load_directory_non_recursive(self, sample_markdown_dir):
        """测试非递归加载目录"""
        loader = MarkdownLoader()
        docs = loader.load_directory(sample_markdown_dir, recursive=False)
        
        assert len(docs) == 2, "应该只加载2个文档（不包括子目录）"
    
    def test_load_empty_directory(self, tmp_path):
        """测试加载空目录"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        loader = MarkdownLoader()
        docs = loader.load_directory(empty_dir)
        
        assert len(docs) == 0, "空目录应该返回空列表"
    
    def test_load_directory_with_mixed_files(self, tmp_path):
        """测试包含多种文件类型的目录"""
        test_dir = tmp_path / "mixed"
        test_dir.mkdir()
        
        # 创建不同类型的文件
        (test_dir / "doc.md").write_text("# Markdown")
        (test_dir / "doc.txt").write_text("Text file")
        (test_dir / "doc.py").write_text("print('Python')")
        
        loader = MarkdownLoader()
        docs = loader.load_directory(test_dir)
        
        assert len(docs) == 1, "应该只加载Markdown文件"
        assert docs[0].metadata['file_name'] == 'doc.md'


class TestWebLoader:
    """Web加载器测试"""
    
    def test_load_url_success(self, mocker):
        """测试成功加载URL"""
        # Mock requests.get
        mock_response = mocker.Mock()
        mock_response.content = b"""
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Test Content</h1>
                <p>This is a test paragraph.</p>
                <script>console.log('should be removed');</script>
                <style>.test { color: red; }</style>
            </body>
        </html>
        """
        mock_response.raise_for_status = mocker.Mock()
        mocker.patch('requests.get', return_value=mock_response)
        
        loader = WebLoader()
        doc = loader.load_url("https://example.com/test")
        
        assert doc is not None
        assert "Test Content" in doc.text
        assert "test paragraph" in doc.text
        assert "console.log" not in doc.text  # script被移除
        assert "color: red" not in doc.text  # style被移除
        assert doc.metadata['source_type'] == 'web'
        assert doc.metadata['url'] == "https://example.com/test"
    
    def test_load_url_invalid_url(self):
        """测试无效URL"""
        loader = WebLoader()
        doc = loader.load_url("invalid-url")
        
        assert doc is None
    
    def test_load_url_network_error(self, mocker):
        """测试网络错误"""
        import requests
        mocker.patch('requests.get', side_effect=requests.RequestException("Network error"))
        
        loader = WebLoader()
        doc = loader.load_url("https://example.com/test")
        
        assert doc is None
    
    def test_load_urls_batch(self, mocker):
        """测试批量加载URL"""
        mock_response = mocker.Mock()
        mock_response.content = b"<html><body>Test</body></html>"
        mock_response.raise_for_status = mocker.Mock()
        mocker.patch('requests.get', return_value=mock_response)
        
        loader = WebLoader()
        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3"
        ]
        docs = loader.load_urls(urls)
        
        assert len(docs) == 3
    
    def test_load_url_timeout(self):
        """测试超时设置"""
        loader = WebLoader(timeout=5)
        assert loader.timeout == 5


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
        # 原有元数据应该保留
        for key in original_metadata:
            assert enriched.metadata[key] == original_metadata[key]
    
    def test_filter_by_length_default(self):
        """测试按长度过滤（默认最小长度）"""
        from llama_index.core import Document
        
        docs = [
            Document(text="短", metadata={}),
            Document(text="这是一个足够长的文档内容" * 3, metadata={}),
            Document(text="中等长度的文档内容", metadata={})
        ]
        
        filtered = DocumentProcessor.filter_by_length(docs, min_length=50)
        
        assert len(filtered) == 1
        assert len(filtered[0].text) >= 50
    
    def test_filter_by_length_custom(self):
        """测试自定义最小长度"""
        from llama_index.core import Document
        
        docs = [
            Document(text="a" * 10, metadata={}),
            Document(text="b" * 20, metadata={}),
            Document(text="c" * 30, metadata={})
        ]
        
        filtered = DocumentProcessor.filter_by_length(docs, min_length=25)
        
        assert len(filtered) == 1
        assert len(filtered[0].text) == 30


class TestLoadDocumentsHelpers:
    """测试便捷函数"""
    
    def test_load_documents_from_directory(self, sample_markdown_dir):
        """测试从目录加载文档的便捷函数"""
        docs = load_documents_from_directory(sample_markdown_dir, recursive=True)
        
        assert len(docs) == 3
        assert all(hasattr(doc, 'text') for doc in docs)
        assert all(hasattr(doc, 'metadata') for doc in docs)
    
    def test_load_documents_from_directory_with_cleaning(self, tmp_path):
        """测试加载时清理文本"""
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        
        # 创建包含多余空白的文档
        (test_dir / "doc.md").write_text("# 标题\n\n\n\n内容    有    空格")
        
        docs = load_documents_from_directory(test_dir, clean=True)
        
        assert len(docs) == 1
        assert "\n\n\n" not in docs[0].text
        assert "    " not in docs[0].text


@pytest.mark.parametrize("filename,should_load", [
    ("test.md", True),
    ("test.markdown", True),
    ("test.MD", True),
    ("test.txt", False),
    ("test.pdf", False),
    ("test", False),
])
def test_file_extension_recognition(filename, should_load, tmp_path):
    """参数化测试：文件扩展名识别"""
    test_file = tmp_path / filename
    test_file.write_text("# Test content")
    
    loader = MarkdownLoader()
    doc = loader.load_file(test_file)
    
    if should_load:
        assert doc is not None, f"{filename} 应该被加载"
    else:
        assert doc is None, f"{filename} 不应该被加载"

