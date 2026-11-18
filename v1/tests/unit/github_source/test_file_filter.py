"""
GitHubSource 文件过滤测试

测试 GitHubSource 的文件过滤逻辑。
"""

import pytest
from backend.infrastructure.data_loader.source.github import GitHubSource


@pytest.mark.fast
class TestGitHubSourceShouldIncludeFile:
    """测试 GitHubSource 的文件过滤逻辑"""
    
    def test_should_include_file_no_filters(self):
        """测试无过滤器时包含所有文件"""
        source = GitHubSource(owner="test", repo="test")
        
        assert source._should_include_file("README.md") is True
        assert source._should_include_file("backend/main.py") is True
        assert source._should_include_file("docs/guide.md") is True
    
    def test_should_include_file_with_directory_filter(self):
        """测试目录过滤器"""
        source = GitHubSource(
            owner="test",
            repo="test",
            filter_directories=["docs", "backend"]
        )
        
        assert source._should_include_file("docs/guide.md") is True
        assert source._should_include_file("backend/main.py") is True
        assert source._should_include_file("docs") is True
        
        assert source._should_include_file("README.md") is False
        assert source._should_include_file("other/file.txt") is False
    
    def test_should_include_file_with_extension_filter(self):
        """测试扩展名过滤器"""
        source = GitHubSource(
            owner="test",
            repo="test",
            filter_file_extensions=[".md", ".py"]
        )
        
        assert source._should_include_file("README.md") is True
        assert source._should_include_file("backend/main.py") is True
        
        assert source._should_include_file("config.json") is False
        assert source._should_include_file("file.txt") is False
    
    def test_should_include_file_with_both_filters(self):
        """测试同时使用目录和扩展名过滤器"""
        source = GitHubSource(
            owner="test",
            repo="test",
            filter_directories=["docs"],
            filter_file_extensions=[".md"]
        )
        
        assert source._should_include_file("docs/guide.md") is True
        
        assert source._should_include_file("docs/image.png") is False
        assert source._should_include_file("README.md") is False
    
    def test_should_include_file_directory_filter_with_trailing_slash(self):
        """测试目录过滤器处理尾部斜杠"""
        source = GitHubSource(
            owner="test",
            repo="test",
            filter_directories=["docs/", "backend/"]
        )
        
        assert source._should_include_file("docs/guide.md") is True
        assert source._should_include_file("backend/main.py") is True
