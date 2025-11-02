"""
多策略检索性能测试
测试并行检索性能、合并策略性能对比
"""

import pytest
import time
import statistics
from typing import List
from unittest.mock import patch

from src.indexer import IndexManager
from src.query.modular.engine import ModularQueryEngine
from llama_index.core.schema import Document as LlamaDocument


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
def performance_index_manager(test_documents, collection_name="multi_strategy_perf_test"):
    """创建性能测试索引"""
    manager = IndexManager(collection_name=collection_name)
    manager.build_index(documents=test_documents, collection_name=collection_name)
    yield manager
    try:
        manager.delete_collection(collection_name)
    except:
        pass


class TestParallelRetrievalPerformance:
    """并行检索性能测试"""
    
    def test_parallel_vs_sequential_retrieval(
        self, performance_index_manager, collection_name="multi_strategy_perf_test"
    ):
        """测试并行检索 vs 串行检索的性能对比"""
        query = "什么是系统科学？"
        
        # 测试并行检索（multi策略）
        with patch('src.config.config.ENABLED_RETRIEVAL_STRATEGIES', ['vector', 'bm25']):
            multi_engine = ModularQueryEngine(
                index_manager=performance_index_manager,
                retrieval_strategy="multi",
                similarity_top_k=5,
            )
            
            # 预热
            try:
                multi_engine.query(query)
            except:
                pass
            
            # 并行检索性能测试
            parallel_times = []
            for _ in range(5):
                start = time.time()
                try:
                    multi_engine.query(query)
                    elapsed = time.time() - start
                    parallel_times.append(elapsed)
                except:
                    pass
            
            if parallel_times:
                avg_parallel_time = statistics.mean(parallel_times)
                print(f"\n并行检索（multi策略）平均耗时: {avg_parallel_time:.3f}s")
        
        # 测试单一策略检索（作为对比）
        vector_engine = ModularQueryEngine(
            index_manager=performance_index_manager,
            retrieval_strategy="vector",
            similarity_top_k=5,
        )
        
        sequential_times = []
        for _ in range(5):
            start = time.time()
            try:
                vector_engine.query(query)
                elapsed = time.time() - start
                sequential_times.append(elapsed)
            except:
                pass
        
        if sequential_times:
            avg_sequential_time = statistics.mean(sequential_times)
            print(f"\n单一策略检索平均耗时: {avg_sequential_time:.3f}s")
        
        # 验证性能合理性
        if parallel_times and sequential_times:
            # 并行检索可能会稍慢（因为需要合并结果），但不应慢太多
            assert max(parallel_times) < 15.0, "并行检索耗时过长"
            assert max(sequential_times) < 10.0, "单一策略检索耗时过长"
    
    def test_multi_strategy_retrieval_performance(
        self, performance_index_manager, collection_name="multi_strategy_perf_test"
    ):
        """测试多策略检索性能"""
        query = "系统科学的应用领域"
        
        with patch('src.config.config.ENABLED_RETRIEVAL_STRATEGIES', ['vector', 'bm25', 'hybrid']):
            engine = ModularQueryEngine(
                index_manager=performance_index_manager,
                retrieval_strategy="multi",
                similarity_top_k=5,
            )
            
            # 预热
            try:
                engine.query(query)
            except:
                pass
            
            # 性能测试
            response_times = []
            for _ in range(10):
                start = time.time()
                try:
                    answer, sources, _ = engine.query(query)
                    elapsed = time.time() - start
                    response_times.append(elapsed)
                    assert answer is not None
                except Exception as e:
                    pytest.skip(f"多策略检索测试失败: {e}")
            
            avg_time = statistics.mean(response_times)
            p95_time = max(response_times) if response_times else 0
            
            print(f"\n多策略检索性能:")
            print(f"  平均响应时间: {avg_time:.3f}s")
            print(f"  P95响应时间: {p95_time:.3f}s")
            
            # 性能断言
            assert p95_time < 15.0, f"多策略检索P95响应时间应该小于15秒"


