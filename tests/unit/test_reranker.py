"""
Reranker unit tests using offline test doubles.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import Mock, patch

import pytest
from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode

import backend.business.rag_engine.reranking.factory as reranker_factory
from backend.business.rag_engine.reranking.base import BaseReranker
from backend.business.rag_engine.reranking.factory import clear_reranker_cache, create_reranker
from backend.business.rag_engine.reranking.strategies.bge import BGEReranker
from backend.business.rag_engine.reranking.strategies.sentence_transformer import (
    SentenceTransformerReranker,
)


@pytest.fixture(autouse=True)
def reset_reranker_cache():
    clear_reranker_cache()
    yield
    clear_reranker_cache()


@pytest.fixture
def sample_nodes():
    nodes = []
    for i in range(5):
        node = TextNode(text=f"文档{i}的内容", metadata={"id": i})
        nodes.append(NodeWithScore(node=node, score=0.9 - i * 0.1))
    return nodes


@pytest.fixture
def mock_sentence_transformer_rerank():
    rerank_impl = Mock()
    with patch(
        "backend.business.rag_engine.reranking.strategies.sentence_transformer.SentenceTransformerRerank",
        return_value=rerank_impl,
    ) as mock_cls:
        yield mock_cls, rerank_impl


@pytest.fixture
def mock_flag_embedding_reranker():
    module = types.ModuleType("llama_index.postprocessor.flag_embedding_reranker")
    rerank_impl = Mock()
    mock_cls = Mock(return_value=rerank_impl)
    module.FlagEmbeddingReranker = mock_cls

    parent = sys.modules.get("llama_index.postprocessor") or types.ModuleType("llama_index.postprocessor")
    parent.flag_embedding_reranker = module

    with patch.dict(
        sys.modules,
        {
            "llama_index.postprocessor": parent,
            "llama_index.postprocessor.flag_embedding_reranker": module,
        },
    ):
        yield mock_cls, rerank_impl


class TestBaseReranker:
    def test_base_reranker_interface(self):
        assert hasattr(BaseReranker, "rerank")
        assert hasattr(BaseReranker, "get_reranker_name")
        assert hasattr(BaseReranker, "get_top_n")
        assert hasattr(BaseReranker, "get_llama_index_postprocessor")


class TestRerankerFactory:
    def test_create_reranker_none(self):
        assert create_reranker(reranker_type="none") is None

    def test_create_reranker_sentence_transformer(self):
        with patch.object(reranker_factory, "SentenceTransformerReranker") as mock_cls:
            instance = Mock(spec=BaseReranker)
            mock_cls.return_value = instance

            reranker = create_reranker(
                reranker_type="sentence-transformer",
                top_n=3,
                use_cache=False,
            )

        assert reranker is instance
        mock_cls.assert_called_once_with(model=None, top_n=3)

    def test_create_reranker_bge(self):
        with patch.object(reranker_factory, "BGEReranker") as mock_cls:
            instance = Mock(spec=BaseReranker)
            mock_cls.return_value = instance

            reranker = create_reranker(reranker_type="bge", top_n=5, use_cache=False)

        assert reranker is instance
        mock_cls.assert_called_once_with(model=None, top_n=5)

    def test_create_reranker_invalid_type_falls_back_to_sentence_transformer(self):
        with patch.object(reranker_factory, "SentenceTransformerReranker") as mock_cls:
            instance = Mock(spec=BaseReranker)
            mock_cls.return_value = instance

            reranker = create_reranker(reranker_type="invalid_type", use_cache=False)

        assert reranker is instance
        mock_cls.assert_called_once_with(model=None, top_n=None)

    def test_create_reranker_default_config(self, monkeypatch):
        mock_config = Mock()
        mock_config.RERANKER_TYPE = "sentence-transformer"
        monkeypatch.setattr(reranker_factory, "config", mock_config)

        with patch.object(reranker_factory, "SentenceTransformerReranker") as mock_cls:
            instance = Mock(spec=BaseReranker)
            mock_cls.return_value = instance

            reranker = create_reranker(use_cache=False)

        assert reranker is instance
        mock_cls.assert_called_once_with(model=None, top_n=None)


class TestSentenceTransformerReranker:
    def test_init(self, mock_sentence_transformer_rerank):
        mock_cls, rerank_impl = mock_sentence_transformer_rerank

        reranker = SentenceTransformerReranker(model="BAAI/bge-reranker-base", top_n=3)

        assert reranker.get_top_n() == 3
        assert reranker.get_reranker_name() == "BAAI/bge-reranker-base"
        assert reranker.get_llama_index_postprocessor() is rerank_impl
        mock_cls.assert_called_once_with(model="BAAI/bge-reranker-base", top_n=3)

    def test_rerank(self, sample_nodes, mock_sentence_transformer_rerank):
        _mock_cls, rerank_impl = mock_sentence_transformer_rerank
        rerank_impl.postprocess_nodes.return_value = sample_nodes[:3]

        reranker = SentenceTransformerReranker(top_n=3)
        query = QueryBundle(query_str="测试查询")

        reranked = reranker.rerank(sample_nodes, query)

        assert reranked == sample_nodes[:3]
        rerank_impl.postprocess_nodes.assert_called_once_with(sample_nodes, query)

    def test_get_llama_index_postprocessor(self, mock_sentence_transformer_rerank):
        _mock_cls, rerank_impl = mock_sentence_transformer_rerank

        reranker = SentenceTransformerReranker()

        assert reranker.get_llama_index_postprocessor() is rerank_impl


class TestBGEReranker:
    def test_init(self, mock_flag_embedding_reranker):
        mock_cls, rerank_impl = mock_flag_embedding_reranker

        reranker = BGEReranker(model="BAAI/bge-reranker-base", top_n=5)

        assert reranker.get_top_n() == 5
        assert reranker.get_reranker_name() == "BAAI/bge-reranker-base"
        assert reranker.get_llama_index_postprocessor() is rerank_impl
        mock_cls.assert_called_once_with(
            model="BAAI/bge-reranker-base",
            top_n=5,
            use_fp16=True,
        )

    def test_rerank(self, sample_nodes, mock_flag_embedding_reranker):
        _mock_cls, rerank_impl = mock_flag_embedding_reranker
        rerank_impl.postprocess_nodes.return_value = sample_nodes[:3]

        reranker = BGEReranker(top_n=3)
        query = QueryBundle(query_str="测试查询")

        reranked = reranker.rerank(sample_nodes, query)

        assert reranked == sample_nodes[:3]
        rerank_impl.postprocess_nodes.assert_called_once_with(sample_nodes, query)

    def test_get_llama_index_postprocessor(self, mock_flag_embedding_reranker):
        _mock_cls, rerank_impl = mock_flag_embedding_reranker

        reranker = BGEReranker()

        assert reranker.get_llama_index_postprocessor() is rerank_impl
