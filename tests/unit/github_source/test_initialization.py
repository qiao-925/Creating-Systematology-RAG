"""
GitHubSource 初始化测试

测试 GitHubSource 的初始化功能。
"""

import pytest
from src.infrastructure.data_loader.source.github import GitHubSource


@pytest.mark.fast
class TestGitHubSourceInitialization:
    """测试 GitHubSource 初始化"""
    
    def test_init_with_required_params(self):
        """测试使用必需参数初始化"""
        source = GitHubSource(owner="test-owner", repo="test-repo")
        
        assert source.owner == "test-owner"
        assert source.repo == "test-repo"
        assert source.branch == "main"
        assert source.filter_directories is None
        assert source.filter_file_extensions is None
        assert source.show_progress is True
        assert source.repo_path is None
        assert source.commit_sha is None
    
    def test_init_with_branch(self):
        """测试指定分支初始化"""
        source = GitHubSource(
            owner="test-owner",
            repo="test-repo",
            branch="develop"
        )
        
        assert source.branch == "develop"
    
    def test_init_with_filters(self):
        """测试使用过滤器初始化"""
        source = GitHubSource(
            owner="test-owner",
            repo="test-repo",
            filter_directories=["docs", "src"],
            filter_file_extensions=[".md", ".py"]
        )
        
        assert source.filter_directories == ["docs", "src"]
        assert source.filter_file_extensions == [".md", ".py"]
    
    def test_init_with_show_progress_false(self):
        """测试禁用进度显示"""
        source = GitHubSource(
            owner="test-owner",
            repo="test-repo",
            show_progress=False
        )
        
        assert source.show_progress is False
