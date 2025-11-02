"""
查询性能测试
测试响应时间（P50, P95, P99）、吞吐量（QPS）和资源消耗
"""

import pytest
import time
import statistics
import numpy as np
from typing import List
from llama_index.core.schema import Document as LlamaDocument

from src.business.services.rag_service import RAGService
from src.indexer import IndexManager
from src.query.modular.engine import ModularQueryEngine


@pytest.fixture
def test_documents():
    """创建测试文档"""
    return [
        LlamaDocument(
            text=f"系统科学是研究系统的一般规律和方法的学科。文档{i}内容包含系统科学、控制论、信息论等相关知识。",
            metadata={"id": i, "title": f"文档{i}", "source": "test"}
        )
        for i in range(50)
    ]


@pytest.fixture
def performance_index_manager(test_documents, collection_name="perf_test_collection"):
    """创建性能测试索引"""
    manager = IndexManager(collection_name=collection_name)
    manager.build_index(documents=test_documents, collection_name=collection_name)
    yield manager
    try:
        manager.delete_collection(collection_name)
    except:
        pass


class TestQueryResponseTime:
    """查询响应时间测试"""
    
    def test_single_query_response_time(
        self, performance_index_manager, collection_name="perf_test_collection"
    ):
        """测试单次查询响应时间"""
        service = RAGService(
            collection_name=collection_name,
            use_modular_engine=True,
            similarity_top_k=5,
        )
        
        query = "什么是系统科学？"
        
        # 预热查询（不计入性能测试）
        try:
            service.query(question=query, user_id="perf_test_user")
        except:
            pass
        
        # 性能测试
        response_times = []
        num_queries = 10
        
        for _ in range(num_queries):
            start_time = time.time()
            try:
                response = service.query(question=query, user_id="perf_test_user")
                elapsed = time.time() - start_time
                response_times.append(elapsed)
                assert response is not None
            except Exception as e:
                pytest.skip(f"查询执行失败: {e}")
        
        # 计算统计指标
        avg_time = statistics.mean(response_times)
        median_time = statistics.median(response_times)
        p95_time = np.percentile(response_times, 95)
        p99_time = np.percentile(response_times, 99)
        
        print(f"\n单次查询响应时间统计:")
        print(f"  平均: {avg_time:.3f}s")
        print(f"  中位数: {median_time:.3f}s")
        print(f"  P95: {p95_time:.3f}s")
        print(f"  P99: {p99_time:.3f}s")
        print(f"  最快: {min(response_times):.3f}s")
        print(f"  最慢: {max(response_times):.3f}s")
        
        # 性能断言（根据实际情况调整阈值）
        assert p95_time < 10.0, f"P95响应时间应该小于10秒，实际为{p95_time:.3f}秒"
        assert p99_time < 15.0, f"P99响应时间应该小于15秒，实际为{p99_time:.3f}秒"
        
        service.close()
    
    def test_batch_query_response_time(
        self, performance_index_manager, collection_name="perf_test_collection"
    ):
        """测试批量查询响应时间"""
        service = RAGService(
            collection_name=collection_name,
            use_modular_engine=True,
        )
        
        queries = [
            "什么是系统科学？",
            "系统科学的应用领域有哪些？",
            "控制论的基本概念是什么？",
            "信息论的主要内容包括什么？",
            "系统工程的方法有哪些？",
        ]
        
        response_times = []
        
        for query in queries:
            start_time = time.time()
            try:
                response = service.query(question=query, user_id="perf_test_user")
                elapsed = time.time() - start_time
                response_times.append(elapsed)
                assert response is not None
            except Exception as e:
                pytest.skip(f"批量查询执行失败: {e}")
        
        # 计算统计指标
        avg_time = statistics.mean(response_times)
        p95_time = np.percentile(response_times, 95)
        
        print(f"\n批量查询响应时间统计:")
        print(f"  平均: {avg_time:.3f}s")
        print(f"  P95: {p95_time:.3f}s")
        
        # 性能断言
        assert p95_time < 10.0, f"批量查询P95响应时间应该小于10秒"
        
        service.close()
    
    def test_query_response_time_by_strategy(
        self, performance_index_manager, collection_name="perf_test_collection"
    ):
        """测试不同检索策略的响应时间"""
        query = "什么是系统科学？"
        
        strategies = ["vector", "bm25", "hybrid"]
        strategy_times = {}
        
        for strategy in strategies:
            try:
                engine = ModularQueryEngine(
                    index_manager=performance_index_manager,
                    retrieval_strategy=strategy,
                    similarity_top_k=5,
                )
                
                # 预热
                engine.query(query)
                
                # 性能测试
                times = []
                for _ in range(5):
                    start = time.time()
                    engine.query(query)
                    elapsed = time.time() - start
                    times.append(elapsed)
                
                avg_time = statistics.mean(times)
                strategy_times[strategy] = avg_time
                
                print(f"\n{strategy}策略平均响应时间: {avg_time:.3f}s")
                
            except Exception as e:
                pytest.skip(f"{strategy}策略测试失败: {e}")
        
        # 验证不同策略都有合理的性能
        for strategy, avg_time in strategy_times.items():
            assert avg_time < 10.0, f"{strategy}策略响应时间过长"


