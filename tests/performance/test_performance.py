"""
性能测试
"""

import pytest
import time
from llama_index.core import Document
from src.infrastructure.indexer import IndexManager


@pytest.mark.performance
class TestIndexingPerformance:
    """索引构建性能测试"""
    
    @pytest.fixture
    def generate_documents(self):
        """生成指定数量的测试文档"""
        def _generate(count: int):
            return [
                Document(
                    text=f"这是测试文档{i}的内容。" + "系统科学相关内容。" * 20,
                    metadata={"id": i, "title": f"文档{i}"}
                )
                for i in range(count)
            ]
        return _generate
    
    @pytest.mark.parametrize("doc_count", [10, 50, 100])
    def test_indexing_time_scaling(self, doc_count, generate_documents, temp_vector_store):
        """测试索引时间随文档数量的变化"""
        documents = generate_documents(doc_count)
        
        manager = IndexManager(
            collection_name=f"perf_test_{doc_count}",
            persist_dir=temp_vector_store
        )
        
        start = time.time()
        manager.build_index(documents, show_progress=False)
        duration = time.time() - start
        
        print(f"\n{doc_count}个文档索引耗时: {duration:.2f}秒")
        
        # 基本性能断言（根据实际情况调整）
        assert duration < doc_count * 1.0, f"{doc_count}个文档索引应该在{doc_count}秒内完成"
    
    def test_search_latency(self, temp_vector_store, generate_documents):
        """测试搜索延迟"""
        documents = generate_documents(100)
        
        manager = IndexManager(
            collection_name="search_perf_test",
            persist_dir=temp_vector_store
        )
        manager.build_index(documents, show_progress=False)
        
        # 测试搜索性能
        queries = ["系统科学", "测试文档", "相关内容"]
        latencies = []
        
        for query in queries:
            start = time.time()
            results = manager.search(query, top_k=5)
            latency = time.time() - start
            latencies.append(latency)
            
            assert len(results) > 0
        
        avg_latency = sum(latencies) / len(latencies)
        print(f"\n平均搜索延迟: {avg_latency*1000:.2f}ms")
        
        # 搜索应该很快（< 1秒）
        assert avg_latency < 1.0, "搜索延迟应该小于1秒"


@pytest.mark.performance
class TestMemoryUsage:
    """内存使用测试"""
    
    def test_large_document_handling(self, temp_vector_store):
        """测试处理大文档"""
        # 创建一个大文档（约10KB）
        large_doc = Document(
            text="这是一个很长的文档。" * 1000,
            metadata={"id": 1, "size": "large"}
        )
        
        manager = IndexManager(
            collection_name="large_doc_test",
            persist_dir=temp_vector_store
        )
        
        # 应该能够成功处理
        index = manager.build_index([large_doc], show_progress=False)
        assert index is not None
        
        # 应该能够检索
        results = manager.search("文档", top_k=1)
        assert len(results) > 0

