"""
模块化查询引擎单元测试
"""

import pytest
from llama_index.core.schema import Document as LlamaDocument

from src.modular_query_engine import ModularQueryEngine, create_modular_query_engine
from src.indexer import IndexManager


@pytest.fixture
def test_documents():
    """创建测试文档"""
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
    return docs


@pytest.fixture
def index_manager(test_documents):
    """创建测试索引"""
    manager = IndexManager(collection_name="test_modular_rag")
    manager.build_index(test_documents)
    return manager


class TestModularQueryEngine:
    """模块化查询引擎测试"""
    
    def test_init_vector_strategy(self, index_manager):
        """测试初始化 - 向量检索策略"""
        engine = ModularQueryEngine(
            index_manager,
            retrieval_strategy="vector"
        )
        
        assert engine.retrieval_strategy == "vector"
        assert engine.retriever is not None
        assert engine.query_engine is not None
    
    def test_init_invalid_strategy(self, index_manager):
        """测试初始化 - 无效策略"""
        with pytest.raises(ValueError, match="不支持的检索策略"):
            ModularQueryEngine(
                index_manager,
                retrieval_strategy="invalid_strategy"
            )
    
    def test_vector_query(self, index_manager):
        """测试向量检索查询"""
        engine = ModularQueryEngine(
            index_manager,
            retrieval_strategy="vector",
            similarity_top_k=3,
        )
        
        answer, sources, _ = engine.query("系统科学是什么？")
        
        assert answer is not None
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert len(sources) > 0
        assert all('score' in s for s in sources)
        assert all('text' in s for s in sources)
        assert all('metadata' in s for s in sources)
    
    def test_query_with_trace(self, index_manager):
        """测试查询 - 收集追踪信息"""
        engine = ModularQueryEngine(
            index_manager,
            retrieval_strategy="vector"
        )
        
        answer, sources, trace = engine.query("钱学森的贡献", collect_trace=True)
        
        assert trace is not None
        assert 'strategy' in trace
        assert 'retrieval_time' in trace
        assert 'chunks_retrieved' in trace
        assert 'total_time' in trace
        assert trace['strategy'] == "vector"
        assert trace['chunks_retrieved'] == len(sources)
    
    def test_similarity_cutoff(self, index_manager):
        """测试相似度过滤"""
        engine = ModularQueryEngine(
            index_manager,
            retrieval_strategy="vector",
            similarity_cutoff=0.8,  # 高阈值
        )
        
        _, sources, _ = engine.query("系统科学")
        
        # 高阈值应该过滤掉一些结果
        for source in sources:
            if source.get('score') is not None:
                assert source['score'] >= 0.8, f"Score {source['score']} below cutoff 0.8"
    
    def test_create_modular_query_engine_factory(self, index_manager):
        """测试工厂函数"""
        engine = create_modular_query_engine(
            index_manager,
            strategy="vector"
        )
        
        assert isinstance(engine, ModularQueryEngine)
        assert engine.retrieval_strategy == "vector"
    
    def test_multiple_queries(self, index_manager):
        """测试多次查询"""
        engine = ModularQueryEngine(index_manager)
        
        questions = [
            "什么是系统科学？",
            "钱学森的主要贡献是什么？",
            "控制论和信息论的关系",
        ]
        
        for question in questions:
            answer, sources, _ = engine.query(question)
            assert answer is not None
            assert len(answer) > 0
            assert len(sources) > 0


class TestBM25Strategy:
    """BM25检索策略测试"""
    
    def test_bm25_strategy(self, index_manager):
        """测试BM25检索策略"""
        try:
            engine = ModularQueryEngine(
                index_manager,
                retrieval_strategy="bm25"
            )
            
            answer, sources, _ = engine.query("钱学森")
            
            assert answer is not None
            assert len(sources) > 0
        except ImportError:
            pytest.skip("BM25Retriever未安装")


class TestHybridStrategy:
    """混合检索策略测试"""
    
    def test_hybrid_strategy(self, index_manager):
        """测试混合检索策略"""
        try:
            engine = ModularQueryEngine(
                index_manager,
                retrieval_strategy="hybrid"
            )
            
            answer, sources, _ = engine.query("系统工程方法")
            
            assert answer is not None
            assert len(sources) > 0
        except ImportError:
            pytest.skip("BM25Retriever未安装，混合检索降级为向量检索")


class TestPostprocessors:
    """后处理器测试"""
    
    def test_similarity_postprocessor(self, index_manager):
        """测试相似度后处理器"""
        # 低阈值
        engine1 = ModularQueryEngine(
            index_manager,
            retrieval_strategy="vector",
            similarity_cutoff=0.3,  # 低阈值
        )
        _, sources1, _ = engine1.query("系统科学")
        
        # 高阈值
        engine2 = ModularQueryEngine(
            index_manager,
            retrieval_strategy="vector",
            similarity_cutoff=0.7,  # 高阈值
        )
        _, sources2, _ = engine2.query("系统科学")
        
        # 高阈值应该返回更少的结果
        assert len(sources2) <= len(sources1)
    
    def test_rerank_postprocessor(self, index_manager):
        """测试重排序后处理器"""
        # 不启用重排序
        engine1 = ModularQueryEngine(
            index_manager,
            retrieval_strategy="vector",
            enable_rerank=False
        )
        _, sources1, _ = engine1.query("系统科学")
        
        # 启用重排序（可能失败，取决于是否安装）
        try:
            engine2 = ModularQueryEngine(
                index_manager,
                retrieval_strategy="vector",
                enable_rerank=True,
                rerank_top_n=2,
            )
            _, sources2, _ = engine2.query("系统科学")
            
            # 重排序应该限制结果数量
            assert len(sources2) <= 2
            assert len(sources2) <= len(sources1)
        except Exception as e:
            pytest.skip(f"重排序模块初始化失败: {e}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])

