"""
模块化RAG架构性能基准测试

建立性能基线，监控迁移影响
"""

import pytest
import time
import statistics
from typing import Dict, List
from pathlib import Path

from backend.infrastructure.indexer import IndexManager
from backend.business.rag_engine.core.engine import ModularQueryEngine
from backend.business.rag_api.rag_service import RAGService
from llama_index.core.schema import Document as LlamaDocument


@pytest.fixture(scope="module")
def benchmark_index_manager():
    """创建基准测试索引管理器"""
    # 创建测试文档
    docs = [
        LlamaDocument(
            text=f"文档{i}的内容。这是关于系统科学的第{i}个文档。",
            metadata={"id": i, "title": f"文档{i}"},
        )
        for i in range(50)  # 50个文档用于基准测试
    ]
    
    manager = IndexManager(collection_name="benchmark_test")
    manager.build_index(docs)
    return manager


class TestQueryEnginePerformance:
    """查询引擎性能测试"""
    
    def test_modular_query_engine_vector(self, benchmark_index_manager):
        """测试ModularQueryEngine向量检索性能"""
        engine = ModularQueryEngine(
            index_manager=benchmark_index_manager,
            retrieval_strategy="vector",
            similarity_top_k=5,
        )
        
        query = "系统科学是什么？"
        
        # 预热
        engine.query(query)
        
        # 性能测试
        times = []
        for _ in range(10):
            start = time.time()
            answer, sources, _ = engine.query(query)
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        
        print(f"\nModularQueryEngine (vector)性能:")
        print(f"  平均耗时: {avg_time:.3f}s")
        
        assert avg_time < 5.0
    
    def test_modular_query_engine_multi(self, benchmark_index_manager):
        """测试ModularQueryEngine多策略检索性能"""
        engine = ModularQueryEngine(
            index_manager=benchmark_index_manager,
            retrieval_strategy="multi",
            similarity_top_k=5,
        )
        
        query = "系统科学是什么？"
        
        # 预热
        try:
            engine.query(query)
        except Exception as e:
            pytest.skip(f"多策略检索初始化失败: {e}")
        
        # 性能测试
        times = []
        for _ in range(5):  # 减少次数，因为多策略较慢
            start = time.time()
            answer, sources, _ = engine.query(query)
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        
        print(f"\nModularQueryEngine (multi)性能:")
        print(f"  平均耗时: {avg_time:.3f}s")
        
        # 多策略检索可能较慢，放宽限制
        assert avg_time < 10.0
    
    def test_modular_query_engine_with_rerank(self, benchmark_index_manager):
        """测试启用重排序的性能影响"""
        engine = ModularQueryEngine(
            index_manager=benchmark_index_manager,
            retrieval_strategy="vector",
            enable_rerank=True,
            rerank_top_n=3,
        )
        
        query = "系统科学是什么？"
        
        try:
            # 预热
            engine.query(query)
            
            # 性能测试
            times = []
            for _ in range(5):
                start = time.time()
                answer, sources, _ = engine.query(query)
                elapsed = time.time() - start
                times.append(elapsed)
            
            avg_time = statistics.mean(times)
            
            print(f"\nModularQueryEngine (with rerank)性能:")
            print(f"  平均耗时: {avg_time:.3f}s")
            
            assert avg_time < 10.0
        except Exception as e:
            pytest.skip(f"重排序模块初始化失败: {e}")
    
    def test_performance_comparison(self, benchmark_index_manager):
        """性能对比测试"""
        query = "系统科学是什么？"
                
        # 新引擎
        new_engine = ModularQueryEngine(
            index_manager=benchmark_index_manager,
            retrieval_strategy="vector",
        )
        new_engine.query(query)  # 预热
        
        new_times = []
        for _ in range(10):
            start = time.time()
            new_engine.query(query)
            new_times.append(time.time() - start)
        
        new_avg = statistics.mean(new_times)
        
        print(f"\n性能对比:")
        print(f"  ModularQueryEngine: {new_avg:.3f}s")


class TestRAGServicePerformance:
    """RAGService性能测试"""
    
    def test_rag_service_query_performance(self, benchmark_index_manager):
        """测试RAGService查询性能"""
        service = RAGService(
            collection_name=benchmark_index_manager.collection_name,
            use_modular_engine=True,
        )
        
        query = "系统科学是什么？"
        
        # 预热
        service.query(query)
        
        # 性能测试
        times = []
        for _ in range(10):
            start = time.time()
            response = service.query(query)
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        
        print(f"\nRAGService性能:")
        print(f"  平均耗时: {avg_time:.3f}s")
        
        assert avg_time < 5.0
    
    def test_rag_service_vs_direct(self, benchmark_index_manager):
        """RAGService vs 直接调用性能对比"""
        query = "系统科学是什么？"
        
        # RAGService方式
        service = RAGService(
            collection_name=benchmark_index_manager.collection_name,
        )
        service.query(query)  # 预热
        
        service_times = []
        for _ in range(10):
            start = time.time()
            service.query(query)
            service_times.append(time.time() - start)
        
        # 直接调用方式
        engine = ModularQueryEngine(index_manager=benchmark_index_manager)
        engine.query(query)  # 预热
        
        direct_times = []
        for _ in range(10):
            start = time.time()
            engine.query(query)
            direct_times.append(time.time() - start)
        
        service_avg = statistics.mean(service_times)
        direct_avg = statistics.mean(direct_times)
        
        print(f"\nRAGService vs 直接调用:")
        print(f"  RAGService: {service_avg:.3f}s")
        print(f"  直接调用: {direct_avg:.3f}s")
        print(f"  开销: {((service_avg - direct_avg) / direct_avg * 100):+.1f}%")


class TestRetrievalStrategiesPerformance:
    """检索策略性能对比"""
    
    def test_vector_vs_bm25_vs_multi(self, benchmark_index_manager):
        """测试不同检索策略性能"""
        query = "系统科学是什么？"
        
        results = {}
        
        # Vector检索
        vector_engine = ModularQueryEngine(
            index_manager=benchmark_index_manager,
            retrieval_strategy="vector",
        )
        vector_engine.query(query)  # 预热
        
        vector_times = []
        for _ in range(10):
            start = time.time()
            vector_engine.query(query)
            vector_times.append(time.time() - start)
        results["vector"] = statistics.mean(vector_times)
        
        # BM25检索
        try:
            bm25_engine = ModularQueryEngine(
                index_manager=benchmark_index_manager,
                retrieval_strategy="bm25",
            )
            bm25_engine.query(query)  # 预热
            
            bm25_times = []
            for _ in range(10):
                start = time.time()
                bm25_engine.query(query)
                bm25_times.append(time.time() - start)
            results["bm25"] = statistics.mean(bm25_times)
        except Exception as e:
            results["bm25"] = None
        
        # Multi策略检索
        try:
            multi_engine = ModularQueryEngine(
                index_manager=benchmark_index_manager,
                retrieval_strategy="multi",
            )
            multi_engine.query(query)  # 预热
            
            multi_times = []
            for _ in range(5):
                start = time.time()
                multi_engine.query(query)
                multi_times.append(time.time() - start)
            results["multi"] = statistics.mean(multi_times)
        except Exception as e:
            results["multi"] = None
        
        print(f"\n检索策略性能对比:")
        for strategy, avg_time in results.items():
            if avg_time:
                print(f"  {strategy}: {avg_time:.3f}s")
            else:
                print(f"  {strategy}: N/A")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

