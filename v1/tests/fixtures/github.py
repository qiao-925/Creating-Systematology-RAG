"""
GitHub 相关 Fixtures

提供 GitHub 测试相关的 fixtures。
"""

import os
import pytest
from pathlib import Path


@pytest.fixture(scope="module")  # 优化：module 级别
def github_test_repo():
    """GitHub测试仓库配置"""
    return {
        "owner": os.getenv("TEST_GITHUB_OWNER", "octocat"),
        "repo": os.getenv("TEST_GITHUB_REPO", "Hello-World"),
        "branch": os.getenv("TEST_GITHUB_BRANCH", "main")
    }


@pytest.fixture(scope="function")
def github_test_repo_path(tmp_path):
    """GitHub测试仓库本地路径"""
    repos_path = tmp_path / "github_repos"
    repos_path.mkdir(parents=True, exist_ok=True)
    return repos_path


@pytest.fixture(scope="function")
def github_test_sync_manager(tmp_path):
    """测试用的GitHubSyncManager"""
    from backend.infrastructure.data_loader.github_sync.manager import GitHubSyncManager
    
    sync_state_path = tmp_path / "test_sync_state.json"
    manager = GitHubSyncManager(sync_state_path)
    
    yield manager
    
    # 清理：删除测试同步状态文件
    try:
        if sync_state_path.exists():
            sync_state_path.unlink()
    except Exception:
        pass


@pytest.fixture(scope="module")  # 优化：module 级别
def github_test_index_manager(tmp_path_factory):
    """专门用于GitHub测试的IndexManager"""
    from backend.infrastructure.indexer import IndexManager
    
    # 使用 tmp_path_factory 创建 module 级别的临时目录
    temp_vector_store = tmp_path_factory.mktemp("github_test_vector_store")
    
    manager = IndexManager(
        collection_name="github_e2e_test",
        persist_dir=temp_vector_store
    )
    
    yield manager
    
    # 清理
    try:
        manager.clear_index()
    except Exception:
        pass


@pytest.fixture(scope="function")
def github_prepared_index_manager(
    github_test_index_manager,
    github_test_sync_manager
):
    """准备好的GitHub索引管理器（已构建索引）"""
    from backend.infrastructure.data_loader import load_documents_from_github
    
    owner = os.getenv("TEST_GITHUB_OWNER", "octocat")
    repo = os.getenv("TEST_GITHUB_REPO", "Hello-World")
    branch = os.getenv("TEST_GITHUB_BRANCH", "main")
    
    # 检查网络和Git可用性
    try:
        import subprocess
        subprocess.run(['git', '--version'], capture_output=True, timeout=2, check=True)
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        pytest.skip("Git不可用，跳过GitHub测试")
    
    # 加载文档并构建索引
    try:
        documents = load_documents_from_github(
            owner=owner,
            repo=repo,
            branch=branch,
            show_progress=False
        )
        
        if len(documents) == 0:
            pytest.skip(f"无法从 {owner}/{repo}@{branch} 加载文档，可能网络不可用")
        
        # 构建索引
        github_test_index_manager.build_index(documents, show_progress=False)
        
    except Exception as e:
        pytest.skip(f"GitHub测试准备失败: {e}")
    
    yield github_test_index_manager


# ==================== GitHub Sync Fixtures ====================

@pytest.fixture
def sample_sync_state():
    """样例同步状态数据"""
    return {
        "version": "1.0",
        "repositories": {
            "owner/repo@main": {
                "owner": "owner",
                "repo": "repo",
                "branch": "main",
                "last_commit_sha": "abc123def456",
                "last_indexed_at": "2025-01-01T00:00:00",
                "file_count": 3,
                "files": {
                    "doc1.md": {
                        "hash": "hash1",
                        "size": 100,
                        "last_modified": "2025-01-01T00:00:00",
                        "vector_ids": ["vec1", "vec2"]
                    },
                    "doc2.md": {
                        "hash": "hash2",
                        "size": 200,
                        "last_modified": "2025-01-01T00:00:00",
                        "vector_ids": ["vec3"]
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_file_changes():
    """样例文件变更"""
    from backend.infrastructure.data_loader.github_sync.file_change import FileChange
    
    changes = FileChange()
    changes.added = ["new_file.md"]
    changes.modified = ["doc1.md"]
    changes.deleted = ["old_file.md"]
    
    return changes
