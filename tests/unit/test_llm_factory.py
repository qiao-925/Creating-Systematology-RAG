"""
DeepSeek LLM 工厂函数单元测试

测试 LLM 工厂函数的创建逻辑、配置处理、JSON Output 等功能。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.llms.factory import (
    create_deepseek_llm,
    create_deepseek_llm_for_query,
    create_deepseek_llm_for_structure,
)
from src.config import config


class TestCreateDeepSeekLLM:
    """测试 create_deepseek_llm 函数"""
    
    @patch('src.llms.factory.DeepSeek')
    @patch('src.llms.factory.wrap_deepseek')
    def test_create_with_default_config(self, mock_wrap, mock_deepseek):
        """测试使用默认配置创建 LLM"""
        mock_instance = Mock()
        mock_deepseek.return_value = mock_instance
        mock_wrap.return_value = mock_instance
        
        llm = create_deepseek_llm()
        
        # 验证 DeepSeek 被调用
        mock_deepseek.assert_called_once()
        call_kwargs = mock_deepseek.call_args[1]
        
        # 验证参数
        assert call_kwargs['api_key'] == config.DEEPSEEK_API_KEY
        assert call_kwargs['model'] == config.LLM_MODEL
        assert call_kwargs['max_tokens'] == 32768
        
        # 验证没有 JSON Output（默认）
        assert 'response_format' not in call_kwargs
        
        # 验证被包装
        mock_wrap.assert_called_once_with(mock_instance)
    
    @patch('src.llms.factory.DeepSeek')
    @patch('src.llms.factory.wrap_deepseek')
    def test_create_with_json_output(self, mock_wrap, mock_deepseek):
        """测试启用 JSON Output"""
        mock_instance = Mock()
        mock_deepseek.return_value = mock_instance
        mock_wrap.return_value = mock_instance
        
        llm = create_deepseek_llm(use_json_output=True)
        
        call_kwargs = mock_deepseek.call_args[1]
        
        # 验证 JSON Output 被启用
        assert 'response_format' in call_kwargs
        assert call_kwargs['response_format'] == {"type": "json_object"}
    
    @patch('src.llms.factory.DeepSeek')
    @patch('src.llms.factory.wrap_deepseek')
    def test_create_with_custom_parameters(self, mock_wrap, mock_deepseek):
        """测试使用自定义参数创建 LLM"""
        mock_instance = Mock()
        mock_deepseek.return_value = mock_instance
        mock_wrap.return_value = mock_instance
        
        llm = create_deepseek_llm(
            api_key="test_key",
            model="test-model",
            max_tokens=1000
        )
        
        call_kwargs = mock_deepseek.call_args[1]
        
        assert call_kwargs['api_key'] == "test_key"
        assert call_kwargs['model'] == "test-model"
        assert call_kwargs['max_tokens'] == 1000
    
    @patch('src.llms.factory.DeepSeek')
    @patch('src.llms.factory.wrap_deepseek')
    def test_create_without_api_key_raises_error(self, mock_wrap, mock_deepseek):
        """测试没有 API 密钥时抛出错误"""
        with patch('src.llms.factory.config') as mock_config:
            mock_config.DEEPSEEK_API_KEY = ""
            
            with pytest.raises(ValueError, match="未设置 DEEPSEEK_API_KEY"):
                create_deepseek_llm()


class TestCreateDeepSeekLLMForQuery:
    """测试 create_deepseek_llm_for_query 函数"""
    
    @patch('src.llms.factory.create_deepseek_llm')
    def test_create_for_query_no_json_output(self, mock_create):
        """测试创建用于查询的 LLM（不使用 JSON Output）"""
        mock_llm = Mock()
        mock_create.return_value = mock_llm
        
        llm = create_deepseek_llm_for_query()
        
        # 验证调用 create_deepseek_llm 时 use_json_output=False
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs['use_json_output'] is False


class TestCreateDeepSeekLLMForStructure:
    """测试 create_deepseek_llm_for_structure 函数"""
    
    @patch('src.llms.factory.create_deepseek_llm')
    def test_create_for_structure_with_json_output(self, mock_create):
        """测试创建用于结构化输出的 LLM（使用 JSON Output）"""
        mock_llm = Mock()
        mock_create.return_value = mock_llm
        
        llm = create_deepseek_llm_for_structure()
        
        # 验证调用 create_deepseek_llm 时 use_json_output=True
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs['use_json_output'] is True


class TestModelConfiguration:
    """测试模型配置"""
    
    @patch('src.llms.factory.DeepSeek')
    @patch('src.llms.factory.wrap_deepseek')
    @patch('src.llms.factory.logger')
    def test_warning_for_non_reasoner_model(self, mock_logger, mock_wrap, mock_deepseek):
        """测试使用非推理模型时发出警告"""
        mock_instance = Mock()
        mock_deepseek.return_value = mock_instance
        mock_wrap.return_value = mock_instance
        
        create_deepseek_llm(model="deepseek-chat")
        
        # 验证发出警告
        warning_calls = [call for call in mock_logger.warning.call_args_list 
                        if 'deepseek-reasoner' in str(call)]
        assert len(warning_calls) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
