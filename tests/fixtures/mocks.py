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


class MockGitLoader:
    """统一的GitLoader Mock"""
    
    def __init__(self, documents=None):
        self.documents = documents or []
        self.load = Mock(return_value=self.documents)


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
    'github_loader': 'src.infrastructure.data_loader.source.github',
    'github_source': 'src.infrastructure.data_loader.source.github',
    'git_repository_manager': 'src.infrastructure.git.manager',
    'git_loader': 'langchain_community.document_loaders.git',  # 外部依赖
    
    # Data loader 相关
    'data_loader': 'src.infrastructure.data_loader',
    'document_parser': 'src.infrastructure.data_loader.parser',
    
    # Embedding 相关
    'embedding': 'src.infrastructure.embeddings',
    'local_embedding': 'src.infrastructure.embeddings.local_embedding',
    'api_embedding': 'src.infrastructure.embeddings.hf_inference_embedding',
    
    # LLM 相关
    'llm': 'src.infrastructure.llms',
    'deepseek': 'src.infrastructure.llms.reasoning',
    
    # Indexer 相关
    'indexer': 'src.infrastructure.indexer',
    'index_manager': 'src.infrastructure.indexer.core.manager',
}


def get_module_path(module_name: str) -> str:
    """获取模块路径（适配重构）"""
    return MODULE_PATH_MAP.get(module_name, module_name)


# ==================== Patch 工具函数 ====================

def patch_github_loader(mocker, mock_git_manager=None, mock_git_loader=None):
    """统一的GitHub loader patch工具"""
    if mock_git_manager is None:
        mock_git_manager = MockGitRepositoryManager()
    
    if mock_git_loader is None:
        mock_git_loader = MockGitLoader()
    
    # Patch GitRepositoryManager
    git_manager_path = get_module_path('git_repository_manager')
    mocker.patch(f'{git_manager_path}.GitRepositoryManager', return_value=mock_git_manager)
    
    # Patch GitLoader（如果需要）
    git_loader_path = get_module_path('git_loader')
    try:
        mocker.patch(f'{git_loader_path}.GitLoader', return_value=mock_git_loader)
    except AttributeError:
        # 如果路径不存在，跳过
        pass
    
    return mock_git_manager, mock_git_loader


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