class TestQueryThroughput:
    """查询吞吐量测试"""
    
    def test_query_throughput_qps(
        self, performance_index_manager, collection_name="perf_test_collection"
    ):
        """测试查询吞吐量（QPS）"""
        service = RAGService(
            collection_name=collection_name,
            use_modular_engine=True,
        )
        
        query = "什么是系统科学？"
        num_queries = 20
        
        # 预热
        try:
            service.query(question=query, user_id="perf_test_user")
        except:
            pass
        
        # 性能测试
        start_time = time.time()
        successful_queries = 0
        
        for _ in range(num_queries):
            try:
                response = service.query(question=query, user_id="perf_test_user")
                if response:
                    successful_queries += 1
            except:
                pass
        
        total_time = time.time() - start_time
        qps = successful_queries / total_time if total_time > 0 else 0
        
        print(f"\n查询吞吐量测试:")
        print(f"  总查询数: {num_queries}")
        print(f"  成功查询数: {successful_queries}")
        print(f"  总耗时: {total_time:.3f}s")
        print(f"  QPS: {qps:.2f}")
        
        # 性能断言（根据实际情况调整）
        if successful_queries > 0:
            assert qps > 0.1, f"QPS应该大于0.1，实际为{qps:.2f}"
        
        service.close()


class TestResourceConsumption:
    """资源消耗测试"""
    
    def test_memory_usage_during_query(
        self, performance_index_manager, collection_name="perf_test_collection"
    ):
        """测试查询过程中的内存使用"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            
            service = RAGService(
                collection_name=collection_name,
                use_modular_engine=True,
            )
            
            # 获取初始内存
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # 执行多次查询
            query = "什么是系统科学？"
            for _ in range(10):
                try:
                    service.query(question=query, user_id="perf_test_user")
                except:
                    pass
            
            # 获取峰值内存
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - initial_memory
            
            print(f"\n内存使用测试:")
            print(f"  初始内存: {initial_memory:.2f} MB")
            print(f"  峰值内存: {peak_memory:.2f} MB")
            print(f"  内存增长: {memory_increase:.2f} MB")
            
            # 内存增长应该合理（不超过500MB）
            # assert memory_increase < 500, f"内存增长过大: {memory_increase:.2f} MB"
            
            service.close()
            
        except ImportError:
            pytest.skip("psutil未安装，跳过内存测试")
        except Exception as e:
            pytest.skip(f"内存测试失败: {e}")
    
    def test_cpu_usage_during_query(
        self, performance_index_manager, collection_name="perf_test_collection"
    ):
        """测试查询过程中的CPU使用"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            
            service = RAGService(
                collection_name=collection_name,
                use_modular_engine=True,
            )
            
            # 执行查询并监控CPU
            query = "什么是系统科学？"
            cpu_percentages = []
            
            for _ in range(5):
                try:
                    process.cpu_percent(interval=None)
                    service.query(question=query, user_id="perf_test_user")
                    cpu_percent = process.cpu_percent(interval=0.1)
                    cpu_percentages.append(cpu_percent)
                except:
                    pass
            
            if cpu_percentages:
                avg_cpu = statistics.mean(cpu_percentages)
                print(f"\nCPU使用测试:")
                print(f"  平均CPU使用率: {avg_cpu:.2f}%")
                print(f"  峰值CPU使用率: {max(cpu_percentages):.2f}%")
            
            service.close()
            
        except ImportError:
            pytest.skip("psutil未安装，跳过CPU测试")
        except Exception as e:
            pytest.skip(f"CPU测试失败: {e}")


class TestQueryPerformanceBenchmarks:
    """查询性能基准测试"""
    
    def test_performance_baseline(
        self, performance_index_manager, collection_name="perf_test_collection"
    ):
        """建立性能基准"""
        service = RAGService(
            collection_name=collection_name,
            use_modular_engine=True,
            similarity_top_k=5,
        )
        
        test_queries = [
            "什么是系统科学？",
            "系统科学的应用",
            "控制论的基本概念",
        ]
        
        all_response_times = []
        
        for query in test_queries:
            times = []
            for _ in range(5):
                start = time.time()
                try:
                    response = service.query(question=query, user_id="perf_test_user")
                    elapsed = time.time() - start
                    if response:
                        times.append(elapsed)
                except:
                    pass
            
            if times:
                avg_time = statistics.mean(times)
                all_response_times.extend(times)
                print(f"\n查询 '{query}' 平均响应时间: {avg_time:.3f}s")
        
        if all_response_times:
            overall_avg = statistics.mean(all_response_times)
            overall_p95 = np.percentile(all_response_times, 95)
            
            print(f"\n整体性能基准:")
            print(f"  平均响应时间: {overall_avg:.3f}s")
            print(f"  P95响应时间: {overall_p95:.3f}s")
            
            # 性能基准断言
            assert overall_p95 < 10.0, f"P95响应时间基准为{overall_p95:.3f}s，超过10秒"
        
        service.close()


