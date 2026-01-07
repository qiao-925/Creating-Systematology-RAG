"""
文件级别检索器单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from llama_index.core.schema import NodeWithScore, TextNode, QueryBundle

from backend.business.rag_engine.retrieval.strategies.file_level import (
    FilesViaContentRetriever,
    FilesViaMetadataRetriever,
    group_nodes_by_file,
    calculate_file_score,
    aggregate_file_chunks,
)
from backend.infrastructure.indexer import IndexManager


class TestFileLevelRetrieversUtils:
    """文件级别检索器工具函数测试"""
    
    def test_group_nodes_by_file(self):
        """测试按文件分组节点"""
        # 创建测试节点
        nodes = [
            NodeWithScore(
                node=TextNode(text="chunk1", metadata={"file_path": "file1.md"}),
                score=0.9
            ),
            NodeWithScore(
                node=TextNode(text="chunk2", metadata={"file_path": "file1.md"}),
                score=0.8
            ),
            NodeWithScore(
                node=TextNode(text="chunk3", metadata={"file_path": "file2.md"}),
                score=0.7
            ),
            NodeWithScore(
                node=TextNode(text="chunk4", metadata={}),  # 无file_path
                score=0.6
            ),
        ]
        
        file_groups = group_nodes_by_file(nodes)
        
        assert "file1.md" in file_groups
        assert "file2.md" in file_groups
        assert "unknown" in file_groups
        assert len(file_groups["file1.md"]) == 2
        assert len(file_groups["file2.md"]) == 1
        assert len(file_groups["unknown"]) == 1
    
    def test_calculate_file_score(self):
        """测试文件分数计算"""
        # 创建测试节点（已按分数排序）
        chunks = [
            NodeWithScore(node=TextNode(text="chunk1"), score=0.9),
            NodeWithScore(node=TextNode(text="chunk2"), score=0.8),
            NodeWithScore(node=TextNode(text="chunk3"), score=0.7),
        ]
        
        score = calculate_file_score(chunks, top_k_chunks=2)
        
        # 应该使用 top 2 的平均分数：(0.9 + 0.8) / 2 = 0.85
        assert score == pytest.approx(0.85, abs=0.01)
    
    def test_calculate_file_score_empty(self):
        """测试空文件分数计算"""
        score = calculate_file_score([], top_k_chunks=3)
        assert score == 0.0
    
    def test_aggregate_file_chunks(self):
        """测试文件chunks聚合"""
        # 创建文件分组
        file_groups = {
            "file1.md": [
                NodeWithScore(node=TextNode(text="chunk1"), score=0.9),
                NodeWithScore(node=TextNode(text="chunk2"), score=0.8),
            ],
            "file2.md": [
                NodeWithScore(node=TextNode(text="chunk3"), score=0.7),
                NodeWithScore(node=TextNode(text="chunk4"), score=0.6),
            ],
        }
        
        aggregated = aggregate_file_chunks(
            file_groups,
            top_k_files=2,
            top_k_per_file=1
        )
        
        # 应该返回2个文件，每个文件1个chunk
        assert len(aggregated) == 2
        # 应该按分数排序（file1的chunk1分数最高）
        assert aggregated[0].score == 0.9


class TestFilesViaContentRetriever:
    """FilesViaContentRetriever测试"""
    
    @pytest.fixture
    def mock_index_manager(self):
        """创建Mock IndexManager"""
        mock_manager = Mock(spec=IndexManager)
        mock_index = Mock()
        mock_retriever = Mock()
        
        # Mock检索结果
        mock_nodes = [
            NodeWithScore(
                node=TextNode(
                    text="系统科学是研究系统的科学",
                    metadata={"file_path": "file1.md"}
                ),
                score=0.9
            ),
            NodeWithScore(
                node=TextNode(
                    text="钱学森是系统科学的奠基人",
                    metadata={"file_path": "file1.md"}
                ),
                score=0.8
            ),
            NodeWithScore(
                node=TextNode(
                    text="系统科学的应用领域",
                    metadata={"file_path": "file2.md"}
                ),
                score=0.7
            ),
        ]
        mock_retriever.retrieve.return_value = mock_nodes
        mock_index.as_retriever.return_value = mock_retriever
        mock_manager.get_index.return_value = mock_index
        
        return mock_manager
    
    def test_files_via_content_init(self, mock_index_manager):
        """测试FilesViaContentRetriever初始化"""
        retriever = FilesViaContentRetriever(
            index_manager=mock_index_manager,
            top_k_files=5,
            top_k_per_file=3,
            similarity_top_k=50,
        )
        
        assert retriever.index_manager == mock_index_manager
        assert retriever.top_k_files == 5
        assert retriever.top_k_per_file == 3
        assert retriever.similarity_top_k == 50
    
    def test_files_via_content_retrieve_basic(self, mock_index_manager):
        """测试基础检索"""
        retriever = FilesViaContentRetriever(
            index_manager=mock_index_manager,
            top_k_files=2,
            top_k_per_file=2,
        )
        
        results = retriever.retrieve("系统科学")
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, NodeWithScore) for r in results)
    
    def test_files_via_content_retrieve_with_query_bundle(self, mock_index_manager):
        """测试使用QueryBundle检索"""
        retriever = FilesViaContentRetriever(
            index_manager=mock_index_manager,
            top_k_files=2,
            top_k_per_file=2,
        )
        
        query_bundle = QueryBundle(query_str="系统科学")
        results = retriever.retrieve(query_bundle)
        
        assert isinstance(results, list)
    
    def test_files_via_content_empty_query(self, mock_index_manager):
        """测试空查询"""
        retriever = FilesViaContentRetriever(
            index_manager=mock_index_manager,
        )
        
        results = retriever.retrieve("")
        assert results == []
        
        results = retriever.retrieve("   ")
        assert results == []
    
    def test_files_via_content_no_results(self, mock_index_manager):
        """测试无结果情况"""
        # Mock返回空结果
        mock_index = Mock()
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = []
        mock_index.as_retriever.return_value = mock_retriever
        mock_index_manager.get_index.return_value = mock_index
        
        retriever = FilesViaContentRetriever(
            index_manager=mock_index_manager,
        )
        
        results = retriever.retrieve("系统科学")
        assert results == []
    
    def test_files_via_content_top_k_limit(self, mock_index_manager):
        """测试Top-K限制"""
        retriever = FilesViaContentRetriever(
            index_manager=mock_index_manager,
            top_k_files=2,
            top_k_per_file=2,
        )
        
        results = retriever.retrieve("系统科学", top_k=3)
        
        assert len(results) <= 3


class TestFilesViaMetadataRetriever:
    """FilesViaMetadataRetriever测试"""
    
    @pytest.fixture
    def mock_index_manager(self):
        """创建Mock IndexManager"""
        mock_manager = Mock(spec=IndexManager)
        mock_index = Mock()
        mock_retriever = Mock()
        
        # Mock检索结果
        mock_nodes = [
            NodeWithScore(
                node=TextNode(
                    text="文件内容1",
                    metadata={"file_path": "system_science.md"}
                ),
                score=0.9
            ),
        ]
        mock_retriever.retrieve.return_value = mock_nodes
        mock_index.as_retriever.return_value = mock_retriever
        mock_manager.get_index.return_value = mock_index
        
        # Mock Chroma collection
        mock_collection = Mock()
        mock_collection.get.return_value = {
            'ids': ['id1', 'id2'],
            'metadatas': [
                {'file_path': 'system_science.md', 'file_name': 'system_science.md'},
                {'file_path': 'system_science.md', 'file_name': 'system_science.md'},
            ]
        }
        mock_manager.chroma_collection = mock_collection
        mock_manager._get_vector_ids_by_metadata.return_value = ['id1', 'id2']
        
        return mock_manager
    
    def test_files_via_metadata_init(self, mock_index_manager):
        """测试FilesViaMetadataRetriever初始化"""
        retriever = FilesViaMetadataRetriever(
            index_manager=mock_index_manager,
            top_k_per_file=5,
            similarity_top_k=20,
        )
        
        assert retriever.index_manager == mock_index_manager
        assert retriever.top_k_per_file == 5
        assert retriever.similarity_top_k == 20
    
    def test_extract_file_keywords(self, mock_index_manager):
        """测试文件名关键词提取"""
        retriever = FilesViaMetadataRetriever(
            index_manager=mock_index_manager,
        )
        
        # 测试包含文件扩展名的查询
        keywords = retriever._extract_file_keywords("system_science.md文件的内容")
        assert len(keywords) > 0
        assert "md" in keywords or "system_science" in keywords
        
        # 测试包含"文件"关键词的查询
        keywords = retriever._extract_file_keywords("系统科学文件的内容")
        assert len(keywords) > 0
    
    def test_match_files_by_metadata(self, mock_index_manager):
        """测试元数据匹配"""
        retriever = FilesViaMetadataRetriever(
            index_manager=mock_index_manager,
        )
        
        # Mock Chroma collection 的 get 方法
        mock_collection = Mock()
        mock_collection.get.return_value = {
            'ids': ['id1'],
            'metadatas': [
                {'file_path': 'system_science.md', 'file_name': 'system_science.md'}
            ]
        }
        mock_index_manager.chroma_collection = mock_collection
        
        keywords = ["system_science", "md"]
        matched_files = retriever._match_files_by_metadata(keywords, fuzzy_match=True)
        
        assert isinstance(matched_files, list)
    
    def test_files_via_metadata_retrieve_basic(self, mock_index_manager):
        """测试基础检索"""
        retriever = FilesViaMetadataRetriever(
            index_manager=mock_index_manager,
        )
        
        results = retriever.retrieve("system_science.md文件的内容")
        
        assert isinstance(results, list)
    
    def test_files_via_metadata_empty_query(self, mock_index_manager):
        """测试空查询"""
        retriever = FilesViaMetadataRetriever(
            index_manager=mock_index_manager,
        )
        
        results = retriever.retrieve("")
        assert results == []
    
    def test_files_via_metadata_no_keywords(self, mock_index_manager):
        """测试无文件名关键词"""
        retriever = FilesViaMetadataRetriever(
            index_manager=mock_index_manager,
        )
        
        # 使用不包含文件名的查询
        results = retriever.retrieve("这是一个普通查询")
        # 可能返回空结果或降级处理
        assert isinstance(results, list)
    
    def test_files_via_metadata_no_matching_files(self, mock_index_manager):
        """测试无匹配文件"""
        # Mock返回空结果
        mock_collection = Mock()
        mock_collection.get.return_value = {
            'ids': [],
            'metadatas': []
        }
        mock_index_manager.chroma_collection = mock_collection
        
        retriever = FilesViaMetadataRetriever(
            index_manager=mock_index_manager,
        )
        
        results = retriever.retrieve("nonexistent_file.md")
        assert results == []
    
    def test_files_via_metadata_with_query_bundle(self, mock_index_manager):
        """测试使用QueryBundle检索"""
        retriever = FilesViaMetadataRetriever(
            index_manager=mock_index_manager,
        )
        
        query_bundle = QueryBundle(query_str="system_science.md文件的内容")
        results = retriever.retrieve(query_bundle)
        
        assert isinstance(results, list)
    
    def test_files_via_metadata_top_k_limit(self, mock_index_manager):
        """测试Top-K限制"""
        retriever = FilesViaMetadataRetriever(
            index_manager=mock_index_manager,
            top_k_per_file=5,
        )
        
        results = retriever.retrieve("system_science.md", top_k=3)
        
        assert len(results) <= 3

