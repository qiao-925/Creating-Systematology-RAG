"""
多策略检索器单元测试
"""

import pytest
from unittest.mock import Mock, patch
from typing import List

from backend.business.rag_engine.retrieval.strategies.multi_strategy import (
    MultiStrategyRetriever,
    BaseRetriever,
)
from backend.business.rag_engine.retrieval.merger import ResultMerger
from llama_index.core.schema import NodeWithScore, TextNode


class MockRetriever(BaseRetriever):
    """Mock检索器用于测试"""
    
    def __init__(self, name: str, top_k: int = 5):
        self._name = name
        self._top_k = top_k
    
    def retrieve(self, query: str, top_k: int = None) -> List[NodeWithScore]:
        current_top_k = top_k or self._top_k
        nodes = []
        for i in range(current_top_k):
            node = TextNode(
                text=f"{self._name} result {i}",
                metadata={"retriever": self._name, "rank": i},
            )
            nodes.append(NodeWithScore(node=node, score=0.9 - i * 0.1))
        return nodes
    
    def get_name(self) -> str:
        return self._name
    
    def get_top_k(self) -> int:
        return self._top_k


class TestBaseRetriever:
    """BaseRetriever接口测试"""
    
    def test_base_retriever_interface(self):
        """测试BaseRetriever接口"""
        retriever = MockRetriever("test", top_k=5)
        
        assert hasattr(retriever, 'retrieve')
        assert hasattr(retriever, 'get_name')
        assert hasattr(retriever, 'get_top_k')
        assert retriever.get_name() == "test"
        assert retriever.get_top_k() == 5
    
    def test_base_retriever_retrieve(self):
        """测试retrieve方法"""
        retriever = MockRetriever("test")
        results = retriever.retrieve("query", top_k=3)
        
        assert isinstance(results, list)
        assert len(results) == 3
        assert all(isinstance(r, NodeWithScore) for r in results)


