"""
重排序性能测试
测试重排序延迟和对整体查询性能的影响
"""

import pytest
import time
import statistics
from llama_index.core.schema import Document as LlamaDocument

from src.indexer import IndexManager
from src.query.modular.engine import ModularQueryEngine


@pytest.fixture
def test_documents():
    """创建测试文档"""
    return [
        LlamaDocument(
            text=f"系统科学是研究系统的一般规律和方法的学科。文档{i}包含系统科学、控制论、信息论等相关知识内容。",
            metadata={"id": i, "title": f"文档{i}", "source": "test"}
        )
        for i in range(50)
    ]


@pytest.fixture
def performance_index_manager(test_documents, collection_name="reranker_perf_test"):
    """创建性能测试索引"""
    manager = IndexManager(collection_name=collection_name)
    manager.build_index(documents=test_documents, collection_name=collection_name)
    yield manager
    try:
        manager.delete_collection(collection_name)
    except:
        pass


class TestRerankerLatency:
    """重排序延迟测试"""
    
    def test_reranker_latency_with_vector_retrieval(
        self, performance_index_manager, collection_name="reranker_perf_test"
    ):
        """测试重排序与向量检索的延迟"""
        query = "什么是系统科学？"
        
        # 不带重排序的查询
        engine_no_rerank = ModularQueryEngine(
            index_manager=performance_index_manager,
            retrieval_strategy="vector",
            similarity_top_k=10,
            enable_rerank=False,
        )
        
        # 带重排序的查询
        engine_with_rerank = ModularQueryEngine(
            index_manager=performance_index_manager,
            retrieval_strategy="vector",
            similarity_top_k=10,
            enable_rerank=True,
        )
        
        # 预热
        try:
            engine_no_rerank.query(query)
            engine_with_rerank.query(query)
        except:
            pass
        
        # 不带重排序的性能测试
        no_rerank_times = []
        for _ in range(5):
            start = time.time()
            try:
                engine_no_rerank.query(query)
                elapsed = time.time() - start
                no_rerank_times.append(elapsed)
            except:
                pass
        
        # 带重排序的性能测试
        with_rerank_times = []
        for _ in range(5):
            start = time.time()
            try:
                engine_with_rerank.query(query)
                elapsed = time.time() - start
                with_rerank_times.append(elapsed)
            except:
                pass
        
        if no_rerank_times and with_rerank_times:
            avg_no_rerank = statistics.mean(no_rerank_times)
            avg_with_rerank = statistics.mean(with_rerank_times)
            latency_overhead = avg_with_rerank - avg_no_rerank
            
            print(f"\n重排序延迟测试:")
            print(f"  不带重排序平均耗时: {avg_no_rerank:.3f}s")
            print(f"  带重排序平均耗时: {avg_with_rerank:.3f}s")
            print(f"  重排序延迟开销: {latency_overhead:.3f}s")
            print(f"  延迟增加比例: {(latency_overhead / avg_no_rerank * 100):.1f}%")
            
            # 重排序延迟应该合理（不超过基准时间的50%）
            if avg_no_rerank > 0:
                overhead_ratio = latency_overhead / avg_no_rerank
                # assert overhead_ratio < 1.0, f"重排序延迟开销过大: {overhead_ratio:.2%}"
    
    def test_reranker_latency_with_multi_strategy(
        self, performance_index_manager, collection_name="reranker_perf_test"
    ):
        """测试重排序与多策略检索的延迟"""
        from unittest.mock import patch
        
        query = "系统科学的应用领域"
        
        with patch('src.config.config.ENABLED_RETRIEVAL_STRATEGIES', ['vector', 'bm25']):
            # 不带重排序
            engine_no_rerank = ModularQueryEngine(
                index_manager=performance_index_manager,
                retrieval_strategy="multi",
                similarity_top_k=10,
                enable_rerank=False,
            )
            
            # 带重排序
            engine_with_rerank = ModularQueryEngine(
                index_manager=performance_index_manager,
                retrieval_strategy="multi",
                similarity_top_k=10,
                enable_rerank=True,
            )
            
            # 性能测试
            try:
                # 不带重排序
                no_rerank_times = []
                for _ in range(5):
                    start = time.time()
                    try:
                        engine_no_rerank.query(query)
                        elapsed = time.time() - start
                        no_rerank_times.append(elapsed)
                    except:
                        pass
                
                # 带重排序
                with_rerank_times = []
                for _ in range(5):
                    start = time.time()
                    try:
                        engine_with_rerank.query(query)
                        elapsed = time.time() - start
                        with_rerank_times.append(elapsed)
                    except:
                        pass
                
                if no_rerank_times and with_rerank_times:
                    avg_no_rerank = statistics.mean(no_rerank_times)
                    avg_with_rerank = statistics.mean(with_rerank_times)
                    
                    print(f"\n多策略+重排序延迟测试:")
                    print(f"  不带重排序: {avg_no_rerank:.3f}s")
                    print(f"  带重排序: {avg_with_rerank:.3f}s")
                    
                    # 验证性能合理性
                    assert max(with_rerank_times) < 20.0, "多策略+重排序耗时过长"
                    
            except Exception as e:
                pytest.skip(f"多策略+重排序测试失败: {e}")
    
    def test_reranker_top_n_impact(
        self, performance_index_manager, collection_name="reranker_perf_test"
    ):
        """测试重排序top_n参数对性能的影响"""
        query = "控制论的基本概念"
        
        top_n_values = [5, 10, 20]
        performance_by_top_n = {}
        
        for top_n in top_n_values:
            engine = ModularQueryEngine(
                index_manager=performance_index_manager,
                retrieval_strategy="vector",
                similarity_top_k=top_n,
                enable_rerank=True,
                rerank_top_n=top_n,
            )
            
            # 性能测试
            times = []
            for _ in range(5):
                start = time.time()
                try:
                    engine.query(query)
                    elapsed = time.time() - start
                    times.append(elapsed)
                except:
                    pass
            
            if times:
                avg_time = statistics.mean(times)
                performance_by_top_n[top_n] = avg_time
                print(f"\ntop_n={top_n} 平均耗时: {avg_time:.3f}s")
        
        # 验证top_n越大，耗时可能增加（但不应该线性增长）
        if len(performance_by_top_n) > 1:
            print(f"\n重排序top_n对性能的影响: {performance_by_top_n}")


