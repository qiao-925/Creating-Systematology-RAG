"""
GitHub 同步模块单元测试
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from llama_index.core.schema import Document as LlamaDocument

from backend.infrastructure.data_loader.github_sync.file_change import FileChange
from backend.infrastructure.data_loader.github_sync.manager import GitHubSyncManager


@pytest.mark.fast
class TestFileChange:
    """FileChange 测试"""
    
    def test_file_change_creation(self):
        """测试创建 FileChange 对象"""
        change = FileChange()
        
        assert change.added == []
        assert change.modified == []
        assert change.deleted == []
    
    def test_has_changes_no_changes(self):
        """测试无变更时返回 False"""
        change = FileChange()
        
        assert change.has_changes() is False
    
    def test_has_changes_with_added(self):
        """测试有新增文件时返回 True"""
        change = FileChange()
        change.added = ["file1.md"]
        
        assert change.has_changes() is True
    
    def test_has_changes_with_modified(self):
        """测试有修改文件时返回 True"""
        change = FileChange()
        change.modified = ["file1.md"]
        
        assert change.has_changes() is True
    
    def test_has_changes_with_deleted(self):
        """测试有删除文件时返回 True"""
        change = FileChange()
        change.deleted = ["file1.md"]
        
        assert change.has_changes() is True
    
    def test_summary(self):
        """测试变更摘要生成"""
        change = FileChange()
        change.added = ["file1.md", "file2.md"]
        change.modified = ["file3.md"]
        change.deleted = ["file4.md"]
        
        summary = change.summary()
        
        assert "新增 2 个" in summary
        assert "修改 1 个" in summary
        assert "删除 1 个" in summary
    
    def test_total_count(self):
        """测试总变更数计算"""
        change = FileChange()
        change.added = ["file1.md", "file2.md"]
        change.modified = ["file3.md"]
        change.deleted = ["file4.md", "file5.md"]
        
        assert change.total_count() == 5


@pytest.mark.fast
class TestGitHubSyncManager:
    """GitHubSyncManager 测试"""
    
    @pytest.fixture
    def sync_state_path(self, tmp_path):
        """临时同步状态文件路径"""
        return tmp_path / "sync_state.json"
    
    @pytest.fixture
    def sync_manager(self, sync_state_path):
        """创建同步管理器"""
        return GitHubSyncManager(sync_state_path)
    
    @pytest.fixture
    def sample_documents(self):
        """样例文档列表"""
        return [
            LlamaDocument(
                text="文档1内容",
                metadata={"file_path": "doc1.md"}
            ),
            LlamaDocument(
                text="文档2内容",
                metadata={"file_path": "doc2.md"}
            ),
            LlamaDocument(
                text="文档3内容",
                metadata={"file_path": "subdir/doc3.md"}
            )
        ]
    
    def test_manager_initialization(self, sync_state_path):
        """测试管理器初始化"""
        manager = GitHubSyncManager(sync_state_path)
        
        assert manager.sync_state_path == sync_state_path
        assert "version" in manager.sync_state
        assert "repositories" in manager.sync_state
    
    def test_load_sync_state_new(self, sync_state_path):
        """测试加载新的同步状态"""
        # 确保文件不存在
        if sync_state_path.exists():
            sync_state_path.unlink()
        
        manager = GitHubSyncManager(sync_state_path)
        
        assert manager.sync_state["version"] == "1.0"
        assert manager.sync_state["repositories"] == {}
    
    def test_load_sync_state_existing(self, sync_state_path):
        """测试加载现有同步状态"""
        # 创建现有状态文件
        existing_state = {
            "version": "1.0",
            "repositories": {
                "owner/repo@main": {
                    "owner": "owner",
                    "repo": "repo",
                    "branch": "main",
                    "file_count": 2
                }
            }
        }
        
        with open(sync_state_path, 'w', encoding='utf-8') as f:
            json.dump(existing_state, f)
        
        manager = GitHubSyncManager(sync_state_path)
        
        assert "owner/repo@main" in manager.sync_state["repositories"]
    
    def test_save_sync_state(self, sync_manager, sync_state_path):
        """测试保存同步状态"""
        sync_manager.sync_state["repositories"]["test/repo@main"] = {
            "owner": "test",
            "repo": "repo",
            "branch": "main"
        }
        
        sync_manager.save_sync_state()
        
        assert sync_state_path.exists()
        with open(sync_state_path, 'r', encoding='utf-8') as f:
            saved_state = json.load(f)
            assert "test/repo@main" in saved_state["repositories"]
    
    def test_get_repository_key(self, sync_manager):
        """测试生成仓库标识"""
        key = sync_manager.get_repository_key("owner", "repo", "main")
        
        assert key == "owner/repo@main"
    
    def test_has_repository(self, sync_manager):
        """测试检查仓库是否存在"""
        # 添加一个仓库
        sync_manager.sync_state["repositories"]["owner/repo@main"] = {
            "owner": "owner",
            "repo": "repo",
            "branch": "main"
        }
        
        assert sync_manager.has_repository("owner", "repo", "main") is True
        assert sync_manager.has_repository("owner", "repo", "dev") is False
    
    def test_get_repository_sync_state(self, sync_manager):
        """测试获取仓库同步状态"""
        repo_data = {
            "owner": "owner",
            "repo": "repo",
            "branch": "main",
            "file_count": 5
        }
        sync_manager.sync_state["repositories"]["owner/repo@main"] = repo_data
        
        state = sync_manager.get_repository_sync_state("owner", "repo", "main")
        
        assert state == repo_data
        assert state["file_count"] == 5
    
    def test_list_repositories(self, sync_manager):
        """测试列出所有仓库"""
        sync_manager.sync_state["repositories"]["owner1/repo1@main"] = {
            "owner": "owner1",
            "repo": "repo1",
            "branch": "main",
            "file_count": 3
        }
        sync_manager.sync_state["repositories"]["owner2/repo2@dev"] = {
            "owner": "owner2",
            "repo": "repo2",
            "branch": "dev",
            "file_count": 5
        }
        
        repos = sync_manager.list_repositories()
        
        assert len(repos) == 2
        assert any(r["owner"] == "owner1" for r in repos)
        assert any(r["owner"] == "owner2" for r in repos)
    
    @patch('backend.infrastructure.data_loader.github_sync.manager.compute_hash')
    def test_detect_changes_first_index(self, mock_compute_hash, sync_manager, sample_documents):
        """测试首次索引时的变更检测"""
        mock_compute_hash.return_value = "hash123"
        
        changes = sync_manager.detect_changes(
            "owner", "repo", "main", sample_documents
        )
        
        assert len(changes.added) == 3
        assert len(changes.modified) == 0
        assert len(changes.deleted) == 0
    
    @patch('backend.infrastructure.data_loader.github_sync.manager.compute_hash')
    def test_detect_changes_added(self, mock_compute_hash, sync_manager, sample_documents):
        """测试检测新增文件"""
        mock_compute_hash.return_value = "hash123"
        
        # 先记录一个文件
        sync_manager.sync_state["repositories"]["owner/repo@main"] = {
            "owner": "owner",
            "repo": "repo",
            "branch": "main",
            "files": {
                "old_file.md": {"hash": "old_hash"}
            }
        }
        
        # 检测变更（新文档不包含 old_file.md）
        changes = sync_manager.detect_changes(
            "owner", "repo", "main", sample_documents
        )
        
        assert len(changes.added) == 3  # 所有新文档都是新增
        assert "old_file.md" in changes.deleted
    
    @patch('backend.infrastructure.data_loader.github_sync.manager.compute_hash')
    def test_detect_changes_modified(self, mock_compute_hash, sync_manager, sample_documents):
        """测试检测修改文件"""
        # 设置不同的哈希值
        def hash_side_effect(text):
            if "文档1" in text:
                return "new_hash1"
            return "hash123"
        
        mock_compute_hash.side_effect = hash_side_effect
        
        # 先记录旧状态
        sync_manager.sync_state["repositories"]["owner/repo@main"] = {
            "owner": "owner",
            "repo": "repo",
            "branch": "main",
            "files": {
                "doc1.md": {"hash": "old_hash1"},
                "doc2.md": {"hash": "hash123"}
            }
        }
        
        changes = sync_manager.detect_changes(
            "owner", "repo", "main", sample_documents
        )
        
        assert "doc1.md" in changes.modified
        assert "doc2.md" not in changes.modified
    
    @patch('backend.infrastructure.data_loader.github_sync.manager.compute_hash')
    def test_detect_changes_deleted(self, mock_compute_hash, sync_manager, sample_documents):
        """测试检测删除文件"""
        mock_compute_hash.return_value = "hash123"
        
        # 先记录多个文件
        sync_manager.sync_state["repositories"]["owner/repo@main"] = {
            "owner": "owner",
            "repo": "repo",
            "branch": "main",
            "files": {
                "doc1.md": {"hash": "hash123"},
                "deleted_file.md": {"hash": "hash456"},
                "another_deleted.md": {"hash": "hash789"}
            }
        }
        
        # 检测变更（新文档只包含 doc1.md）
        changes = sync_manager.detect_changes(
            "owner", "repo", "main", sample_documents
        )
        
        assert "deleted_file.md" in changes.deleted
        assert "another_deleted.md" in changes.deleted
    
    @patch('backend.infrastructure.data_loader.github_sync.manager.compute_hash')
    def test_update_repository_sync_state(self, mock_compute_hash, sync_manager, sample_documents):
        """测试更新仓库同步状态"""
        mock_compute_hash.return_value = "hash123"
        
        sync_manager.update_repository_sync_state(
            "owner", "repo", "main", sample_documents, commit_sha="abc123"
        )
        
        repo_state = sync_manager.get_repository_sync_state("owner", "repo", "main")
        assert repo_state is not None
        assert repo_state["file_count"] == 3
        assert repo_state["last_commit_sha"] == "abc123"
        assert "doc1.md" in repo_state["files"]
    
    @patch('backend.infrastructure.data_loader.github_sync.manager.compute_hash')
    def test_update_file_vector_ids(self, mock_compute_hash, sync_manager, sample_documents):
        """测试更新文件向量ID"""
        mock_compute_hash.return_value = "hash123"
        
        # 先更新仓库状态
        sync_manager.update_repository_sync_state(
            "owner", "repo", "main", sample_documents
        )
        
        # 更新向量ID
        sync_manager.update_file_vector_ids(
            "owner", "repo", "main", "doc1.md", ["vec_id_1", "vec_id_2"]
        )
        
        vector_ids = sync_manager.get_file_vector_ids(
            "owner", "repo", "main", "doc1.md"
        )
        
        assert vector_ids == ["vec_id_1", "vec_id_2"]
    
    @patch('backend.infrastructure.data_loader.github_sync.manager.compute_hash')
    def test_get_file_vector_ids(self, mock_compute_hash, sync_manager, sample_documents):
        """测试获取文件向量ID"""
        mock_compute_hash.return_value = "hash123"
        
        # 先更新仓库状态并设置向量ID
        sync_manager.update_repository_sync_state(
            "owner", "repo", "main", sample_documents,
            vector_ids_map={"doc1.md": ["vec1", "vec2"]}
        )
        
        vector_ids = sync_manager.get_file_vector_ids(
            "owner", "repo", "main", "doc1.md"
        )
        
        assert vector_ids == ["vec1", "vec2"]
    
    @patch('backend.infrastructure.data_loader.github_sync.manager.compute_hash')
    def test_remove_repository(self, mock_compute_hash, sync_manager, sample_documents):
        """测试移除仓库"""
        mock_compute_hash.return_value = "hash123"
        
        # 先添加仓库
        sync_manager.update_repository_sync_state(
            "owner", "repo", "main", sample_documents
        )
        
        assert sync_manager.has_repository("owner", "repo", "main") is True
        
        # 移除仓库
        sync_manager.remove_repository("owner", "repo", "main")
        
        assert sync_manager.has_repository("owner", "repo", "main") is False
    
    @patch('backend.infrastructure.data_loader.github_sync.manager.compute_hash')
    def test_get_documents_by_change(self, mock_compute_hash, sync_manager, sample_documents):
        """测试根据变更分组文档"""
        mock_compute_hash.return_value = "hash123"
        
        # 创建变更记录
        changes = FileChange()
        changes.added = ["doc1.md"]
        changes.modified = ["doc2.md"]
        changes.deleted = ["deleted_file.md"]
        
        added_docs, modified_docs, deleted_paths = sync_manager.get_documents_by_change(
            sample_documents, changes
        )
        
        assert len(added_docs) == 1
        assert len(modified_docs) == 1
        assert len(deleted_paths) == 1
        assert deleted_paths[0] == "deleted_file.md"
