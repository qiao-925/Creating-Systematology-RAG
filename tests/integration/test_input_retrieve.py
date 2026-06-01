"""Integration tests: input/retrieve.py — source-tiered document retrieval."""

from __future__ import annotations

import pytest
from llama_index.core import Document

from backend.core.input.retrieve import (
    _get_source_tier,
    _content_hash,
    source_tiered_retrieve,
    SOURCE_TIERS,
)


# =====================================================================
# _get_source_tier Tests
# =====================================================================

class TestGetSourceTier:
    def test_academic_tier(self):
        doc = Document(text="test", metadata={"source": "academic_journal"})
        assert _get_source_tier(doc) == 1

    def test_government_tier(self):
        doc = Document(text="test", metadata={"source": "government_report"})
        assert _get_source_tier(doc) == 2

    def test_news_tier(self):
        doc = Document(text="test", metadata={"source": "news_outlet"})
        assert _get_source_tier(doc) == 4

    def test_blog_tier(self):
        doc = Document(text="test", metadata={"source": "blog_post"})
        assert _get_source_tier(doc) == 5

    def test_unknown_default(self):
        doc = Document(text="test", metadata={})
        assert _get_source_tier(doc) == SOURCE_TIERS["unknown"]

    def test_uses_source_type_fallback(self):
        doc = Document(text="test", metadata={"source_type": "arxiv"})
        assert _get_source_tier(doc) == 1


# =====================================================================
# _content_hash Tests
# =====================================================================

class TestContentHash:
    def test_same_content_same_hash(self):
        a = Document(text="hello world")
        b = Document(text="hello world")
        assert _content_hash(a) == _content_hash(b)

    def test_different_content_different_hash(self):
        a = Document(text="hello")
        b = Document(text="world")
        assert _content_hash(a) != _content_hash(b)

    def test_empty_text(self):
        doc = Document(text="")
        assert _content_hash(doc) == ""


# =====================================================================
# source_tiered_retrieve Tests
# =====================================================================

class TestSourceTieredRetrieve:
    def test_ranks_by_source_tier(self):
        from unittest.mock import MagicMock

        mock_retriever = MagicMock()

        class MockNode:
            def __init__(self, text, meta):
                self.text = text
                self.metadata = meta
                self.score = 0.5

            class Node:
                def get_content(self):
                    return self.text

        # Build mock nodes with return values that capture the query
        def retrieve(query):
            if "academic" in query:
                return [
                    MagicMock(
                        node=MagicMock(
                            get_content=lambda: "academic paper about subsidies",
                            metadata={"source": "academic_journal"},
                        ),
                        score=0.9,
                    )
                ]
            return [
                MagicMock(
                    node=MagicMock(
                        get_content=lambda: "blog post about subsidies",
                        metadata={"source": "blog_post"},
                    ),
                    score=0.8,
                )
            ]

        mock_retriever.retrieve.side_effect = retrieve

        result = source_tiered_retrieve(
            queries=["academic query", "blog query"],
            retriever=mock_retriever,
            top_k=5,
        )
        assert len(result) == 2
        # Academic should come first (tier 1 vs tier 5)
        assert "academic" in result[0].text

    def test_deduplicates_by_content(self):
        from unittest.mock import MagicMock

        mock_retriever = MagicMock()

        def retrieve(query):
            return [
                MagicMock(
                    node=MagicMock(
                        get_content=lambda: "same content repeated across queries",
                        metadata={"source": "unknown"},
                    ),
                    score=0.5,
                )
            ]

        mock_retriever.retrieve.side_effect = retrieve

        result = source_tiered_retrieve(
            queries=["q1", "q2", "q3"],
            retriever=mock_retriever,
            top_k=10,
        )
        # Same content across 3 queries → deduplicated to 1
        assert len(result) == 1

    def test_respects_top_k(self):
        from unittest.mock import MagicMock

        mock_retriever = MagicMock()
        counter = 0

        def retrieve(query):
            nonlocal counter
            counter += 1
            return [
                MagicMock(
                    node=MagicMock(
                        get_content=lambda c=counter: f"document {c}",
                        metadata={"source": "unknown"},
                    ),
                    score=0.5,
                )
            ]

        mock_retriever.retrieve.side_effect = retrieve

        result = source_tiered_retrieve(
            queries=["q1", "q2", "q3"],
            retriever=mock_retriever,
            top_k=2,
        )
        assert len(result) <= 2

    def test_query_exception_is_skipped(self):
        from unittest.mock import MagicMock

        mock_retriever = MagicMock()

        call_count = 0

        def retrieve(query):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise RuntimeError("retrieval error")
            return [
                MagicMock(
                    node=MagicMock(
                        get_content=lambda: "good document",
                        metadata={"source": "academic"},
                    ),
                    score=0.5,
                )
            ]

        mock_retriever.retrieve.side_effect = retrieve

        result = source_tiered_retrieve(
            queries=["good query", "bad query", "another good query"],
            retriever=mock_retriever,
            top_k=10,
        )
        # Should still get results from queries 1 and 3
        assert len(result) > 0
