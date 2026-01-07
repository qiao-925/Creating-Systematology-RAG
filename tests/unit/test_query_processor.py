"""
查询处理器单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from backend.business.rag_engine.processing.query_processor import QueryProcessor, reset_query_processor


@pytest.fixture
def mock_llm():
    """创建Mock LLM"""
    llm = Mock()
    return llm


@pytest.fixture
def query_processor(mock_llm):
    """创建查询处理器实例"""
    processor = QueryProcessor(llm=mock_llm)
    processor._llm_initialized = True
    return processor


@pytest.fixture
def sample_understanding_response():
    """示例意图理解响应"""
    return {
        "understanding": {
            "query_type": "factual",
            "complexity": "medium",
            "entities": ["系统科学", "RAG"],
            "intent": "查询系统科学的定义",
            "confidence": 0.85
        },
        "rewritten_queries": [
            "系统科学 定义 概念",
            "系统科学是什么"
        ]
    }


class TestQueryProcessor:
    """查询处理器测试"""
    
    def test_init(self):
        """测试初始化"""
        processor = QueryProcessor()
        assert processor._cache == {}
        assert processor._cache_size == 100
        assert processor._llm_initialized is False
    
    def test_assess_complexity_simple(self, query_processor):
        """测试简单查询复杂度评估"""
        # 短查询
        assert query_processor._assess_complexity_simple("什么是系统科学") == "simple"
        
        # 文件名查询
        assert query_processor._assess_complexity_simple("README.md文件") == "simple"
        
        # 复杂查询
        complex_query = "系统科学和复杂性理论在研究方法上的异同点是什么？它们各自的发展历史如何？"
        assert query_processor._assess_complexity_simple(complex_query) == "complex"
        
        # 中等查询
        medium_query = "介绍一下系统科学的发展历程"
        assert query_processor._assess_complexity_simple(medium_query) == "medium"
    
    def test_process_simple_query(self, query_processor):
        """测试简单查询处理（不走LLM）"""
        simple_query = "什么是系统科学"
        
        result = query_processor.process(simple_query)
        
        assert result["original_query"] == simple_query
        assert result["final_query"] == simple_query
        assert result["processing_method"] == "simple"
        assert result["rewritten_queries"] == [simple_query]
        assert result.get("understanding") is None
    
    def test_process_complex_query(
        self, 
        query_processor, 
        mock_llm, 
        sample_understanding_response
    ):
        """测试复杂查询处理（走LLM）"""
        complex_query = "系统科学和复杂性理论的关系是什么"
        
        # Mock LLM响应
        mock_response = Mock()
        mock_response.text = json.dumps(sample_understanding_response)
        mock_llm.complete.return_value = mock_response
        
        result = query_processor.process(complex_query, force_llm=True)
        
        assert result["original_query"] == complex_query
        assert result["processing_method"] == "llm"
        assert result["understanding"] == sample_understanding_response["understanding"]
        assert len(result["rewritten_queries"]) > 0
        assert result["final_query"] == sample_understanding_response["rewritten_queries"][0]
        
        # 验证LLM被调用
        mock_llm.complete.assert_called_once()
    
    def test_process_llm_failure(self, query_processor, mock_llm):
        """测试LLM失败时的降级处理"""
        complex_query = "系统科学和复杂性理论的关系"
        
        # Mock LLM失败
        mock_llm.complete.side_effect = Exception("LLM调用失败")
        
        result = query_processor.process(complex_query, force_llm=True)
        
        assert result["processing_method"] == "llm_failed"
        assert result["final_query"] == complex_query
        assert result["rewritten_queries"] == [complex_query]
    
    def test_process_json_parse_error(self, query_processor, mock_llm):
        """测试JSON解析失败"""
        complex_query = "测试查询"
        
        # Mock无效JSON响应
        mock_response = Mock()
        mock_response.text = "这不是JSON格式"
        mock_llm.complete.return_value = mock_response
        
        result = query_processor.process(complex_query, force_llm=True)
        
        assert result["processing_method"] == "llm_failed"
        assert result["final_query"] == complex_query
    
    def test_process_json_with_markdown(self, query_processor, mock_llm):
        """测试包含Markdown代码块的JSON响应"""
        complex_query = "测试查询"
        
        # Mock包含markdown的JSON响应
        json_content = json.dumps({
            "understanding": {"query_type": "factual"},
            "rewritten_queries": ["改写查询"]
        })
        mock_response = Mock()
        mock_response.text = f"```json\n{json_content}\n```"
        mock_llm.complete.return_value = mock_response
        
        result = query_processor.process(complex_query, force_llm=True)
        
        assert result["processing_method"] == "llm"
        assert result["understanding"]["query_type"] == "factual"
    
    def test_cache_functionality(self, query_processor):
        """测试缓存功能"""
        query = "测试查询"
        
        # 第一次处理
        result1 = query_processor.process(query, use_cache=True)
        
        # 第二次处理（应该使用缓存）
        result2 = query_processor.process(query, use_cache=True)
        
        assert result2["from_cache"] is True
        assert result1["original_query"] == result2["original_query"]
    
    def test_cache_lru_eviction(self, query_processor):
        """测试缓存LRU淘汰"""
        # 设置小缓存大小
        query_processor._cache_size = 2
        
        # 添加3个查询
        query_processor.process("query1", use_cache=True)
        query_processor.process("query2", use_cache=True)
        query_processor.process("query3", use_cache=True)
        
        # 第一个应该被淘汰
        assert "query1" not in query_processor._cache
        assert "query2" in query_processor._cache
        assert "query3" in query_processor._cache
    
    def test_clear_cache(self, query_processor):
        """测试清空缓存"""
        query_processor.process("test", use_cache=True)
        assert len(query_processor._cache) > 0
        
        query_processor.clear_cache()
        assert len(query_processor._cache) == 0
    
    def test_rewritten_queries_limit(self, query_processor, mock_llm):
        """测试改写查询数量限制（最多3个）"""
        complex_query = "测试查询"
        
        # Mock返回5个改写查询
        mock_response = Mock()
        mock_response.text = json.dumps({
            "understanding": {"query_type": "factual"},
            "rewritten_queries": [
                "改写1", "改写2", "改写3", "改写4", "改写5"
            ]
        })
        mock_llm.complete.return_value = mock_response
        
        result = query_processor.process(complex_query, force_llm=True)
        
        assert len(result["rewritten_queries"]) == 3
        assert result["rewritten_queries"] == ["改写1", "改写2", "改写3"]
    
    def test_empty_rewritten_queries(self, query_processor, mock_llm):
        """测试空改写查询列表的处理"""
        complex_query = "测试查询"
        
        # Mock返回空改写列表
        mock_response = Mock()
        mock_response.text = json.dumps({
            "understanding": {"query_type": "factual"},
            "rewritten_queries": []
        })
        mock_llm.complete.return_value = mock_response
        
        result = query_processor.process(complex_query, force_llm=True)
        
        # 应该使用原始查询
        assert result["rewritten_queries"] == [complex_query]
        assert result["final_query"] == complex_query


class TestQueryProcessorIntegration:
    """查询处理器集成测试"""
    
    def test_get_query_processor_singleton(self):
        """测试全局查询处理器单例"""
        reset_query_processor()
        
        from backend.business.rag_engine.processing.query_processor import get_query_processor
        
        processor1 = get_query_processor()
        processor2 = get_query_processor()
        
        assert processor1 is processor2
    
    def test_reset_query_processor(self):
        """测试重置查询处理器"""
        from backend.business.rag_engine.processing.query_processor import (
            get_query_processor,
            reset_query_processor
        )
        
        processor1 = get_query_processor()
        reset_query_processor()
        processor2 = get_query_processor()
        
        assert processor1 is not processor2

