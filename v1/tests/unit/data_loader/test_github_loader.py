"""
GitHub 加载功能测试

测试从 GitHub 仓库加载文档的功能。
项目使用自研的 GitRepositoryManager + os.walk 实现，不依赖 langchain。
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from backend.infrastructure.data_loader import load_documents_from_github
from backend.infrastructure.data_loader.github_preflight import PreflightResult


@pytest.fixture
def mock_git_manager():
    """创建 GitRepositoryManager 的 mock"""
    manager = Mock()
    manager.clone_or_update = Mock()
    return manager


@pytest.fixture
def mock_preflight_success():
    """创建成功的预检结果 mock"""
    return PreflightResult(
        success=True,
        exists=True,
        is_private=False,
        size_kb=1024,
        default_branch="main"
    )


@pytest.mark.fast
class TestLoadDocumentsFromGithub:
    """测试GitHub加载功能"""
    
    def test_load_repository_success(self, mock_git_manager, mock_preflight_success):
        """测试成功加载公开仓库"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "testrepo"
            repo_path.mkdir()
            (repo_path / "README.md").write_text("# Test Repository\nContent", encoding='utf-8')
            
            mock_git_manager.clone_or_update.return_value = (repo_path, "abc123def")
            
            with patch(
                'backend.infrastructure.data_loader.source.github.GitRepositoryManager',
                return_value=mock_git_manager
            ), patch(
                'backend.infrastructure.data_loader.github_preflight.check_repository',
                return_value=mock_preflight_success
            ):
                docs = load_documents_from_github("testowner", "testrepo", "main", show_progress=False)
            
            # 验证调用了 clone_or_update
            mock_git_manager.clone_or_update.assert_called_once()
            
            # 验证返回的文档
            assert len(docs) >= 1
            doc = docs[0]
            assert doc.metadata['source_type'] == 'github'
            assert doc.metadata['repository'] == 'testowner/testrepo'
            assert doc.metadata['branch'] == 'main'
            assert 'url' in doc.metadata
    
    def test_load_repository_with_subdirectories(self, mock_git_manager, mock_preflight_success):
        """测试加载包含子目录的仓库"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "repo"
            repo_path.mkdir()
            
            # 创建子目录和文件
            (repo_path / "docs").mkdir()
            (repo_path / "docs" / "guide.md").write_text("Guide content", encoding='utf-8')
            (repo_path / "src").mkdir()
            (repo_path / "src" / "main.py").write_text("print('hello')", encoding='utf-8')
            
            mock_git_manager.clone_or_update.return_value = (repo_path, "abc123")
            
            with patch(
                'backend.infrastructure.data_loader.source.github.GitRepositoryManager',
                return_value=mock_git_manager
            ), patch(
                'backend.infrastructure.data_loader.github_preflight.check_repository',
                return_value=mock_preflight_success
            ):
                docs = load_documents_from_github("owner", "repo", show_progress=False)
            
            # 应该找到两个文件
            assert len(docs) == 2
    
    def test_load_repository_default_branch(self, mock_git_manager, mock_preflight_success):
        """测试默认分支（main）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "repo"
            repo_path.mkdir()
            (repo_path / "file.md").write_text("Content", encoding='utf-8')
            
            mock_git_manager.clone_or_update.return_value = (repo_path, "abc123")
            
            with patch(
                'backend.infrastructure.data_loader.source.github.GitRepositoryManager',
                return_value=mock_git_manager
            ), patch(
                'backend.infrastructure.data_loader.github_preflight.check_repository',
                return_value=mock_preflight_success
            ):
                docs = load_documents_from_github("owner", "repo", branch=None, show_progress=False)
            
            assert len(docs) >= 1
            # 默认分支应该是 main
            assert docs[0].metadata['branch'] == 'main'
    
    def test_git_operation_failure(self, mock_git_manager, mock_preflight_success):
        """测试 Git 操作失败时返回空列表"""
        mock_git_manager.clone_or_update.side_effect = RuntimeError("Git 操作失败")
        
        with patch(
            'backend.infrastructure.data_loader.source.github.GitRepositoryManager',
            return_value=mock_git_manager
        ), patch(
            'backend.infrastructure.data_loader.github_preflight.check_repository',
            return_value=mock_preflight_success
        ):
            docs = load_documents_from_github("owner", "repo", show_progress=False)
        
        assert len(docs) == 0
    
    def test_load_repository_empty(self, mock_git_manager, mock_preflight_success):
        """测试空仓库（无文档）"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "empty_repo"
            repo_path.mkdir()
            # 空目录，不创建任何文件
            
            mock_git_manager.clone_or_update.return_value = (repo_path, "abc123")
            
            with patch(
                'backend.infrastructure.data_loader.source.github.GitRepositoryManager',
                return_value=mock_git_manager
            ), patch(
                'backend.infrastructure.data_loader.github_preflight.check_repository',
                return_value=mock_preflight_success
            ):
                docs = load_documents_from_github("owner", "repo", show_progress=False)
            
            assert len(docs) == 0
    
    def test_load_repository_with_cleaning(self, mock_git_manager, mock_preflight_success):
        """测试加载时清理文本"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "repo"
            repo_path.mkdir()
            (repo_path / "file.md").write_text("Content    with    spaces\n\n\n\n", encoding='utf-8')
            
            mock_git_manager.clone_or_update.return_value = (repo_path, "abc123")
            
            with patch(
                'backend.infrastructure.data_loader.source.github.GitRepositoryManager',
                return_value=mock_git_manager
            ), patch(
                'backend.infrastructure.data_loader.github_preflight.check_repository',
                return_value=mock_preflight_success
            ):
                docs = load_documents_from_github("owner", "repo", clean=True, show_progress=False)
            
            # 验证返回了文档
            assert len(docs) >= 1
            # 验证文本被清理
            assert "    " not in docs[0].text
    
    def test_load_repository_git_manager_unavailable(self, mock_preflight_success):
        """测试 GitRepositoryManager 不可用时的处理"""
        with patch(
            'backend.infrastructure.data_loader.source.github.GitRepositoryManager',
            None
        ), patch(
            'backend.infrastructure.data_loader.github_preflight.check_repository',
            return_value=mock_preflight_success
        ):
            docs = load_documents_from_github("owner", "repo", show_progress=False)
        
        assert len(docs) == 0
    
    def test_load_repository_with_extension_filter(self, mock_git_manager, mock_preflight_success):
        """测试使用扩展名过滤器"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "repo"
            repo_path.mkdir()
            (repo_path / "code.py").write_text("print('hello')", encoding='utf-8')
            (repo_path / "readme.md").write_text("# Readme", encoding='utf-8')
            (repo_path / "data.json").write_text("{}", encoding='utf-8')
            
            mock_git_manager.clone_or_update.return_value = (repo_path, "abc123")
            
            with patch(
                'backend.infrastructure.data_loader.source.github.GitRepositoryManager',
                return_value=mock_git_manager
            ), patch(
                'backend.infrastructure.data_loader.github_preflight.check_repository',
                return_value=mock_preflight_success
            ):
                # 只加载 .py 文件
                docs = load_documents_from_github(
                    "owner", "repo",
                    filter_file_extensions=[".py"],
                    show_progress=False
                )
            
            assert len(docs) == 1
            assert docs[0].metadata['file_name'] == 'code.py'
    
    def test_load_repository_excludes_git_directory(self, mock_git_manager, mock_preflight_success):
        """测试自动排除 .git 目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "repo"
            repo_path.mkdir()
            (repo_path / "file.md").write_text("Content", encoding='utf-8')
            
            # 创建 .git 目录（模拟 git 仓库）
            git_dir = repo_path / ".git"
            git_dir.mkdir()
            (git_dir / "config").write_text("[core]", encoding='utf-8')
            
            mock_git_manager.clone_or_update.return_value = (repo_path, "abc123")
            
            with patch(
                'backend.infrastructure.data_loader.source.github.GitRepositoryManager',
                return_value=mock_git_manager
            ), patch(
                'backend.infrastructure.data_loader.github_preflight.check_repository',
                return_value=mock_preflight_success
            ):
                docs = load_documents_from_github("owner", "repo", show_progress=False)
            
            # 只应该有 file.md，不包含 .git 目录下的文件
            assert len(docs) == 1
            assert docs[0].metadata['file_name'] == 'file.md'
