"""
模块化RAG架构性能基准测试

建立性能基线，监控迁移影响
"""

import pytest
import time
import statistics
from typing import Dict, List
from pathlib import Path

from src.indexer import IndexManager
from src.query.modular.engine import ModularQueryEngine
# QueryEngine可能在不同的路径，需要根据实际情况调整
try:
    from src.query_engine import QueryEngine
except ImportError:
    try:
        from src.query.modular.engine import ModularQueryEngine as QueryEngine
    except ImportError:
        QueryEngine = None
from src.business.services.rag_service import RAGService
from src.business.pipeline.adapter_factory import create_modular_rag_pipeline
from src.business.pipeline.executor import PipelineExecutor
from src.business.protocols import PipelineContext
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
    
    def test_old_query_engine_baseline(self, benchmark_index_manager):
        """测试旧QueryEngine性能基线"""
        engine = QueryEngine(
            index_manager=benchmark_index_manager,
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
        median_time = statistics.median(times)
        
        print(f"\n旧QueryEngine性能:")
        print(f"  平均耗时: {avg_time:.3f}s")
        print(f"  中位数耗时: {median_time:.3f}s")
        print(f"  最快: {min(times):.3f}s")
        print(f"  最慢: {max(times):.3f}s")
        
        # 性能断言（可以根据实际情况调整）
        assert avg_time < 5.0, "查询耗时过长"
    
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
        
        # 旧引擎
        old_engine = QueryEngine(index_manager=benchmark_index_manager)
        old_engine.query(query)  # 预热
        
        old_times = []
        for _ in range(10):
            start = time.time()
            old_engine.query(query)
            old_times.append(time.time() - start)
        
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
        
        old_avg = statistics.mean(old_times)
        new_avg = statistics.mean(new_times)
        
        print(f"\n性能对比:")
        print(f"  旧QueryEngine: {old_avg:.3f}s")
        print(f"  新ModularQueryEngine: {new_avg:.3f}s")
        print(f"  性能变化: {((new_avg - old_avg) / old_avg * 100):+.1f}%")
        
        # 新引擎不应该比旧引擎慢太多（允许20%的性能下降）
        assert new_avg <= old_avg * 1.2, "新引擎性能下降超过20%"


class TestPipelinePerformance:
    """PipelineExecutor性能测试"""
    
    def test_pipeline_executor_performance(self, benchmark_index_manager):
        """测试PipelineExecutor性能"""
        pipeline = create_modular_rag_pipeline(
            index_manager=benchmark_index_manager,
            enable_reranking=False,
            enable_formatting=True,
        )
        
        executor = PipelineExecutor()
        context = PipelineContext(query="系统科学是什么？")
        
        # 预热
        executor.execute(pipeline, context)
        
        # 性能测试
        times = []
        for _ in range(5):
            context = PipelineContext(query="系统科学是什么？")
            start = time.time()
            result = executor.execute(pipeline, context)
            elapsed = time.time() - start
            times.append(elapsed)
        
        avg_time = statistics.mean(times)
        
        print(f"\nPipelineExecutor性能:")
        print(f"  平均耗时: {avg_time:.3f}s")
        
        assert avg_time < 10.0
    
    def test_pipeline_vs_direct_query(self, benchmark_index_manager):
        """Pipeline vs 直接查询性能对比"""
        query = "系统科学是什么？"
        
        # Pipeline方式
        pipeline = create_modular_rag_pipeline(
            index_manager=benchmark_index_manager,
            enable_reranking=False,
        )
        executor = PipelineExecutor()
        
        pipeline_times = []
        for _ in range(5):
            context = PipelineContext(query=query)
            start = time.time()
            executor.execute(pipeline, context)
            pipeline_times.append(time.time() - start)
        
        # 直接查询方式
        engine = ModularQueryEngine(index_manager=benchmark_index_manager)
        direct_times = []
        for _ in range(5):
            start = time.time()
            engine.query(query)
            direct_times.append(time.time() - start)
        
        pipeline_avg = statistics.mean(pipeline_times)
        direct_avg = statistics.mean(direct_times)
        
        print(f"\nPipeline vs 直接查询:")
        print(f"  Pipeline: {pipeline_avg:.3f}s")
        print(f"  直接查询: {direct_avg:.3f}s")
        print(f"  开销: {((pipeline_avg - direct_avg) / direct_avg * 100):+.1f}%")


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


class TestMemoryUsage:
    """内存使用测试"""
    
    def test_memory_usage_comparison(self, benchmark_index_manager):
        """测试内存使用对比"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # 旧引擎内存
        old_engine = QueryEngine(index_manager=benchmark_index_manager)
        old_engine.query("测试")  # 触发加载
        old_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 新引擎内存
        new_engine = ModularQueryEngine(index_manager=benchmark_index_manager)
        new_engine.query("测试")  # 触发加载
        new_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"\n内存使用对比:")
        print(f"  旧QueryEngine: {old_memory:.1f} MB")
        print(f"  新ModularQueryEngine: {new_memory:.1f} MB")
        print(f"  内存变化: {((new_memory - old_memory) / old_memory * 100):+.1f}%")
        
        # 新引擎内存不应该增加太多（允许50%的增长）
        assert new_memory <= old_memory * 1.5, "新引擎内存使用增加超过50%"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

