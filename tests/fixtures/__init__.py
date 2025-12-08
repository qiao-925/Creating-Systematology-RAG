"""
测试 Fixtures 模块

按功能域组织的共享 fixtures，提升可维护性和可读性。

pytest 会自动发现此目录下的所有 fixtures，无需手动导入。
"""

__all__ = [
    # 数据 fixtures
    'sample_markdown_file',
    'sample_markdown_dir',
    'sample_documents',
    'temp_data_dir',
    # 索引 fixtures
    'temp_vector_store',
    'prepared_index_manager',
    # GitHub fixtures
    'github_test_repo',
    'github_test_repo_path',
    'github_test_metadata_manager',
    'github_test_index_manager',
    'github_prepared_index_manager',
    # Embedding fixtures
    'mock_embedding',
    # LLM fixtures
    'mock_openai_response',
    'mock_llm',
    # Mock 工具
    'MockGitRepositoryManager',
    'MockGitLoader',
    'MockEmbedding',
    'MockLLM',
    'patch_github_loader',
]
