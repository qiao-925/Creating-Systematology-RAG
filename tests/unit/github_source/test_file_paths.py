"""
GitHubSource 文件路径获取测试

测试 GitHubSource 获取文件路径的功能。
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from backend.infrastructure.data_loader.source.base import SourceFile
from backend.infrastructure.data_loader.source.github import GitHubSource
from tests.fixtures.mocks import MockGitRepositoryManager


@pytest.mark.fast
class TestGitHubSourceGetFilePaths:
    """测试 GitHubSource 获取文件路径"""
    
    @patch('src.infrastructure.data_loader.source.github.GitRepositoryManager')
    @patch('src.infrastructure.config.config')
    def test_get_file_paths_success(self, mock_config, mock_git_manager_class):
        """测试成功获取文件路径"""
        mock_config.GITHUB_REPOS_PATH = Path("/tmp/repos")
        
        mock_git_manager = MockGitRepositoryManager()
        mock_git_manager_class.return_value = mock_git_manager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test-repo"
            repo_path.mkdir()
            (repo_path / "README.md").write_text("# Test Repo")
            (repo_path / "src").mkdir()
            (repo_path / "src" / "main.py").write_text("print('hello')")
            
            mock_git_manager.repo_path = repo_path
            mock_git_manager.commit_sha = "abc123def456789"
            mock_git_manager.clone_or_update.return_value = (repo_path, "abc123def456789")
            
            source = GitHubSource(owner="test-owner", repo="test-repo")
            files = source.get_file_paths()
            
            assert len(files) > 0
            assert all(isinstance(f, SourceFile) for f in files)
            assert all(f.source_type == 'github' for f in files)
            assert source.repo_path == repo_path
            assert source.commit_sha == "abc123def456789"
            
            for file in files:
                assert 'file_path' in file.metadata
                assert 'file_name' in file.metadata
                assert 'owner' in file.metadata
                assert 'repo' in file.metadata
                assert 'url' in file.metadata
    
    @patch('src.infrastructure.data_loader.source.github.GitRepositoryManager', None)
    def test_get_file_paths_no_git_manager(self):
        """测试 GitRepositoryManager 未安装时的处理"""
        source = GitHubSource(owner="test-owner", repo="test-repo")
        files = source.get_file_paths()
        
        assert files == []
        assert source.repo_path is None
    
    @patch('src.infrastructure.data_loader.source.github.GitRepositoryManager')
    @patch('src.infrastructure.config.config')
    def test_get_file_paths_git_error(self, mock_config, mock_git_manager_class):
        """测试 Git 操作失败时的处理"""
        mock_config.GITHUB_REPOS_PATH = Path("/tmp/repos")
        
        mock_git_manager = MockGitRepositoryManager()
        mock_git_manager.clone_or_update.side_effect = RuntimeError("Git clone failed")
        mock_git_manager_class.return_value = mock_git_manager
        
        source = GitHubSource(owner="test-owner", repo="test-repo")
        files = source.get_file_paths()
        
        assert files == []
        assert source.repo_path is None
    
    @patch('src.infrastructure.data_loader.source.github.GitRepositoryManager')
    @patch('src.infrastructure.config.config')
    def test_get_file_paths_with_directory_filter(self, mock_config, mock_git_manager_class):
        """测试使用目录过滤器"""
        mock_config.GITHUB_REPOS_PATH = Path("/tmp/repos")
        
        mock_git_manager = MockGitRepositoryManager()
        mock_git_manager_class.return_value = mock_git_manager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test-repo"
            repo_path.mkdir()
            (repo_path / "README.md").write_text("# Test")
            (repo_path / "docs").mkdir()
            (repo_path / "docs" / "guide.md").write_text("# Guide")
            (repo_path / "src").mkdir()
            (repo_path / "src" / "main.py").write_text("print('hello')")
            
            mock_git_manager.repo_path = repo_path
            mock_git_manager.clone_or_update.return_value = (repo_path, "abc123")
            
            source = GitHubSource(
                owner="test-owner",
                repo="test-repo",
                filter_directories=["docs"]
            )
            files = source.get_file_paths()
            
            assert len(files) > 0
            for file in files:
                assert 'docs' in str(file.metadata['file_path'])
    
    @patch('src.infrastructure.data_loader.source.github.GitRepositoryManager')
    @patch('src.infrastructure.config.config')
    def test_get_file_paths_with_extension_filter(self, mock_config, mock_git_manager_class):
        """测试使用扩展名过滤器"""
        mock_config.GITHUB_REPOS_PATH = Path("/tmp/repos")
        
        mock_git_manager = MockGitRepositoryManager()
        mock_git_manager_class.return_value = mock_git_manager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test-repo"
            repo_path.mkdir()
            (repo_path / "README.md").write_text("# Test")
            (repo_path / "main.py").write_text("print('hello')")
            (repo_path / "config.json").write_text("{}")
            
            mock_git_manager.repo_path = repo_path
            mock_git_manager.clone_or_update.return_value = (repo_path, "abc123")
            
            source = GitHubSource(
                owner="test-owner",
                repo="test-repo",
                filter_file_extensions=[".md"]
            )
            files = source.get_file_paths()
            
            assert len(files) > 0
            for file in files:
                assert file.path.suffix == ".md"
    
    @patch('src.infrastructure.data_loader.source.github.GitRepositoryManager')
    @patch('src.infrastructure.config.config')
    def test_get_file_paths_exception_handling(self, mock_config, mock_git_manager_class):
        """测试异常处理"""
        mock_config.GITHUB_REPOS_PATH = Path("/tmp/repos")
        
        mock_git_manager = MockGitRepositoryManager()
        mock_git_manager.clone_or_update.side_effect = Exception("Unexpected error")
        mock_git_manager_class.return_value = mock_git_manager
        
        source = GitHubSource(owner="test-owner", repo="test-repo")
        files = source.get_file_paths()
        
        assert files == []
