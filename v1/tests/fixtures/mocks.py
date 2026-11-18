"""
Mock 工具模块

提供统一的 Mock 类和工具函数，集中管理 Mock 路径。
"""

from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Optional


# ==================== Mock 类 ====================

class MockGitRepositoryManager:
    """统一的Git仓库管理器Mock"""
    
    def __init__(self, repo_path: Optional[Path] = None, commit_sha: str = None):
        self.repo_path = repo_path or Path("/tmp/repo")
        self.commit_sha = commit_sha or "abc123def456" * 5
        self.clone_or_update = Mock(return_value=(self.repo_path, self.commit_sha))
        self.clone = Mock(return_value=(self.repo_path, self.commit_sha))
        self.update = Mock(return_value=(self.repo_path, self.commit_sha))




class MockEmbedding:
    """统一的Embedding Mock"""
    
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        self.get_query_embedding = Mock(return_value=[0.1] * dimension)
        self.get_text_embeddings = Mock(return_value=[[0.1] * dimension])
        self.get_embedding_dimension = Mock(return_value=dimension)
        self.get_model_name = Mock(return_value="test-embedding")


class MockLLM:
    """统一的LLM Mock"""
    
    def __init__(self, response: str = "测试回答"):
        self.response = response
        self.complete = Mock()
        self.complete.return_value.text = response
        self.stream_complete = Mock(return_value=iter([response]))


# ==================== 路径映射配置 ====================

# 模块路径映射（适配重构后的路径）
MODULE_PATH_MAP = {
    # GitHub 相关
    'github_loader': 'backend.infrastructure.data_loader.source.github',
    'github_source': 'backend.infrastructure.data_loader.source.github',
    'git_repository_manager': 'backend.infrastructure.git.manager',
    
    # Data loader 相关
    'data_loader': 'backend.infrastructure.data_loader',
    'document_parser': 'backend.infrastructure.data_loader.parser',
    
    # Embedding 相关
    'embedding': 'backend.infrastructure.embeddings',
    'local_embedding': 'backend.infrastructure.embeddings.local_embedding',
    'api_embedding': 'backend.infrastructure.embeddings.hf_inference_embedding',
    
    # LLM 相关
    'llm': 'backend.infrastructure.llms',
    'deepseek': 'backend.infrastructure.llms.reasoning',
    
    # Indexer 相关
    'indexer': 'backend.infrastructure.indexer',
    'index_manager': 'backend.infrastructure.indexer.core.manager',
}


def get_module_path(module_name: str) -> str:
    """获取模块路径（适配重构）"""
    return MODULE_PATH_MAP.get(module_name, module_name)


# ==================== Patch 工具函数 ====================

def patch_github_loader(mocker, mock_git_manager=None):
    """统一的GitHub loader patch工具
    
    注意：项目使用自研的 GitRepositoryManager，不依赖 langchain。
    需要在使用该类的模块中 patch，而不是在定义它的模块中。
    """
    if mock_git_manager is None:
        mock_git_manager = MockGitRepositoryManager()
    
    # Patch GitRepositoryManager（在使用它的模块中 patch）
    # GitHubSource 从 backend.infrastructure.git 导入 GitRepositoryManager
    mocker.patch(
        'backend.infrastructure.data_loader.source.github.GitRepositoryManager',
        return_value=mock_git_manager
    )
    
    # 返回兼容的元组（保持向后兼容）
    return mock_git_manager, None


def patch_embedding(mocker, mock_embedding=None):
    """统一的Embedding patch工具"""
    if mock_embedding is None:
        mock_embedding = MockEmbedding()
    
    embedding_path = get_module_path('embedding')
    mocker.patch(f'{embedding_path}.BaseEmbedding', return_value=mock_embedding)
    
    return mock_embedding


def patch_llm(mocker, mock_llm=None):
    """统一的LLM patch工具"""
    if mock_llm is None:
        mock_llm = MockLLM()
    
    llm_path = get_module_path('llm')
    mocker.patch(f'{llm_path}.LLM', return_value=mock_llm)
    
    return mock_llm
