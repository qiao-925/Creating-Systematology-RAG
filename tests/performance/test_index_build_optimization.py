#!/usr/bin/env python3
"""
索引构建流程优化性能测试

测试场景：
1. 批量插入性能测试（10/50/100/500个文档）
2. 向量ID查询性能测试
3. 增量更新性能测试
4. 内存使用情况

运行方式：
    python -m pytest tests/performance/test_index_build_optimization.py -v
    或
    python tests/performance/test_index_build_optimization.py
"""

import os
import sys
import time
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
import statistics

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from llama_index.core.schema import Document as LlamaDocument
from src.indexer import IndexManager
from src.config import config


def create_test_documents(count: int, doc_size: int = 500) -> List[LlamaDocument]:
    """创建测试文档
    
    Args:
        count: 文档数量
        doc_size: 每个文档的字符数
        
    Returns:
        文档列表
    """
    documents = []
    base_text = "这是一个测试文档。内容用于测试索引构建性能。" * 20
    
    for i in range(count):
        doc_text = f"文档{i} - {base_text}"[:doc_size]
        doc = LlamaDocument(
            text=doc_text,
            metadata={
                "file_path": f"test/doc_{i}.md",
                "file_name": f"doc_{i}.md",
                "source_type": "test",
                "index": i,
            },
            id_=f"test_doc_{i}"
        )
        documents.append(doc)
    
    return documents


def measure_time(func, *args, **kwargs):
    """测量函数执行时间
    
    Returns:
        (结果, 耗时秒数)
    """
    start_time = time.time()
    result = func(*args, **kwargs)
    elapsed = time.time() - start_time
    return result, elapsed