class TestMultiStrategyRetriever:
    """MultiStrategyRetriever单元测试"""
    
    def test_init(self):
        """测试初始化"""
        retrievers = [
            MockRetriever("retriever1"),
            MockRetriever("retriever2"),
        ]
        
        multi_retriever = MultiStrategyRetriever(
            retrievers=retrievers,
            merge_strategy="reciprocal_rank_fusion",
        )
        
        assert len(multi_retriever.retrievers) == 2
        assert multi_retriever.merge_strategy == "reciprocal_rank_fusion"
        assert multi_retriever.get_name() == "multi_strategy_retriever"
    
    def test_init_empty_retrievers(self):
        """测试空检索器列表"""
        with pytest.raises(ValueError, match="必须至少提供一个检索器"):
            MultiStrategyRetriever(retrievers=[])
    
    def test_retrieve_rrf(self):
        """测试RRF合并策略"""
        retrievers = [
            MockRetriever("retriever1", top_k=3),
            MockRetriever("retriever2", top_k=3),
        ]
        
        multi_retriever = MultiStrategyRetriever(
            retrievers=retrievers,
            merge_strategy="reciprocal_rank_fusion",
            enable_deduplication=True,
        )
        
        results = multi_retriever.retrieve("query", top_k=5)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, NodeWithScore) for r in results)
        # RRF应该合并两个检索器的结果
        assert len(results) <= 5  # Top-K限制
    
    def test_retrieve_weighted_score(self):
        """测试加权分数融合"""
        retrievers = [
            MockRetriever("retriever1", top_k=2),
            MockRetriever("retriever2", top_k=2),
        ]
        
        multi_retriever = MultiStrategyRetriever(
            retrievers=retrievers,
            merge_strategy="weighted_score",
            weights={"retriever1": 1.0, "retriever2": 0.5},
        )
        
        results = multi_retriever.retrieve("query", top_k=5)
        
        assert isinstance(results, list)
        assert len(results) > 0
    
    def test_retrieve_with_error(self):
        """测试检索器错误处理"""
        class FailingRetriever(BaseRetriever):
            def retrieve(self, query: str, top_k: int = None):
                raise Exception("检索失败")
            
            def get_name(self):
                return "failing"
            
            def get_top_k(self):
                return 5
        
        retrievers = [
            MockRetriever("retriever1"),
            FailingRetriever(),
        ]
        
        multi_retriever = MultiStrategyRetriever(
            retrievers=retrievers,
            merge_strategy="reciprocal_rank_fusion",
        )
        
        # 应该处理错误，继续执行其他检索器
        results = multi_retriever.retrieve("query", top_k=5)
        
        assert isinstance(results, list)
        # 至少应该有retriever1的结果
        assert len(results) > 0
    
    def test_retrieve_deduplication(self):
        """测试去重功能"""
        # 创建返回相同节点的检索器
        node = TextNode(text="相同内容", metadata={"id": "1"})
        
        class SameResultRetriever(BaseRetriever):
            def retrieve(self, query: str, top_k: int = None):
                return [NodeWithScore(node=node, score=0.9)]
            
            def get_name(self):
                return "same_result"
            
            def get_top_k(self):
                return 5
        
        retrievers = [
            SameResultRetriever(),
            SameResultRetriever(),
        ]
        
        multi_retriever = MultiStrategyRetriever(
            retrievers=retrievers,
            merge_strategy="reciprocal_rank_fusion",
            enable_deduplication=True,
        )
        
        results = multi_retriever.retrieve("query", top_k=5)
        
        # 去重后应该只有1个结果
        assert len(results) == 1
    
    def test_parallel_retrieval(self):
        """测试并行执行多种检索策略"""
        import time
        
        class SlowRetriever(BaseRetriever):
            """模拟慢速检索器"""
            def __init__(self, name: str, delay: float = 0.1):
                self._name = name
                self._delay = delay
            
            def retrieve(self, query: str, top_k: int = None):
                time.sleep(self._delay)
                return [
                    NodeWithScore(
                        node=TextNode(text=f"{self._name} result", metadata={"retriever": self._name}),
                        score=0.9
                    )
                ]
            
            def get_name(self):
                return self._name
            
            def get_top_k(self):
                return 5
        
        retrievers = [
            SlowRetriever("retriever1", delay=0.1),
            SlowRetriever("retriever2", delay=0.1),
            SlowRetriever("retriever3", delay=0.1),
        ]
        
        multi_retriever = MultiStrategyRetriever(
            retrievers=retrievers,
            merge_strategy="reciprocal_rank_fusion",
            max_workers=3,
        )
        
        # 并行执行应该比串行快
        start_time = time.time()
        results = multi_retriever.retrieve("query", top_k=5)
        elapsed_time = time.time() - start_time
        
        assert len(results) > 0
        # 并行执行应该比串行（3 * 0.1 = 0.3秒）快
        assert elapsed_time < 0.25  # 允许一些开销
    
    def test_merge_strategy_selection(self):
        """测试合并策略选择"""
        retrievers = [
            MockRetriever("retriever1"),
            MockRetriever("retriever2"),
        ]
        
        # 测试RRF策略
        multi_retriever_rrf = MultiStrategyRetriever(
            retrievers=retrievers,
            merge_strategy="reciprocal_rank_fusion",
        )
        results_rrf = multi_retriever_rrf.retrieve("query", top_k=5)
        assert isinstance(results_rrf, list)
        
        # 测试加权分数策略
        multi_retriever_weighted = MultiStrategyRetriever(
            retrievers=retrievers,
            merge_strategy="weighted_score",
            weights={"retriever1": 1.0, "retriever2": 0.5},
        )
        results_weighted = multi_retriever_weighted.retrieve("query", top_k=5)
        assert isinstance(results_weighted, list)
        
        # 测试简单拼接策略
        multi_retriever_simple = MultiStrategyRetriever(
            retrievers=retrievers,
            merge_strategy="simple",
        )
        results_simple = multi_retriever_simple.retrieve("query", top_k=5)
        assert isinstance(results_simple, list)

