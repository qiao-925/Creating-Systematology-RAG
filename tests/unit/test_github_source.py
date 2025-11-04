"""
GitHub 数据源单元测试
测试 GitHubSource 的各种功能
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.data_source.base import SourceFile
from src.data_source.github_source import GitHubSource


class TestGitHubSourceInitialization:
    """测试 GitHubSource 初始化"""

    def test_init_with_required_params(self):
        """测试使用必需参数初始化"""
        source = GitHubSource(owner="test-owner", repo="test-repo")
        
        assert source.owner == "test-owner"
        assert source.repo == "test-repo"
        assert source.branch == "main"  # 默认分支
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


class TestGitHubSourceGetFilePaths:
    """测试 GitHubSource 获取文件路径"""

    @patch('src.data_source.github_source.GitRepositoryManager')
    @patch('src.data_source.github_source.config')
    def test_get_file_paths_success(self, mock_config, mock_git_manager_class):
        """测试成功获取文件路径"""
        # Mock 配置
        mock_config.GITHUB_REPOS_PATH = Path("/tmp/repos")
        
        # Mock GitRepositoryManager
        mock_git_manager = Mock()
        mock_repo_path = Path("/tmp/repos/test-owner-test-repo")
        mock_commit_sha = "abc123def456789"
        mock_git_manager.clone_or_update.return_value = (mock_repo_path, mock_commit_sha)
        mock_git_manager_class.return_value = mock_git_manager
        
        # 创建测试文件结构
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test-repo"
            repo_path.mkdir()
            (repo_path / "README.md").write_text("# Test Repo")
            (repo_path / "src").mkdir()
            (repo_path / "src" / "main.py").write_text("print('hello')")
            
            mock_git_manager.clone_or_update.return_value = (repo_path, mock_commit_sha)
            
            source = GitHubSource(owner="test-owner", repo="test-repo")
            files = source.get_file_paths()
            
            assert len(files) > 0
            assert all(isinstance(f, SourceFile) for f in files)
            assert all(f.source_type == 'github' for f in files)
            assert source.repo_path == repo_path
            assert source.commit_sha == mock_commit_sha
            
            # 验证文件元数据
            for file in files:
                assert 'file_path' in file.metadata
                assert 'file_name' in file.metadata
                assert 'owner' in file.metadata
                assert 'repo' in file.metadata
                assert 'url' in file.metadata

    @patch('src.data_source.github_source.GitRepositoryManager', None)
    def test_get_file_paths_no_git_manager(self):
        """测试 GitRepositoryManager 未安装时的处理"""
        source = GitHubSource(owner="test-owner", repo="test-repo")
        files = source.get_file_paths()
        
        assert files == []
        assert source.repo_path is None

    @patch('src.data_source.github_source.GitRepositoryManager')
    @patch('src.data_source.github_source.config')
    def test_get_file_paths_git_error(self, mock_config, mock_git_manager_class):
        """测试 Git 操作失败时的处理"""
        mock_config.GITHUB_REPOS_PATH = Path("/tmp/repos")
        
        mock_git_manager = Mock()
        mock_git_manager.clone_or_update.side_effect = RuntimeError("Git clone failed")
        mock_git_manager_class.return_value = mock_git_manager
        
        source = GitHubSource(owner="test-owner", repo="test-repo")
        files = source.get_file_paths()
        
        assert files == []
        assert source.repo_path is None

    @patch('src.data_source.github_source.GitRepositoryManager')
    @patch('src.data_source.github_source.config')
    def test_get_file_paths_with_directory_filter(self, mock_config, mock_git_manager_class):
        """测试使用目录过滤器"""
        mock_config.GITHUB_REPOS_PATH = Path("/tmp/repos")
        
        mock_git_manager = Mock()
        mock_git_manager_class.return_value = mock_git_manager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test-repo"
            repo_path.mkdir()
            (repo_path / "README.md").write_text("# Test")
            (repo_path / "docs").mkdir()
            (repo_path / "docs" / "guide.md").write_text("# Guide")
            (repo_path / "src").mkdir()
            (repo_path / "src" / "main.py").write_text("print('hello')")
            
            mock_git_manager.clone_or_update.return_value = (repo_path, "abc123")
            
            source = GitHubSource(
                owner="test-owner",
                repo="test-repo",
                filter_directories=["docs"]
            )
            files = source.get_file_paths()
            
            # 应该只包含 docs 目录下的文件
            assert len(files) > 0
            for file in files:
                assert 'docs' in str(file.metadata['file_path'])

    @patch('src.data_source.github_source.GitRepositoryManager')
    @patch('src.data_source.github_source.config')
    def test_get_file_paths_with_extension_filter(self, mock_config, mock_git_manager_class):
        """测试使用扩展名过滤器"""
        mock_config.GITHUB_REPOS_PATH = Path("/tmp/repos")
        
        mock_git_manager = Mock()
        mock_git_manager_class.return_value = mock_git_manager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test-repo"
            repo_path.mkdir()
            (repo_path / "README.md").write_text("# Test")
            (repo_path / "main.py").write_text("print('hello')")
            (repo_path / "config.json").write_text("{}")
            
            mock_git_manager.clone_or_update.return_value = (repo_path, "abc123")
            
            source = GitHubSource(
                owner="test-owner",
                repo="test-repo",
                filter_file_extensions=[".md"]
            )
            files = source.get_file_paths()
            
            # 应该只包含 .md 文件
            assert len(files) > 0
            for file in files:
                assert file.path.suffix == ".md"


class TestGitHubSourceWalkRepository:
    """测试 GitHubSource 的仓库遍历功能"""

    def test_walk_repository_basic(self):
        """测试基本仓库遍历"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / "file1.txt").write_text("content1")
            (repo_path / "file2.md").write_text("content2")
            subdir = repo_path / "subdir"
            subdir.mkdir()
            (subdir / "file3.py").write_text("content3")
            
            source = GitHubSource(owner="test", repo="test")
            files = source._walk_repository(repo_path)
            
            assert len(files) == 3
            assert all(f.exists() for f in files)
            file_names = [f.name for f in files]
            assert "file1.txt" in file_names
            assert "file2.md" in file_names
            assert "file3.py" in file_names

    def test_walk_repository_excludes_dot_git(self):
        """测试排除 .git 目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / "file1.txt").write_text("content1")
            git_dir = repo_path / ".git"
            git_dir.mkdir()
            (git_dir / "config").write_text("git config")
            
            source = GitHubSource(owner="test", repo="test")
            files = source._walk_repository(repo_path)
            
            # 应该只包含 file1.txt，不包含 .git 目录下的文件
            assert len(files) == 1
            assert files[0].name == "file1.txt"

    def test_walk_repository_excludes_pycache(self):
        """测试排除 __pycache__ 目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / "main.py").write_text("print('hello')")
            pycache = repo_path / "__pycache__"
            pycache.mkdir()
            (pycache / "main.pyc").write_text("compiled")
            
            source = GitHubSource(owner="test", repo="test")
            files = source._walk_repository(repo_path)
            
            # 应该只包含 main.py
            assert len(files) == 1
            assert files[0].name == "main.py"

    def test_walk_repository_excludes_pyc_files(self):
        """测试排除 .pyc 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / "main.py").write_text("print('hello')")
            (repo_path / "main.pyc").write_text("compiled")
            
            source = GitHubSource(owner="test", repo="test")
            files = source._walk_repository(repo_path)
            
            # 应该只包含 main.py，不包含 main.pyc
            file_names = [f.name for f in files]
            assert "main.py" in file_names
            assert "main.pyc" not in file_names


class TestGitHubSourceShouldIncludeFile:
    """测试 GitHubSource 的文件过滤逻辑"""

    def test_should_include_file_no_filters(self):
        """测试无过滤器时包含所有文件"""
        source = GitHubSource(owner="test", repo="test")
        
        assert source._should_include_file("README.md") is True
        assert source._should_include_file("src/main.py") is True
        assert source._should_include_file("docs/guide.md") is True

    def test_should_include_file_with_directory_filter(self):
        """测试目录过滤器"""
        source = GitHubSource(
            owner="test",
            repo="test",
            filter_directories=["docs", "src"]
        )
        
        # 应该包含
        assert source._should_include_file("docs/guide.md") is True
        assert source._should_include_file("src/main.py") is True
        assert source._should_include_file("docs") is True
        
        # 不应该包含
        assert source._should_include_file("README.md") is False
        assert source._should_include_file("other/file.txt") is False

    def test_should_include_file_with_extension_filter(self):
        """测试扩展名过滤器"""
        source = GitHubSource(
            owner="test",
            repo="test",
            filter_file_extensions=[".md", ".py"]
        )
        
        # 应该包含
        assert source._should_include_file("README.md") is True
        assert source._should_include_file("src/main.py") is True
        
        # 不应该包含
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
        
        # 应该包含：docs 目录下的 .md 文件
        assert source._should_include_file("docs/guide.md") is True
        
        # 不应该包含：docs 目录下但不是 .md
        assert source._should_include_file("docs/image.png") is False
        
        # 不应该包含：是 .md 但不在 docs 目录
        assert source._should_include_file("README.md") is False

    def test_should_include_file_directory_filter_with_trailing_slash(self):
        """测试目录过滤器处理尾部斜杠"""
        source = GitHubSource(
            owner="test",
            repo="test",
            filter_directories=["docs/", "src/"]
        )
        
        # 应该正确处理尾部斜杠
        assert source._should_include_file("docs/guide.md") is True
        assert source._should_include_file("src/main.py") is True


class TestGitHubSourceErrorHandling:
    """测试 GitHubSource 的错误处理"""

    @patch('src.data_source.github_source.GitRepositoryManager')
    @patch('src.data_source.github_source.config')
    def test_get_file_paths_exception_handling(self, mock_config, mock_git_manager_class):
        """测试异常处理"""
        mock_config.GITHUB_REPOS_PATH = Path("/tmp/repos")
        
        mock_git_manager = Mock()
        # 模拟在遍历目录时抛出异常
        def side_effect(*args, **kwargs):
            raise Exception("Unexpected error")
        mock_git_manager.clone_or_update = side_effect
        mock_git_manager_class.return_value = mock_git_manager
        
        source = GitHubSource(owner="test-owner", repo="test-repo")
        files = source.get_file_paths()
        
        # 异常应该被捕获，返回空列表
        assert files == []

    def test_walk_repository_handles_symlinks(self):
        """测试处理符号链接"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / "file1.txt").write_text("content1")
            
            # 注意：Windows 上创建符号链接需要特殊权限，这里只测试逻辑
            source = GitHubSource(owner="test", repo="test")
            files = source._walk_repository(repo_path)
            
            # 应该只包含真实文件
            assert len(files) >= 1
            assert all(f.is_file() for f in files)
