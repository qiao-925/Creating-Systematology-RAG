"""
查询处理工具单元测试

测试内容：
- 工具创建
- 意图分析（Mock LLM）
- 查询改写（Mock LLM）
- 多意图分解（Mock LLM）
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from backend.business.rag_engine.agentic.agent.tools import create_query_processing_tools
from backend.business.rag_engine.agentic.agent.tools.query_processing_impl import (
    analyze_intent,
    rewrite_query,
    decompose_multi_intent,
    _extract_json,
)


class TestQueryProcessingTools:
    """查询处理工具测试"""
    
    def test_create_query_processing_tools(self):
        """测试工具创建"""
        tools = create_query_processing_tools()
        
        assert len(tools) == 3
        tool_names = [t.metadata.name for t in tools]
        assert "analyze_intent" in tool_names
        assert "rewrite_query" in tool_names
        assert "decompose_multi_intent" in tool_names
    
    def test_extract_json_plain(self):
        """测试JSON提取 - 纯JSON"""
        text = '{"key": "value"}'
        result = _extract_json(text)
        assert result == '{"key": "value"}'
    
    def test_extract_json_markdown(self):
        """测试JSON提取 - Markdown代码块"""
        text = '```json\n{"key": "value"}\n```'
        result = _extract_json(text)
        assert result == '{"key": "value"}'
    
    def test_extract_json_generic_block(self):
        """测试JSON提取 - 通用代码块"""
        text = '```\n{"key": "value"}\n```'
        result = _extract_json(text)
        assert result == '{"key": "value"}'


class TestAnalyzeIntent:
    """意图分析测试"""
    
    @patch('backend.business.rag_engine.agentic.agent.tools.query_processing_impl._get_llm')
    def test_analyze_intent_success(self, mock_get_llm):
        """测试意图分析成功"""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "query_type": "factual",
            "complexity": "simple",
            "entities": ["系统科学"],
            "intent_summary": "查询系统科学相关信息",
            "needs_rewrite": False,
            "needs_decompose": False,
            "confidence": 0.9
        })
        mock_llm.complete.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        result = analyze_intent("什么是系统科学？")
        result_dict = json.loads(result)
        
        assert result_dict["query_type"] == "factual"
        assert result_dict["complexity"] == "simple"
        assert "系统科学" in result_dict["entities"]
        assert result_dict["needs_rewrite"] is False
    
    @patch('backend.business.rag_engine.agentic.agent.tools.query_processing_impl._get_llm')
    def test_analyze_intent_error_fallback(self, mock_get_llm):
        """测试意图分析失败降级"""
        mock_llm = MagicMock()
        mock_llm.complete.side_effect = Exception("LLM error")
        mock_get_llm.return_value = mock_llm
        
        result = analyze_intent("测试查询")
        result_dict = json.loads(result)
        
        # 应该返回默认值
        assert result_dict["query_type"] == "factual"
        assert result_dict["complexity"] == "medium"
        assert "error" in result_dict


class TestRewriteQuery:
    """查询改写测试"""
    
    @patch('backend.business.rag_engine.agentic.agent.tools.query_processing_impl._get_llm')
    def test_rewrite_query_success(self, mock_get_llm):
        """测试查询改写成功"""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "original_query": "系统是什么",
            "rewritten_queries": [
                "系统科学中系统的定义和概念",
                "钱学森关于系统的理论阐述"
            ],
            "preserved_entities": ["系统"],
            "added_keywords": ["系统科学", "钱学森", "定义"],
            "rewrite_reason": "补充领域关键词"
        })
        mock_llm.complete.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        result = rewrite_query("系统是什么")
        result_dict = json.loads(result)
        
        assert result_dict["original_query"] == "系统是什么"
        assert len(result_dict["rewritten_queries"]) == 2
        assert "系统" in result_dict["preserved_entities"]


class TestDecomposeMultiIntent:
    """多意图分解测试"""
    
    @patch('backend.business.rag_engine.agentic.agent.tools.query_processing_impl._get_llm')
    def test_decompose_multi_intent_success(self, mock_get_llm):
        """测试多意图分解成功"""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "is_multi_intent": True,
            "intent_count": 2,
            "sub_queries": [
                {"query": "系统科学是什么？", "intent_type": "factual", "priority": 1},
                {"query": "系统科学有什么应用？", "intent_type": "exploratory", "priority": 2}
            ],
            "decompose_reason": "包含两个独立问题"
        })
        mock_llm.complete.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        result = decompose_multi_intent("系统科学是什么？有什么应用？")
        result_dict = json.loads(result)
        
        assert result_dict["is_multi_intent"] is True
        assert result_dict["intent_count"] == 2
        assert len(result_dict["sub_queries"]) == 2
    
    @patch('backend.business.rag_engine.agentic.agent.tools.query_processing_impl._get_llm')
    def test_decompose_single_intent(self, mock_get_llm):
        """测试单一意图不分解"""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "is_multi_intent": False,
            "intent_count": 1,
            "sub_queries": [
                {"query": "什么是系统科学？", "intent_type": "factual", "priority": 1}
            ],
            "decompose_reason": "单一意图，无需分解"
        })
        mock_llm.complete.return_value = mock_response
        mock_get_llm.return_value = mock_llm
        
        result = decompose_multi_intent("什么是系统科学？")
        result_dict = json.loads(result)
        
        assert result_dict["is_multi_intent"] is False
        assert result_dict["intent_count"] == 1
