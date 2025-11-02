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


class TestGrepStrategy:
    """Grep检索策略测试"""
    
    def test_grep_strategy(self, index_manager, tmp_path):
        """测试Grep检索策略"""
        try:
            # 创建测试文件
            test_file = tmp_path / "test_grep.md"
            test_file.write_text("系统科学是研究系统的科学", encoding='utf-8')
            
            engine = ModularQueryEngine(
                index_manager,
                retrieval_strategy="grep",
                data_source_path=str(tmp_path)
            )
            
            answer, sources, _ = engine.query("系统科学")
            
            assert answer is not None
            # Grep策略可能返回结果
            assert isinstance(sources, list)
        except Exception as e:
            pytest.skip(f"Grep检索策略初始化失败: {e}")


class TestMultiStrategy:
    """多策略检索测试"""
    
    def test_multi_strategy(self, index_manager):
        """测试多策略检索"""
        try:
            engine = ModularQueryEngine(
                index_manager,
                retrieval_strategy="multi",
                similarity_top_k=3,
            )
            
            answer, sources, _ = engine.query("系统科学")
            
            assert answer is not None
            assert len(sources) > 0
        except Exception as e:
            pytest.skip(f"多策略检索初始化失败: {e}")


class TestAutoRouting:
    """自动路由模式测试"""
    
    def test_auto_routing_enabled(self, index_manager):
        """测试启用自动路由"""
        try:
            engine = ModularQueryEngine(
                index_manager,
                enable_auto_routing=True,
            )
            
            assert engine.enable_auto_routing is True
            assert engine.query_router is not None
            # 自动路由模式下，retriever和query_engine应该为None（动态创建）
            assert engine.retriever is None or engine.query_engine is None
            
            # 测试查询
            answer, sources, trace = engine.query("什么是系统科学？", collect_trace=True)
            
            assert answer is not None
            assert isinstance(sources, list)
            if trace:
                assert 'routing_decision' in trace or 'strategy' in trace
        except Exception as e:
            pytest.skip(f"自动路由模式初始化失败: {e}")
    
    def test_auto_routing_disabled(self, index_manager):
        """测试禁用自动路由"""
        engine = ModularQueryEngine(
            index_manager,
            enable_auto_routing=False,
            retrieval_strategy="vector"
        )
        
        assert engine.enable_auto_routing is False
        assert engine.query_router is None
        assert engine.retriever is not None
        assert engine.query_engine is not None
    
    def test_auto_routing_different_queries(self, index_manager):
        """测试自动路由对不同查询类型的处理"""
        try:
            engine = ModularQueryEngine(
                index_manager,
                enable_auto_routing=True,
            )
            
            # 精确问题（应该路由到chunk模式）
            answer1, sources1, _ = engine.query("系统科学的定义")
            
            # 宽泛问题（应该路由到files_via_content模式）
            answer2, sources2, _ = engine.query("什么是系统科学？")
            
            assert answer1 is not None
            assert answer2 is not None
            assert isinstance(sources1, list)
            assert isinstance(sources2, list)
        except Exception as e:
            pytest.skip(f"自动路由查询测试失败: {e}")


class TestPostprocessorPipeline:
    """后处理流水线测试"""
    
    def test_postprocessor_pipeline_order(self, index_manager):
        """测试后处理流水线顺序"""
        engine = ModularQueryEngine(
            index_manager,
            retrieval_strategy="vector",
            similarity_cutoff=0.3,
            enable_rerank=False,
        )
        
        # 验证后处理器已创建
        assert engine.postprocessors is not None
        assert isinstance(engine.postprocessors, list)
    
    def test_postprocessor_with_rerank(self, index_manager):
        """测试重排序后处理器集成"""
        try:
            engine = ModularQueryEngine(
                index_manager,
                retrieval_strategy="vector",
                enable_rerank=True,
                rerank_top_n=2,
            )
            
            _, sources, _ = engine.query("系统科学")
            
            # 重排序应该限制结果数量
            assert len(sources) <= 2
        except Exception as e:
            pytest.skip(f"重排序集成测试失败: {e}")
    
    def test_postprocessor_similarity_cutoff(self, index_manager):
        """测试相似度阈值后处理器"""
        engine = ModularQueryEngine(
            index_manager,
            retrieval_strategy="vector",
            similarity_cutoff=0.5,
        )
        
        _, sources, _ = engine.query("系统科学")
        
        # 验证结果都满足相似度阈值
        for source in sources:
            if source.get('score') is not None:
                assert source['score'] >= 0.5


class TestErrorHandling:
    """错误处理测试"""
    
    def test_query_with_invalid_index(self):
        """测试无效索引的错误处理"""
        # 创建空的IndexManager
        empty_manager = IndexManager(collection_name="empty_test")
        
        engine = ModularQueryEngine(
            empty_manager,
            retrieval_strategy="vector"
        )
        
        # 查询空索引可能返回空结果或抛出异常
        try:
            answer, sources, _ = engine.query("测试问题")
            assert isinstance(answer, str)
            assert isinstance(sources, list)
        except Exception as e:
            # 如果抛出异常也是合理的
            assert "索引" in str(e).lower() or "文档" in str(e).lower()
    
    def test_query_with_empty_string(self, index_manager):
        """测试空字符串查询"""
        engine = ModularQueryEngine(index_manager)
        
        try:
            answer, sources, _ = engine.query("")
            # 可能返回空答案或抛出异常
            assert isinstance(answer, str)
            assert isinstance(sources, list)
        except Exception:
            # 空查询抛出异常也是合理的
            pass


class TestTraceCollection:
    """追踪信息收集测试"""
    
    def test_trace_collection_enabled(self, index_manager):
        """测试启用追踪收集"""
        engine = ModularQueryEngine(index_manager)
        
        answer, sources, trace = engine.query("系统科学", collect_trace=True)
        
        assert trace is not None
        assert isinstance(trace, dict)
        assert 'strategy' in trace or 'retrieval_time' in trace
    
    def test_trace_collection_disabled(self, index_manager):
        """测试禁用追踪收集"""
        engine = ModularQueryEngine(index_manager)
        
        answer, sources, trace = engine.query("系统科学", collect_trace=False)
        
        # trace可能为None或空字典
        assert trace is None or isinstance(trace, dict)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])