class PerformanceTestSuite:
    """性能测试套件"""
    
    def __init__(self):
        self.test_dir = None
        self.results = []
        
    def setup(self):
        """设置测试环境"""
        # 创建临时目录用于测试
        self.test_dir = Path(tempfile.mkdtemp(prefix="index_perf_test_"))
        print(f"📁 测试目录: {self.test_dir}")
        
    def teardown(self):
        """清理测试环境"""
        if self.test_dir and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            print(f"🧹 已清理测试目录")
    
    def test_batch_insert_performance(self):
        """测试批量插入性能"""
        print("\n" + "="*60)
        print("📊 测试1: 批量插入性能测试")
        print("="*60)
        
        test_cases = [
            (10, "小批量"),
            (50, "中批量"),
            (100, "大批量"),
            (500, "超大批量"),
        ]
        
        results = []
        
        for doc_count, label in test_cases:
            print(f"\n🔨 测试 {label} ({doc_count} 个文档)...")
            
            # 创建测试集合（每次测试使用新的集合）
            collection_name = f"perf_test_{doc_count}_{int(time.time())}"
            index_manager = IndexManager(
                collection_name=collection_name,
                persist_dir=self.test_dir / f"vector_store_{doc_count}",
                embed_model_instance=None,  # 使用默认模型
            )
            
            # 创建测试文档
            documents = create_test_documents(doc_count)
            
            # 测试批量插入性能
            result, elapsed = measure_time(
                index_manager.build_index,
                documents,
                show_progress=False
            )
            
            # 获取统计信息
            stats = index_manager.get_stats()
            vector_count = stats.get('document_count', 0)
            
            # 计算平均每个文档耗时
            avg_time_per_doc = elapsed / doc_count if doc_count > 0 else 0
            avg_time_per_vector = elapsed / vector_count if vector_count > 0 else 0
            
            result_data = {
                "test_name": f"批量插入-{label}",
                "doc_count": doc_count,
                "vector_count": vector_count,
                "total_time": elapsed,
                "avg_time_per_doc": avg_time_per_doc,
                "avg_time_per_vector": avg_time_per_vector,
                "throughput_docs_per_sec": doc_count / elapsed if elapsed > 0 else 0,
            }
            results.append(result_data)
            
            print(f"✅ 完成: {doc_count} 个文档, {vector_count} 个向量")
            print(f"   总耗时: {elapsed:.2f}s")
            print(f"   平均每文档: {avg_time_per_doc:.3f}s")
            print(f"   平均每向量: {avg_time_per_vector:.3f}s")
            print(f"   吞吐量: {result_data['throughput_docs_per_sec']:.2f} 文档/秒")
            
            # 清理
            index_manager.clear_index()
        
        self.results.extend(results)
        return results
    
    def test_incremental_update_performance(self):
        """测试增量更新性能"""
        print("\n" + "="*60)
        print("📊 测试2: 增量更新性能测试")
        print("="*60)
        
        collection_name = f"perf_test_incremental_{int(time.time())}"
        index_manager = IndexManager(
            collection_name=collection_name,
            persist_dir=self.test_dir / "vector_store_incremental",
            embed_model_instance=None,
        )
        
        # 初始加载50个文档
        initial_docs = create_test_documents(50)
        print(f"\n📥 初始加载: 50 个文档...")
        result, initial_elapsed = measure_time(
            index_manager.build_index,
            initial_docs,
            show_progress=False
        )
        print(f"✅ 初始加载完成: {initial_elapsed:.2f}s")
        
        # 测试增量添加
        incremental_sizes = [10, 25, 50]
        results = []
        
        for add_count in incremental_sizes:
            print(f"\n➕ 增量添加: {add_count} 个文档...")
            
            new_docs = create_test_documents(add_count)
            # 修改metadata以避免ID冲突
            for i, doc in enumerate(new_docs):
                doc.metadata["file_path"] = f"test/incremental_doc_{add_count}_{i}.md"
                doc.id_ = f"test_incremental_{add_count}_{i}"
            
            result, add_elapsed = measure_time(
                index_manager.build_index,
                new_docs,
                show_progress=False
            )
            
            stats = index_manager.get_stats()
            vector_count = stats.get('document_count', 0)
            
            result_data = {
                "test_name": f"增量更新-添加{add_count}个",
                "doc_count": add_count,
                "vector_count": vector_count,
                "total_time": add_elapsed,
                "avg_time_per_doc": add_elapsed / add_count if add_count > 0 else 0,
                "throughput_docs_per_sec": add_count / add_elapsed if add_elapsed > 0 else 0,
            }
            results.append(result_data)
            
            print(f"✅ 增量添加完成: {add_count} 个文档")
            print(f"   耗时: {add_elapsed:.2f}s")
            print(f"   平均每文档: {result_data['avg_time_per_doc']:.3f}s")
            print(f"   当前向量总数: {vector_count}")
        
        self.results.extend(results)
        return results
    
    def test_vector_id_query_performance(self):
        """测试向量ID查询性能"""
        print("\n" + "="*60)
        print("📊 测试3: 向量ID查询性能测试")
        print("="*60)
        
        collection_name = f"perf_test_query_{int(time.time())}"
        index_manager = IndexManager(
            collection_name=collection_name,
            persist_dir=self.test_dir / "vector_store_query",
            embed_model_instance=None,
        )
        
        # 创建100个测试文档
        doc_count = 100
        documents = create_test_documents(doc_count)
        
        print(f"\n📥 准备测试数据: {doc_count} 个文档...")
        index_manager.build_index(documents, show_progress=False)
        
        # 测试单个查询
        print(f"\n🔍 测试单个查询...")
        file_paths = [doc.metadata.get("file_path") for doc in documents[:10]]
        
        single_query_times = []
        for file_path in file_paths:
            result, elapsed = measure_time(
                index_manager._get_vector_ids_by_metadata,
                file_path
            )
            single_query_times.append(elapsed)
        
        avg_single_query_time = statistics.mean(single_query_times)
        
        # 测试批量查询
        print(f"\n🔍 测试批量查询 (100个路径)...")
        all_file_paths = [doc.metadata.get("file_path") for doc in documents]
        
        result, batch_query_time = measure_time(
            index_manager._get_vector_ids_batch,
            all_file_paths
        )
        
        result_data = {
            "test_name": "向量ID查询",
            "single_query_count": 10,
            "avg_single_query_time": avg_single_query_time,
            "batch_query_count": doc_count,
            "batch_query_time": batch_query_time,
            "speedup": (avg_single_query_time * doc_count) / batch_query_time if batch_query_time > 0 else 0,
        }
        
        print(f"✅ 单次查询平均耗时: {avg_single_query_time*1000:.2f}ms")
        print(f"✅ 批量查询耗时: {batch_query_time:.2f}s (100个路径)")
        print(f"✅ 性能提升: {result_data['speedup']:.2f}x")
        
        self.results.append(result_data)
        return result_data
    
    def run_all_tests(self):
        """运行所有测试"""
        print("\n" + "="*60)
        print("🚀 开始性能测试")
        print("="*60)
        
        try:
            self.setup()
            
            # 运行所有测试
            self.test_batch_insert_performance()
            self.test_incremental_update_performance()
            self.test_vector_id_query_performance()
            
            # 生成报告
            self.generate_report()
            
        finally:
            self.teardown()
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "="*60)
        print("📋 性能测试报告")
        print("="*60)
        
        if not self.results:
            print("⚠️  没有测试结果")
            return
        
        # 批量插入性能汇总
        insert_results = [r for r in self.results if "批量插入" in r.get("test_name", "")]
        if insert_results:
            print("\n📊 批量插入性能汇总:")
            print(f"{'文档数':<10} {'总耗时(s)':<12} {'平均(ms/文档)':<15} {'吞吐量(文档/s)':<15}")
            print("-" * 60)
            for r in sorted(insert_results, key=lambda x: x["doc_count"]):
                print(
                    f"{r['doc_count']:<10} "
                    f"{r['total_time']:<12.2f} "
                    f"{r['avg_time_per_doc']*1000:<15.2f} "
                    f"{r['throughput_docs_per_sec']:<15.2f}"
                )
        
        # 增量更新性能汇总
        incremental_results = [r for r in self.results if "增量更新" in r.get("test_name", "")]
        if incremental_results:
            print("\n📊 增量更新性能汇总:")
            print(f"{'添加数':<10} {'总耗时(s)':<12} {'平均(ms/文档)':<15} {'吞吐量(文档/s)':<15}")
            print("-" * 60)
            for r in sorted(incremental_results, key=lambda x: x["doc_count"]):
                print(
                    f"{r['doc_count']:<10} "
                    f"{r['total_time']:<12.2f} "
                    f"{r['avg_time_per_doc']*1000:<15.2f} "
                    f"{r['throughput_docs_per_sec']:<15.2f}"
                )
        
        # 查询性能汇总
        query_results = [r for r in self.results if "向量ID查询" in r.get("test_name", "")]
        if query_results:
            print("\n📊 向量ID查询性能汇总:")
            for r in query_results:
                print(f"   单次查询平均: {r['avg_single_query_time']*1000:.2f}ms")
                print(f"   批量查询 ({r['batch_query_count']}个): {r['batch_query_time']:.2f}s")
                print(f"   性能提升: {r['speedup']:.2f}x")
        
        # 性能分析
        print("\n📈 性能分析:")
        
        if insert_results:
            # 计算不同文档数的性能趋势
            doc_counts = sorted([r["doc_count"] for r in insert_results])
            times_per_doc = [
                r["avg_time_per_doc"] * 1000
                for r in sorted(insert_results, key=lambda x: x["doc_count"])
            ]
            
            if len(doc_counts) >= 2:
                # 检查是否存在性能下降趋势
                first_time = times_per_doc[0]
                last_time = times_per_doc[-1]
                if last_time < first_time * 1.5:
                    print("   ✅ 批量插入性能稳定，无明显性能下降")
                else:
                    print("   ⚠️  大批量插入时性能有所下降，建议分批处理")
        
        print("\n✅ 性能测试完成!")
        
        # 保存详细结果到文件
        report_file = project_root / "agent-task-log" / "索引构建性能测试报告.md"
        self.save_detailed_report(report_file)
        print(f"\n📄 详细报告已保存: {report_file}")
    
    def save_detailed_report(self, report_file: Path):
        """保存详细报告到文件"""
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# 索引构建性能测试报告\n\n")
            f.write(f"**测试时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # 批量插入结果
            insert_results = [r for r in self.results if "批量插入" in r.get("test_name", "")]
            if insert_results:
                f.write("## 批量插入性能测试\n\n")
                f.write("| 文档数 | 向量数 | 总耗时(s) | 平均(ms/文档) | 吞吐量(文档/s) |\n")
                f.write("|--------|--------|-----------|---------------|----------------|\n")
                for r in sorted(insert_results, key=lambda x: x["doc_count"]):
                    f.write(
                        f"| {r['doc_count']} | {r.get('vector_count', 'N/A')} | "
                        f"{r['total_time']:.2f} | {r['avg_time_per_doc']*1000:.2f} | "
                        f"{r['throughput_docs_per_sec']:.2f} |\n"
                    )
                f.write("\n")
            
            # 增量更新结果
            incremental_results = [r for r in self.results if "增量更新" in r.get("test_name", "")]
            if incremental_results:
                f.write("## 增量更新性能测试\n\n")
                f.write("| 添加文档数 | 总耗时(s) | 平均(ms/文档) | 吞吐量(文档/s) |\n")
                f.write("|-----------|-----------|---------------|----------------|\n")
                for r in sorted(incremental_results, key=lambda x: x["doc_count"]):
                    f.write(
                        f"| {r['doc_count']} | {r['total_time']:.2f} | "
                        f"{r['avg_time_per_doc']*1000:.2f} | {r['throughput_docs_per_sec']:.2f} |\n"
                    )
                f.write("\n")
            
            # 查询结果
            query_results = [r for r in self.results if "向量ID查询" in r.get("test_name", "")]
            if query_results:
                f.write("## 向量ID查询性能测试\n\n")
                for r in query_results:
                    f.write(f"- **单次查询平均耗时**: {r['avg_single_query_time']*1000:.2f}ms\n")
                    f.write(f"- **批量查询耗时**: {r['batch_query_time']:.2f}s ({r['batch_query_count']}个路径)\n")
                    f.write(f"- **性能提升**: {r['speedup']:.2f}x\n")
                f.write("\n")


def main():
    """主函数"""
    print("="*60)
    print("🔬 索引构建流程优化 - 性能测试")
    print("="*60)
    print("\n注意事项:")
    print("1. 首次运行会下载Embedding模型，可能需要较长时间")
    print("2. 测试会在临时目录创建索引，测试完成后自动清理")
    print("3. 建议在CPU和内存充足的机器上运行")
    print("\n开始测试...\n")
    
    suite = PerformanceTestSuite()
    suite.run_all_tests()


if __name__ == "__main__":
    main()

