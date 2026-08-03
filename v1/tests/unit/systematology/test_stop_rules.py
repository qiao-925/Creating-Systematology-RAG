"""Unit tests: stop_rules.py — saturation detection for retrieval pipeline."""

from __future__ import annotations

import pytest
from llama_index.core import Document

from backend.core.input.stop_rules import _jaccard_similarity, check_saturation, get_saturation_stats


# =====================================================================
# Jaccard Similarity Tests
# =====================================================================

class TestJaccardSimilarity:
    def test_identical_texts(self):
        assert _jaccard_similarity("hello world", "hello world") == 1.0

    def test_completely_different_texts(self):
        sim = _jaccard_similarity("abc", "xyz")
        assert sim < 0.3

    def test_partial_overlap(self):
        sim = _jaccard_similarity("housing demand analysis", "housing demand forecast")
        assert sim > 0.3  # "housing demand" trigrams overlap

    def test_empty_strings_both(self):
        assert _jaccard_similarity("", "") == 1.0

    def test_one_empty_one_nonempty(self):
        assert _jaccard_similarity("hello", "") == 0.0

    def test_short_string_less_than_ngram_size(self):
        # "ab" has 0 trigrams
        sim = _jaccard_similarity("ab", "ab")
        assert sim == 1.0  # both have empty ngram sets → 1.0

    def test_case_insensitive(self):
        sim = _jaccard_similarity("Hello World", "hello world")
        assert sim == 1.0

    def test_custom_ngram_size(self):
        sim = _jaccard_similarity("hello", "hallo", ngram_size=2)
        assert sim > 0.0  # "he" vs "ha" differ but others overlap


# =====================================================================
# check_saturation Tests
# =====================================================================

class TestCheckSaturation:
    def test_too_few_documents(self):
        docs = [Document(text="doc1"), Document(text="doc2")]
        assert check_saturation(docs, window_size=2) is False

    def test_exactly_window_plus_one_docs(self):
        docs = [
            Document(text="system science studies general laws"),
            Document(text="system science studies general laws"),
            Document(text="system science studies general laws"),
        ]
        # All 3 docs are identical, so the recent ones (last 2) are similar to prior (first 1)
        result = check_saturation(docs, threshold=0.5, window_size=2)
        assert result is True

    def test_diverse_documents_not_saturated(self):
        docs = [
            Document(text="system science studies general laws of systems"),
            Document(text="interdisciplinary studies across multiple domains"),
            Document(text="applied mathematics in engineering design"),
            Document(text="history of ancient civilizations in mesopotamia"),
            Document(text="quantum mechanics and particle physics theories"),
        ]
        assert check_saturation(docs, threshold=0.9, window_size=3) is False

    def test_empty_text_documents(self):
        docs = [
            Document(text="hello world"),
            Document(text=""),
            Document(text=""),
            Document(text=""),
        ]
        # recent docs are empty → no text to compare → not saturated
        assert check_saturation(docs, window_size=3) is False

    def test_no_prior_documents(self):
        # Only recent docs, no prior to compare against
        docs = [Document(text="a")] * 3
        result = check_saturation(docs, window_size=3)
        assert result is False  # len(docs)=3 < window_size+1=4 → False

    def test_zero_window_size(self):
        docs = [Document(text="a"), Document(text="b")]
        # window_size=0: len(docs) < 0+1=1 → False
        assert check_saturation(docs, window_size=0) is False


# =====================================================================
# get_saturation_stats Tests
# =====================================================================

class TestGetSaturationStats:
    def test_single_document(self):
        stats = get_saturation_stats([Document(text="hello")])
        assert stats["avg_similarity"] == 0.0
        assert stats["unique_ratio"] == 1.0
        assert stats["count"] == 1.0

    def test_two_identical_documents(self):
        docs = [Document(text="hello world"), Document(text="hello world")]
        stats = get_saturation_stats(docs, window_size=1)
        assert stats["count"] == 2.0
        assert stats["avg_similarity"] > 0.0

    def test_multiple_documents(self):
        docs = [
            Document(text="aaa bbb ccc"),
            Document(text="aaa bbb ccc"),
            Document(text="xxx yyy zzz"),
            Document(text="aaa bbb ccc"),
        ]
        stats = get_saturation_stats(docs, window_size=2)
        assert stats["count"] == 4.0
        assert 0.0 <= stats["avg_similarity"] <= 1.0
        assert 0.0 <= stats["unique_ratio"] <= 1.0

    def test_empty_document_list(self):
        stats = get_saturation_stats([])
        assert stats["avg_similarity"] == 0.0
        assert stats["unique_ratio"] == 1.0
        assert stats["count"] == 0.0
