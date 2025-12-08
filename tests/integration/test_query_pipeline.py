"""
查询流程集成测试
测试从索引到查询的完整流程
"""

import pytest
from src.infrastructure.indexer import IndexManager
from src.business.rag_engine import QueryEngine


@pytest.mark.integration
class TestQueryPipeline:
    """查询流程集成测试"""
    
    def test_index_to_retrieval_pipeline(self, prepared_index_manager):
        """测试从索引到检索的流程"""
        # 步骤1：验证索引已构建
        stats = prepared_index_manager.get_stats()
        assert stats['document_count'] > 0
        
        # 步骤2：执行检索
        results = prepared_index_manager.search("系统科学", top_k=3)
        
        # 步骤3：验证检索结果
        assert len(results) > 0
        assert all('text' in r for r in results)
        assert all('score' in r for r in results)
        assert all('metadata' in r for r in results)
        
        # 步骤4：验证相似度排序
        scores = [r['score'] for r in results]
        assert scores == sorted(scores, reverse=True), "结果应该按相似度降序排列"
    
    def test_query_with_mock_llm(self, prepared_index_manager, mocker, monkeypatch):
        """测试完整查询流程（使用Mock响应）"""
        # Mock Response 对象
        from llama_index.core.schema import NodeWithScore, TextNode
        
        mock_response = mocker.Mock()
        mock_response.__str__ = mocker.Mock(return_value="系统科学是研究系统的科学。[1]")
        
        # 创建真实的 source_nodes
        test_node = TextNode(
            text="系统科学是研究系统的一般规律和方法的科学。",
            metadata={"title": "系统科学", "source": "test"}
        )
        mock_response.source_nodes = [NodeWithScore(node=test_node, score=0.9)]
        
        # 设置环境变量
        monkeypatch.setenv('DEEPSEEK_API_KEY', 'test_key_for_mock')
        
        # 创建查询引擎
        query_engine = QueryEngine(prepared_index_manager)
        
        # Mock 内部查询引擎的 query 方法
        query_engine.query_engine.query = mocker.Mock(return_value=mock_response)
        
        # 执行查询
        answer, sources, _ = query_engine.query("什么是系统科学？")
        
        # 验证结果
        assert isinstance(answer, str)
        assert len(answer) > 0
        assert isinstance(sources, list)
        assert len(sources) > 0
    
    def test_multiple_queries_same_index(self, prepared_index_manager, mocker, monkeypatch):
        """测试在同一个索引上执行多次查询"""
        # Mock Response 对象
        from llama_index.core.schema import NodeWithScore, TextNode
        
        mock_response = mocker.Mock()
        mock_response.__str__ = mocker.Mock(return_value="测试答案")
        
        # 创建真实的 source_nodes
        test_node = TextNode(
            text="测试内容",
            metadata={"title": "测试", "source": "test"}
        )
        mock_response.source_nodes = [NodeWithScore(node=test_node, score=0.8)]
        
        # 设置环境变量
        monkeypatch.setenv('DEEPSEEK_API_KEY', 'test_key_for_mock')
        
        # 创建查询引擎
        query_engine = QueryEngine(prepared_index_manager)
        
        # Mock 内部查询引擎的 query 方法
        query_engine.query_engine.query = mocker.Mock(return_value=mock_response)
        
        # 多次查询
        questions = [
            "什么是系统科学？",
            "钱学森是谁？",
            "系统工程的特点是什么？"
        ]
        
        for question in questions:
            answer, sources, _ = query_engine.query(question)
            assert isinstance(answer, str)
            assert isinstance(sources, list)


@pytest.mark.integration
class TestQueryRelevance:
    """查询相关性测试"""
    
    def test_retrieval_returns_relevant_documents(self, prepared_index_manager):
        """测试检索返回相关文档"""
        test_cases = [
            ("系统科学", ["系统科学", "系统", "科学"]),
            ("钱学森", ["钱学森"]),
            ("工程", ["工程", "系统工程"])
        ]
        
        for query, keywords in test_cases:
            results = prepared_index_manager.search(query, top_k=3)
            
            # 至少一个结果应该包含关键词
            assert len(results) > 0
            found = any(
                any(kw in r['text'] for kw in keywords)
                for r in results
            )
            assert found, f"查询'{query}'没有找到包含关键词的结果"
    
    def test_retrieval_score_reasonable(self, prepared_index_manager):
        """测试检索分数合理性"""
        results = prepared_index_manager.search("系统科学", top_k=5)
        
        for result in results:
            # 分数应该在合理范围内（0-1之间，或者其他合理范围）
            assert result['score'] >= 0, "相似度分数不应该为负"