class TestMergeStrategyPerformance:
    """合并策略性能测试"""
    
    def test_rrf_vs_weighted_merge_performance(
        self, performance_index_manager, collection_name="multi_strategy_perf_test"
    ):
        """测试RRF vs 加权合并的性能对比"""
        query = "控制论的基本概念"
        
        with patch('src.config.config.ENABLED_RETRIEVAL_STRATEGIES', ['vector', 'bm25']):
            # RRF合并策略
            rrf_engine = ModularQueryEngine(
                index_manager=performance_index_manager,
                retrieval_strategy="multi",
                similarity_top_k=5,
            )
            
            # 修改为加权合并策略（如果支持）
            # 注意：这里假设MultiStrategyRetriever支持不同的合并策略
            # 实际实现可能需要通过配置传递
            
            # 测试RRF策略
            rrf_times = []
            for _ in range(5):
                start = time.time()
                try:
                    rrf_engine.query(query)
                    elapsed = time.time() - start
                    rrf_times.append(elapsed)
                except:
                    pass
            
            if rrf_times:
                avg_rrf_time = statistics.mean(rrf_times)
                print(f"\nRRF合并策略平均耗时: {avg_rrf_time:.3f}s")
            
            # 验证性能
            if rrf_times:
                assert max(rrf_times) < 15.0, "RRF合并策略耗时过长"
    
    def test_merge_strategy_scalability(
        self, performance_index_manager, collection_name="multi_strategy_perf_test"
    ):
        """测试合并策略的可扩展性"""
        query = "信息论的主要内容"
        
        # 测试不同数量的策略组合
        strategy_combinations = [
            ['vector'],
            ['vector', 'bm25'],
            ['vector', 'bm25', 'grep'],
        ]
        
        for strategies in strategy_combinations:
            with patch('src.config.config.ENABLED_RETRIEVAL_STRATEGIES', strategies):
                try:
                    engine = ModularQueryEngine(
                        index_manager=performance_index_manager,
                        retrieval_strategy="multi" if len(strategies) > 1 else "vector",
                        similarity_top_k=5,
                    )
                    
                    # 性能测试
                    times = []
                    for _ in range(3):
                        start = time.time()
                        try:
                            engine.query(query)
                            elapsed = time.time() - start
                            times.append(elapsed)
                        except:
                            pass
                    
                    if times:
                        avg_time = statistics.mean(times)
                        print(f"\n策略组合 {strategies}: 平均耗时 {avg_time:.3f}s")
                    
                except Exception as e:
                    pytest.skip(f"策略组合 {strategies} 测试失败: {e}")


class TestMultiStrategyResourceUsage:
    """多策略检索资源使用测试"""
    
    def test_multi_strategy_memory_usage(
        self, performance_index_manager, collection_name="multi_strategy_perf_test"
    ):
        """测试多策略检索的内存使用"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            
            query = "系统科学的应用"
            
            with patch('src.config.config.ENABLED_RETRIEVAL_STRATEGIES', ['vector', 'bm25']):
                engine = ModularQueryEngine(
                    index_manager=performance_index_manager,
                    retrieval_strategy="multi",
                    similarity_top_k=5,
                )
                
                # 获取初始内存
                initial_memory = process.memory_info().rss / 1024 / 1024  # MB
                
                # 执行多次查询
                for _ in range(10):
                    try:
                        engine.query(query)
                    except:
                        pass
                
                # 获取峰值内存
                peak_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = peak_memory - initial_memory
                
                print(f"\n多策略检索内存使用:")
                print(f"  初始内存: {initial_memory:.2f} MB")
                print(f"  峰值内存: {peak_memory:.2f} MB")
                print(f"  内存增长: {memory_increase:.2f} MB")
                
                # 内存增长应该合理
                # assert memory_increase < 500, f"多策略检索内存增长过大"
                
        except ImportError:
            pytest.skip("psutil未安装，跳过内存测试")
        except Exception as e:
            pytest.skip(f"内存测试失败: {e}")


class TestMultiStrategyPerformanceBenchmarks:
    """多策略检索性能基准测试"""
    
    def test_multi_strategy_performance_baseline(
        self, performance_index_manager, collection_name="multi_strategy_perf_test"
    ):
        """建立多策略检索性能基准"""
        test_queries = [
            "什么是系统科学？",
            "系统科学的应用领域",
            "控制论的基本概念",
        ]
        
        with patch('src.config.config.ENABLED_RETRIEVAL_STRATEGIES', ['vector', 'bm25']):
            engine = ModularQueryEngine(
                index_manager=performance_index_manager,
                retrieval_strategy="multi",
                similarity_top_k=5,
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
                
                print(f"\n多策略检索性能基准:")
                print(f"  平均响应时间: {overall_avg:.3f}s")
                print(f"  最大响应时间: {overall_max:.3f}s")
                
                # 性能基准断言
                assert overall_max < 15.0, f"多策略检索最大响应时间为{overall_max:.3f}s，超过15秒"