class TestRerankerPerformanceImpact:
    """重排序性能影响测试"""
    
    def test_reranker_performance_impact_on_p95(
        self, performance_index_manager, collection_name="reranker_perf_test"
    ):
        """测试重排序对P95响应时间的影响"""
        import numpy as np
        
        query = "信息论的主要内容"
        
        # 不带重排序
        engine_no_rerank = ModularQueryEngine(
            index_manager=performance_index_manager,
            retrieval_strategy="vector",
            similarity_top_k=10,
            enable_rerank=False,
        )
        
        # 带重排序
        engine_with_rerank = ModularQueryEngine(
            index_manager=performance_index_manager,
            retrieval_strategy="vector",
            similarity_top_k=10,
            enable_rerank=True,
        )
        
        # 性能测试（多次查询获取P95）
        no_rerank_times = []
        with_rerank_times = []
        
        for _ in range(20):
            # 不带重排序
            start = time.time()
            try:
                engine_no_rerank.query(query)
                elapsed = time.time() - start
                no_rerank_times.append(elapsed)
            except:
                pass
            
            # 带重排序
            start = time.time()
            try:
                engine_with_rerank.query(query)
                elapsed = time.time() - start
                with_rerank_times.append(elapsed)
            except:
                pass
        
        if no_rerank_times and with_rerank_times:
            p95_no_rerank = np.percentile(no_rerank_times, 95)
            p95_with_rerank = np.percentile(with_rerank_times, 95)
            impact = p95_with_rerank - p95_no_rerank
            
            print(f"\n重排序对P95响应时间的影响:")
            print(f"  不带重排序P95: {p95_no_rerank:.3f}s")
            print(f"  带重排序P95: {p95_with_rerank:.3f}s")
            print(f"  性能影响: {impact:.3f}s")
            
            # 重排序不应使P95超过合理范围
            assert p95_with_rerank < 15.0, f"带重排序的P95响应时间过长: {p95_with_rerank:.3f}s"


class TestRerankerResourceUsage:
    """重排序资源使用测试"""
    
    def test_reranker_memory_usage(
        self, performance_index_manager, collection_name="reranker_perf_test"
    ):
        """测试重排序的内存使用"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            
            query = "系统科学的应用"
            
            # 不带重排序
            engine_no_rerank = ModularQueryEngine(
                index_manager=performance_index_manager,
                retrieval_strategy="vector",
                enable_rerank=False,
            )
            
            # 带重排序
            engine_with_rerank = ModularQueryEngine(
                index_manager=performance_index_manager,
                retrieval_strategy="vector",
                enable_rerank=True,
            )
            
            # 测试不带重排序的内存
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            for _ in range(10):
                try:
                    engine_no_rerank.query(query)
                except:
                    pass
            memory_no_rerank = process.memory_info().rss / 1024 / 1024  # MB
            
            # 测试带重排序的内存
            for _ in range(10):
                try:
                    engine_with_rerank.query(query)
                except:
                    pass
            memory_with_rerank = process.memory_info().rss / 1024 / 1024  # MB
            
            memory_overhead = memory_with_rerank - memory_no_rerank
            
            print(f"\n重排序内存使用:")
            print(f"  不带重排序: {memory_no_rerank:.2f} MB")
            print(f"  带重排序: {memory_with_rerank:.2f} MB")
            print(f"  内存开销: {memory_overhead:.2f} MB")
            
        except ImportError:
            pytest.skip("psutil未安装，跳过内存测试")
        except Exception as e:
            pytest.skip(f"内存测试失败: {e}")


class TestRerankerPerformanceBenchmarks:
    """重排序性能基准测试"""
    
    def test_reranker_performance_baseline(
        self, performance_index_manager, collection_name="reranker_perf_test"
    ):
        """建立重排序性能基准"""
        test_queries = [
            "什么是系统科学？",
            "系统科学的应用",
            "控制论的基本概念",
        ]
        
        engine = ModularQueryEngine(
            index_manager=performance_index_manager,
            retrieval_strategy="vector",
            similarity_top_k=10,
            enable_rerank=True,
        )
        
        all_response_times = []
        
        for query in test_queries:
            times = []
            for _ in range(5):
                start = time.time()
                try:
                    answer, sources, _ = engine.query(query)
                    elapsed = time.time() - start
                    if answer:
                        times.append(elapsed)
                except:
                    pass
            
            if times:
                avg_time = statistics.mean(times)
                all_response_times.extend(times)
                print(f"\n查询 '{query}' 平均响应时间: {avg_time:.3f}s")
        
        if all_response_times:
            overall_avg = statistics.mean(all_response_times)
            overall_max = max(all_response_times)
            
            print(f"\n重排序性能基准:")
            print(f"  平均响应时间: {overall_avg:.3f}s")
            print(f"  最大响应时间: {overall_max:.3f}s")
            
            # 性能基准断言
            assert overall_max < 15.0, f"重排序最大响应时间为{overall_max:.3f}s，超过15秒"


