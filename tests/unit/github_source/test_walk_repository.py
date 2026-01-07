"""
GitHubSource 仓库遍历测试

测试 GitHubSource 的仓库遍历功能。
"""

import pytest
import tempfile
from pathlib import Path
from backend.infrastructure.data_loader.source.github import GitHubSource


@pytest.mark.fast
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
            
            file_names = [f.name for f in files]
            assert "main.py" in file_names
            assert "main.pyc" not in file_names
    
    def test_walk_repository_handles_symlinks(self):
        """测试处理符号链接"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            (repo_path / "file1.txt").write_text("content1")
            
            source = GitHubSource(owner="test", repo="test")
            files = source._walk_repository(repo_path)
            
            assert len(files) >= 1
            assert all(f.is_file() for f in files)
