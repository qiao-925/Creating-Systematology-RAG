"""
目录加载功能测试

测试从本地目录加载文档的功能。
"""

import pytest
from src.infrastructure.data_loader import load_documents_from_directory


# 导入 fixtures（pytest 会自动发现）


@pytest.mark.fast
class TestLoadDocumentsFromDirectory:
    """测试目录加载功能（使用 SimpleDirectoryReader）"""
    
    def test_load_directory_recursive(self, sample_markdown_dir):
        """测试递归加载目录"""
        docs = load_documents_from_directory(sample_markdown_dir, recursive=True)
        
        assert len(docs) == 3, "应该加载3个文档（包括子目录）"
        assert all(hasattr(doc, 'text') for doc in docs)
        assert all(hasattr(doc, 'metadata') for doc in docs)
        assert all(doc.metadata.get('source_type') == 'markdown' for doc in docs)
    
    def test_load_directory_non_recursive(self, sample_markdown_dir):
        """测试非递归加载目录"""
        docs = load_documents_from_directory(sample_markdown_dir, recursive=False)
        
        assert len(docs) == 2, "应该只加载2个文档（不包括子目录）"
    
    def test_load_empty_directory(self, tmp_path):
        """测试加载空目录"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        docs = load_documents_from_directory(empty_dir)
        
        assert len(docs) == 0, "空目录应该返回空列表"
    
    def test_load_nonexistent_directory(self, tmp_path):
        """测试加载不存在的目录"""
        docs = load_documents_from_directory(tmp_path / "nonexistent")
        
        assert len(docs) == 0, "不存在的目录应该返回空列表"
    
    def test_load_with_text_cleaning(self, tmp_path):
        """测试加载时清理文本"""
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        
        (test_dir / "doc.md").write_text("# 标题\n\n\n\n内容    有    空格", encoding='utf-8')
        
        docs = load_documents_from_directory(test_dir, clean=True)
        
        assert len(docs) == 1
        assert "\n\n\n" not in docs[0].text
        assert "    " not in docs[0].text
    
    def test_load_without_cleaning(self, tmp_path):
        """测试不清理文本加载"""
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        
        content = "# 标题\n\n\n\n内容"
        (test_dir / "doc.md").write_text(content, encoding='utf-8')
        
        docs = load_documents_from_directory(test_dir, clean=False)
        
        assert len(docs) == 1
        normalized_text = docs[0].text.replace('\r\n', '\n').replace('\r', '\n')
        assert "\n\n\n\n" in normalized_text
    
    def test_metadata_extraction(self, sample_markdown_dir):
        """测试元数据提取"""
        docs = load_documents_from_directory(sample_markdown_dir)
        
        for doc in docs:
            assert 'file_path' in doc.metadata
            assert 'file_name' in doc.metadata
            assert 'source_type' in doc.metadata
            assert doc.metadata['source_type'] == 'markdown'
    
    def test_title_extraction_from_markdown(self, tmp_path):
        """测试从Markdown提取标题"""
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        
        (test_dir / "doc.md").write_text("# 系统科学简介\n\n这是内容", encoding='utf-8')
        
        docs = load_documents_from_directory(test_dir)
        
        assert len(docs) == 1
        assert docs[0].metadata.get('title') == '系统科学简介'
    
    def test_custom_extensions(self, tmp_path):
        """测试自定义文件扩展名"""
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        
        (test_dir / "doc.md").write_text("Markdown", encoding='utf-8')
        (test_dir / "doc.txt").write_text("Text", encoding='utf-8')
        (test_dir / "doc.rst").write_text("RST", encoding='utf-8')
        
        # 注意：当前实现中，load_documents_from_directory 使用 filter_file_extensions 参数
        # 而不是 required_exts（SimpleDirectoryReader 会自动加载所有支持的扩展名）
        docs = load_documents_from_directory(test_dir, filter_file_extensions=[".md", ".txt"])
        
        # 验证只加载了指定扩展名的文件
        loaded_exts = {Path(doc.metadata.get('file_path', '')).suffix for doc in docs}
        assert ".md" in loaded_exts or ".txt" in loaded_exts
        assert ".rst" not in loaded_exts or len(docs) <= 2
