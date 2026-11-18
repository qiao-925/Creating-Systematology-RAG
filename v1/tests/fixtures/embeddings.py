"""
Embedding 相关 Fixtures

提供 Embedding 测试相关的 fixtures。
"""

import pytest


@pytest.fixture
def mock_embedding(mocker):
    """Mock Embedding 对象"""
    mock = mocker.Mock()
    mock.get_query_embedding.return_value = [0.1] * 768
    mock.get_text_embeddings.return_value = [[0.1] * 768]
    mock.get_embedding_dimension.return_value = 768
    mock.get_model_name.return_value = "test-embedding-model"
    return mock
