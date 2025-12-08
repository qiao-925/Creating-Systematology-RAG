"""
Git 仓库管理器单元测试
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

from src.infrastructure.git import GitRepositoryManager


class TestGitRepositoryManager:
    """测试 Git 仓库管理器"""
    
    def test_init(self, tmp_path):
        """测试初始化"""
        repos_path = tmp_path / "repos"
        manager = GitRepositoryManager(repos_path)
        
        assert manager.repos_base_path == repos_path
        assert repos_path.exists()
    
    def test_get_repo_path(self, tmp_path):
        """测试获取仓库路径"""
        manager = GitRepositoryManager(tmp_path)
        
        repo_path = manager.get_repo_path("microsoft", "TypeScript", "main")
        
        assert repo_path == tmp_path / "microsoft" / "TypeScript_main"
    
    def test_build_clone_url_with_token(self, tmp_path):
        """测试构建克隆 URL（公开仓库）"""
        manager = GitRepositoryManager(tmp_path)
        
        url = manager._build_clone_url("owner", "repo")
        
        assert url == "https://github.com/owner/repo.git"
    
    def test_build_clone_url_without_token(self, tmp_path):
        """测试构建克隆 URL（公开仓库）- 别名测试"""
        manager = GitRepositoryManager(tmp_path)
        
        url = manager._build_clone_url("owner", "repo")
        
        assert url == "https://github.com/owner/repo.git"
    
    @patch('subprocess.run')
    def test_clone_repository_success(self, mock_run, tmp_path):
        """测试克隆仓库成功"""
        # Mock git --version 和 git clone
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.30.0"
        mock_run.return_value = mock_result
        
        manager = GitRepositoryManager(tmp_path)
        
        repo_path = tmp_path / "microsoft" / "TypeScript_main"
        clone_url = "https://github.com/microsoft/TypeScript.git"
        
        manager._clone_repository(clone_url, repo_path, "main")
        
        # 验证 git clone 被调用（__init__ 会先调用 git --version，然后是 git clone）
        assert mock_run.call_count == 2  # git --version + git clone
        # 检查最后一次调用是 git clone
        last_call_args = mock_run.call_args_list[-1]
        assert last_call_args[0][0][0] == 'git'
        assert last_call_args[0][0][1] == 'clone'
        assert '--branch' in last_call_args[0][0]
        assert 'main' in last_call_args[0][0]
    
    @patch('subprocess.run')
    def test_clone_repository_failure(self, mock_run, tmp_path):
        """测试克隆仓库失败"""
        manager = GitRepositoryManager(tmp_path)
        
        # Mock git clone 失败
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "fatal: repository not found"
        mock_run.return_value = mock_result
        
        repo_path = tmp_path / "owner" / "repo_main"
        clone_url = "https://github.com/owner/repo.git"
        
        with pytest.raises(RuntimeError, match="git clone 失败"):
            manager._clone_repository(clone_url, repo_path, "main")
    
    @patch('subprocess.run')
    def test_update_repository_success(self, mock_run, tmp_path):
        """测试更新仓库成功"""
        # Mock git --version, git checkout 和 git pull
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Already up to date"
        mock_run.return_value = mock_result
        
        manager = GitRepositoryManager(tmp_path)
        
        # 创建假的仓库目录
        repo_path = tmp_path / "owner" / "repo_main"
        repo_path.mkdir(parents=True)
        
        manager._update_repository(repo_path, "main")
        
        # 验证 git checkout 和 git pull 被调用（__init__ 会先调用 git --version）
        assert mock_run.call_count == 3  # git --version + git checkout + git pull
    
    @patch('subprocess.run')
    def test_get_current_commit_sha(self, mock_run, tmp_path):
        """测试获取当前 commit SHA"""
        manager = GitRepositoryManager(tmp_path)
        
        # Mock git rev-parse 返回
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "abc123def456abc123def456abc123def456ab12\n"
        mock_run.return_value = mock_result
        
        repo_path = tmp_path / "owner" / "repo_main"
        repo_path.mkdir(parents=True)
        
        commit_sha = manager.get_current_commit_sha(repo_path)
        
        assert commit_sha == "abc123def456abc123def456abc123def456ab12"
        assert len(commit_sha) == 40
    
    @patch('subprocess.run')
    def test_get_current_commit_sha_invalid(self, mock_run, tmp_path):
        """测试获取无效的 commit SHA"""
        manager = GitRepositoryManager(tmp_path)
        
        # Mock 返回无效的 SHA
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "invalid_sha\n"
        mock_run.return_value = mock_result
        
        repo_path = tmp_path / "owner" / "repo_main"
        repo_path.mkdir(parents=True)
        
        with pytest.raises(RuntimeError, match="无效的 commit SHA"):
            manager.get_current_commit_sha(repo_path)
    
    @patch('subprocess.run')
    def test_clone_or_update_first_time(self, mock_run, tmp_path):
        """测试首次克隆"""
        manager = GitRepositoryManager(tmp_path)
        
        # Mock git clone 和 git rev-parse
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "abc123def456abc123def456abc123def456ab12\n"
        mock_run.return_value = mock_result
        
        repo_path, commit_sha = manager.clone_or_update(
            "owner", "repo", "main"
        )
        
        assert repo_path == tmp_path / "owner" / "repo_main"
        assert len(commit_sha) == 40
        assert mock_run.call_count >= 2  # clone + rev-parse
    
    @patch('subprocess.run')
    def test_clone_or_update_existing(self, mock_run, tmp_path):
        """测试更新已存在的仓库"""
        # Mock git --version, checkout, pull 和 rev-parse
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "abc123def456abc123def456abc123def456ab12\n"
        mock_run.return_value = mock_result
        
        manager = GitRepositoryManager(tmp_path)
        
        # 创建假的仓库目录
        repo_path = tmp_path / "owner" / "repo_main"
        repo_path.mkdir(parents=True)
        
        returned_path, commit_sha = manager.clone_or_update(
            "owner", "repo", "main"
        )
        
        assert returned_path == repo_path
        assert len(commit_sha) == 40
        # git --version + checkout + pull + rev-parse
        assert mock_run.call_count == 4
    
    def test_cleanup_repo(self, tmp_path):
        """测试清理仓库"""
        manager = GitRepositoryManager(tmp_path)
        
        # 创建假的仓库目录
        repo_path = tmp_path / "owner" / "repo_main"
        repo_path.mkdir(parents=True)
        (repo_path / "test.txt").write_text("test")
        
        assert repo_path.exists()
        
        manager.cleanup_repo("owner", "repo", "main")
        
        assert not repo_path.exists()
    
    def test_cleanup_repo_not_exists(self, tmp_path):
        """测试清理不存在的仓库"""
        manager = GitRepositoryManager(tmp_path)
        
        # 不应该抛出异常
        manager.cleanup_repo("owner", "repo", "main")
    
    @patch('subprocess.run')
    def test_check_git_available(self, mock_run, tmp_path):
        """测试检查 git 是否可用"""
        manager = GitRepositoryManager.__new__(GitRepositoryManager)
        manager.repos_base_path = tmp_path
        
        # Mock git --version 成功
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.30.0"
        mock_run.return_value = mock_result
        
        result = manager._check_git_available()
        
        assert result is True
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_check_git_not_available(self, mock_run, tmp_path):
        """测试 git 不可用"""
        manager = GitRepositoryManager.__new__(GitRepositoryManager)
        manager.repos_base_path = tmp_path
        
        # Mock git 命令不存在
        mock_run.side_effect = FileNotFoundError()
        
        result = manager._check_git_available()
        
        assert result is False

