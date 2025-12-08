"""
GitHubSource 元数据测试

测试 GitHubSource 的元数据获取功能。
"""

import pytest
from src.infrastructure.data_loader.source.github import GitHubSource


@pytest.mark.fast
class TestGitHubSourceMetadata:
    """测试 GitHubSource 元数据获取"""
    
    def test_get_source_metadata_basic(self):
        """测试获取基本元数据"""
        source = GitHubSource(owner="test-owner", repo="test-repo")
        metadata = source.get_source_metadata()
        
        assert metadata['owner'] == "test-owner"
        assert metadata['repo'] == "test-repo"
        assert metadata['branch'] == "main"
        assert metadata['repository'] == "test-owner/test-repo"
        assert metadata['url'] == "https://github.com/test-owner/test-repo/blob/main"
        assert metadata['commit_sha'] is None
    
    def test_get_source_metadata_with_branch(self):
        """测试获取指定分支的元数据"""
        source = GitHubSource(
            owner="test-owner",
            repo="test-repo",
            branch="develop"
        )
        metadata = source.get_source_metadata()
        
        assert metadata['branch'] == "develop"
        assert metadata['url'] == "https://github.com/test-owner/test-repo/blob/develop"
    
    def test_get_source_metadata_with_commit_sha(self):
        """测试包含 commit_sha 的元数据"""
        source = GitHubSource(owner="test-owner", repo="test-repo")
        source.commit_sha = "abc123def456"
        metadata = source.get_source_metadata()
        
        assert metadata['commit_sha'] == "abc123def456"
