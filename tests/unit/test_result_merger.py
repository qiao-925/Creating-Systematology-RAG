"""
结果合并器单元测试
"""

import pytest
from llama_index.core.schema import NodeWithScore, TextNode

from backend.business.rag_engine.retrieval.merger import ResultMerger


class TestResultMerger:
    """ResultMerger单元测试"""
    
    @pytest.fixture
    def sample_nodes(self):
        """创建示例节点"""
        nodes = []
        for i in range(5):
            node = TextNode(
                text=f"文档{i}",
                metadata={"id": i},
            )
            nodes.append(NodeWithScore(node=node, score=0.9 - i * 0.1))
        return nodes
    
    def test_init(self):
        """测试初始化"""
        merger = ResultMerger(
            merge_strategy="reciprocal_rank_fusion",
            weights={"retriever1": 1.0, "retriever2": 0.8},
            enable_deduplication=True,
        )
        
        assert merger.merge_strategy == "reciprocal_rank_fusion"
        assert merger.weights == {"retriever1": 1.0, "retriever2": 0.8}
        assert merger.enable_deduplication is True
    
    def test_reciprocal_rank_fusion(self, sample_nodes):
        """测试RRF合并"""
        merger = ResultMerger(
            merge_strategy="reciprocal_rank_fusion",
            rrf_k=60,
        )
        
        results_by_retriever = {
            "retriever1": sample_nodes[:3],
            "retriever2": sample_nodes[2:5],
        }
        
        merged = merger.merge_results(results_by_retriever, top_k=5)
        
        assert isinstance(merged, list)
        assert len(merged) <= 5
        assert all(isinstance(r, NodeWithScore) for r in merged)
        
        # 应该合并两个检索器的结果
        assert len(merged) >= 3
    
    def test_weighted_score_fusion(self, sample_nodes):
        """测试加权分数融合"""
        merger = ResultMerger(
            merge_strategy="weighted_score",
            weights={"retriever1": 1.0, "retriever2": 0.5},
        )
        
        results_by_retriever = {
            "retriever1": sample_nodes[:3],
            "retriever2": sample_nodes[2:5],
        }
        
        merged = merger.merge_results(results_by_retriever, top_k=5)
        
        assert isinstance(merged, list)
        assert len(merged) <= 5
    
    def test_deduplication(self, sample_nodes):
        """测试去重"""
        # 创建重复节点
        node = TextNode(text="重复文档", metadata={"id": "duplicate"})
        duplicate_nodes = [
            NodeWithScore(node=node, score=0.9),
            NodeWithScore(node=node, score=0.8),
        ]
        
        merger = ResultMerger(
            merge_strategy="reciprocal_rank_fusion",
            enable_deduplication=True,
        )
        
        results_by_retriever = {
            "retriever1": duplicate_nodes,
            "retriever2": duplicate_nodes,
        }
        
        merged = merger.merge_results(results_by_retriever, top_k=5)
        
        # 去重后应该只有1个唯一节点
        unique_ids = {r.node.node_id for r in merged}
        assert len(unique_ids) == 1
    
    def test_deduplication_disabled(self, sample_nodes):
        """测试禁用去重"""
        merger = ResultMerger(
            merge_strategy="reciprocal_rank_fusion",
            enable_deduplication=False,
        )
        
        # 使用相同节点测试
        results_by_retriever = {
            "retriever1": sample_nodes[:2],
            "retriever2": sample_nodes[:2],
        }
        
        merged = merger.merge_results(results_by_retriever, top_k=5)
        
        # 不去重时可能包含重复节点（取决于合并策略）
        assert isinstance(merged, list)
    
    def test_empty_results(self):
        """测试空结果"""
        merger = ResultMerger()
        
        merged = merger.merge_results({}, top_k=5)
        
        assert isinstance(merged, list)
        assert len(merged) == 0
    
    def test_top_k_limit(self, sample_nodes):
        """测试Top-K限制"""
        merger = ResultMerger()
        
        results_by_retriever = {
            "retriever1": sample_nodes,
            "retriever2": sample_nodes,
        }
        
        merged = merger.merge_results(results_by_retriever, top_k=3)
        
        assert len(merged) <= 3
    
    def test_rrf_k_parameter(self, sample_nodes):
        """测试RRF K参数"""
        merger1 = ResultMerger(
            merge_strategy="reciprocal_rank_fusion",
            rrf_k=60,
        )
        
        merger2 = ResultMerger(
            merge_strategy="reciprocal_rank_fusion",
            rrf_k=100,
        )
        
        results_by_retriever = {
            "retriever1": sample_nodes[:3],
            "retriever2": sample_nodes[:3],
        }
        
        merged1 = merger1.merge_results(results_by_retriever, top_k=5)
        merged2 = merger2.merge_results(results_by_retriever, top_k=5)
        
        # 不同K值可能产生不同排序
        assert isinstance(merged1, list)
        assert isinstance(merged2, list)
    
    def test_simple_concatenation(self, sample_nodes):
        """测试简单拼接策略"""
        merger = ResultMerger(
            merge_strategy="simple",
            enable_deduplication=False,
        )
        
        results_by_retriever = {
            "retriever1": sample_nodes[:2],
            "retriever2": sample_nodes[2:4],
        }
        
        merged = merger.merge_results(results_by_retriever, top_k=5)
        
        assert isinstance(merged, list)
        # 简单拼接应该包含所有结果（可能超过top_k限制）
        # 但实际返回受top_k限制
        assert len(merged) <= 5
    
    def test_node_id_generation(self):
        """测试节点ID生成"""
        merger = ResultMerger()
        
        # 创建相同文本但不同元数据的节点
        node1 = TextNode(text="相同文本", metadata={"id": 1, "file": "doc1.md"})
        node2 = TextNode(text="相同文本", metadata={"id": 2, "file": "doc2.md"})
        
        nodes = [
            NodeWithScore(node=node1, score=0.9),
            NodeWithScore(node=node2, score=0.8),
        ]
        
        results_by_retriever = {
            "retriever1": nodes,
        }
        
        merged = merger.merge_results(results_by_retriever, top_k=5)
        
        # 验证节点ID被正确生成和使用
        assert len(merged) > 0
        for result in merged:
            assert hasattr(result.node, 'node_id')
            assert result.node.node_id is not None

