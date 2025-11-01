#!/usr/bin/env python3
"""
模块化RAG测试脚本
用于测试和对比不同检索策略
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from llama_index.core.schema import Document as LlamaDocument
from src.modular_query_engine import ModularQueryEngine
from src.indexer import IndexManager


def create_test_index():
    """创建测试索引"""
    print("="*60)
    print("📚 创建测试索引")
    print("="*60)
    
    docs = [
        LlamaDocument(
            text="系统科学是20世纪中期兴起的一门新兴学科，它研究系统的一般规律和方法。系统科学包括系统论、控制论、信息论等多个分支。",
            metadata={"title": "系统科学概述", "source": "test", "file_name": "系统科学.md"}
        ),
        LlamaDocument(
            text="钱学森（1911-2009）是中国著名科学家，被誉为\"中国航天之父\"。他在系统工程和系统科学领域做出了杰出贡献，提出了开放的复杂巨系统理论。",
            metadata={"title": "钱学森生平", "source": "test", "file_name": "钱学森.md"}
        ),
        LlamaDocument(
            text="系统工程是一种组织管理技术，用于解决大规模复杂系统的设计和实施问题。钱学森将系统工程引入中国，并结合中国实际进行了创新性发展。",
            metadata={"title": "系统工程简介", "source": "test", "file_name": "系统工程.md"}
        ),
        LlamaDocument(
            text="控制论是研究系统控制和调节的科学。维纳（Wiener）在1948年提出了控制论的基本概念，强调反馈机制在系统中的重要作用。",
            metadata={"title": "控制论", "source": "test", "file_name": "控制论.md"}
        ),
        LlamaDocument(
            text="信息论是研究信息的量化、存储、传输和处理的理论。香农（Shannon）在1948年奠定了信息论的数学基础。",
            metadata={"title": "信息论", "source": "test", "file_name": "信息论.md"}
        ),
    ]
    
    manager = IndexManager(collection_name="test_modular_rag_demo")
    manager.build_index(docs)
    print(f"✅ 索引创建完成，共 {len(docs)} 个文档\n")
    
    return manager


def test_vector_strategy(index_manager):
    """测试向量检索策略"""
    print("\n" + "="*60)
    print("🔍 测试1: 向量检索策略 (vector)")
    print("="*60)
    
    engine = ModularQueryEngine(
        index_manager,
        retrieval_strategy="vector",
        similarity_top_k=3,
    )
    
    question = "系统科学是什么？"
    answer, sources, trace = engine.query(question, collect_trace=True)
    
    print(f"\n📊 检索结果:")
    print(f"   检索时间: {trace['retrieval_time']}s")
    print(f"   总时间: {trace['total_time']}s")
    print(f"   找到 {len(sources)} 个来源")
    
    print(f"\n💡 答案（前200字符）:")
    print(f"   {answer[:200]}...")
    
    return {"strategy": "vector", "time": trace['total_time'], "sources": len(sources)}


def test_bm25_strategy(index_manager):
    """测试BM25检索策略"""
    print("\n" + "="*60)
    print("🔍 测试2: BM25检索策略 (bm25)")
    print("="*60)
    
    try:
        engine = ModularQueryEngine(
            index_manager,
            retrieval_strategy="bm25",
            similarity_top_k=3,
        )
        
        question = "钱学森的贡献"
        answer, sources, trace = engine.query(question, collect_trace=True)
        
        print(f"\n📊 检索结果:")
        print(f"   检索时间: {trace['retrieval_time']}s")
        print(f"   总时间: {trace['total_time']}s")
        print(f"   找到 {len(sources)} 个来源")
        
        print(f"\n💡 答案（前200字符）:")
        print(f"   {answer[:200]}...")
        
        return {"strategy": "bm25", "time": trace['total_time'], "sources": len(sources)}
    
    except ImportError as e:
        print(f"\n⚠️  BM25策略不可用: {e}")
        print(f"   请运行: pip install llama-index-retrievers-bm25")
        return {"strategy": "bm25", "error": str(e)}


def test_hybrid_strategy(index_manager):
    """测试混合检索策略"""
    print("\n" + "="*60)
    print("🔍 测试3: 混合检索策略 (hybrid)")
    print("="*60)
    
    try:
        engine = ModularQueryEngine(
            index_manager,
            retrieval_strategy="hybrid",
            similarity_top_k=3,
        )
        
        question = "控制论和信息论的关系"
        answer, sources, trace = engine.query(question, collect_trace=True)
        
        print(f"\n📊 检索结果:")
        print(f"   检索时间: {trace['retrieval_time']}s")
        print(f"   总时间: {trace['total_time']}s")
        print(f"   找到 {len(sources)} 个来源")
        
        print(f"\n💡 答案（前200字符）:")
        print(f"   {answer[:200]}...")
        
        return {"strategy": "hybrid", "time": trace['total_time'], "sources": len(sources)}
    
    except ImportError as e:
        print(f"\n⚠️  混合策略不可用: {e}")
        print(f"   降级为向量检索")
        return {"strategy": "hybrid", "error": str(e)}


def print_summary(results):
    """打印测试总结"""
    print("\n" + "="*60)
    print("📋 测试总结")
    print("="*60)
    
    for result in results:
        if 'error' in result:
            print(f"\n❌ {result['strategy']}: 失败")
            print(f"   原因: {result['error']}")
        else:
            print(f"\n✅ {result['strategy']}:")
            print(f"   总时间: {result['time']}s")
            print(f"   来源数: {result['sources']}")
    
    print("\n" + "="*60)
    print("🎉 测试完成！")
    print("="*60)


def main():
    """主函数"""
    print("\n🚀 模块化RAG测试脚本")
    print("="*60)
    
    # 创建测试索引
    index_manager = create_test_index()
    
    # 测试各策略
    results = []
    results.append(test_vector_strategy(index_manager))
    results.append(test_bm25_strategy(index_manager))
    results.append(test_hybrid_strategy(index_manager))
    
    # 打印总结
    print_summary(results)
    
    # 清理测试索引
    print("\n🧹 清理测试数据...")
    try:
        index_manager.clear_index()
        print("✅ 清理完成")
    except Exception as e:
        print(f"⚠️  清理失败: {e}")


if __name__ == "__main__":
    main()

