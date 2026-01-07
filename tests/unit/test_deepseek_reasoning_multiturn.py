"""
DeepSeek 推理链多轮对话验证测试

验证在多轮对话中，reasoning_content 不会被传递到下一轮对话的 messages 中。
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from llama_index.core.llms import ChatMessage, MessageRole

from backend.infrastructure.llms.reasoning import clean_messages_for_api, extract_reasoning_content
from backend.business.chat.session import ChatTurn, ChatSession


class TestChatMessageStructure:
    """测试 ChatMessage 结构"""
    
    def test_chat_message_only_contains_role_and_content(self):
        """验证 ChatMessage 只包含 role 和 content"""
        msg = ChatMessage(role=MessageRole.USER, content="测试问题")
        
        # ChatMessage 应该只包含 role 和 content
        assert hasattr(msg, 'role')
        assert hasattr(msg, 'content')
        # 不应该包含 reasoning_content 字段
        assert not hasattr(msg, 'reasoning_content')
    
    def test_chat_message_content_extraction(self):
        """验证从 ChatMessage 提取内容"""
        msg = ChatMessage(role=MessageRole.USER, content="测试问题")
        
        role = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
        content = msg.content
        
        assert role in ['user', 'system', 'assistant']
        assert content == "测试问题"


class TestCleanMessagesForAPI:
    """测试消息清理函数"""
    
    def test_clean_chat_message_objects(self):
        """测试清理 ChatMessage 对象"""
        messages = [
            ChatMessage(role=MessageRole.USER, content="问题1"),
            ChatMessage(role=MessageRole.ASSISTANT, content="回答1"),
        ]
        
        cleaned = clean_messages_for_api(messages)
        
        assert len(cleaned) == 2
        assert cleaned[0]['role'] == 'user'
        assert cleaned[0]['content'] == "问题1"
        assert 'reasoning_content' not in cleaned[0]
        assert cleaned[1]['role'] == 'assistant'
        assert cleaned[1]['content'] == "回答1"
        assert 'reasoning_content' not in cleaned[1]
    
    def test_clean_dict_messages(self):
        """测试清理字典格式的消息"""
        messages = [
            {'role': 'user', 'content': '问题1'},
            {'role': 'assistant', 'content': '回答1', 'reasoning_content': '推理过程'},
        ]
        
        cleaned = clean_messages_for_api(messages)
        
        assert len(cleaned) == 2
        assert cleaned[0]['role'] == 'user'
        assert cleaned[0]['content'] == "问题1"
        assert 'reasoning_content' not in cleaned[0]
        assert cleaned[1]['role'] == 'assistant'
        assert cleaned[1]['content'] == "回答1"
        assert 'reasoning_content' not in cleaned[1]  # 应该被移除
    
    def test_clean_messages_removes_reasoning_content(self):
        """测试清理函数移除 reasoning_content"""
        messages = [
            {'role': 'assistant', 'content': '回答', 'reasoning_content': '推理链内容'},
        ]
        
        cleaned = clean_messages_for_api(messages)
        
        assert len(cleaned) == 1
        assert 'reasoning_content' not in cleaned[0]
        assert cleaned[0]['role'] == 'assistant'
        assert cleaned[0]['content'] == '回答'


class TestChatTurnStructure:
    """测试 ChatTurn 结构"""
    
    def test_chat_turn_without_reasoning(self):
        """测试没有推理链的 ChatTurn"""
        turn = ChatTurn(
            question="问题",
            answer="回答",
            sources=[],
            timestamp="2025-01-01T00:00:00"
        )
        
        assert turn.question == "问题"
        assert turn.answer == "回答"
        assert turn.reasoning_content is None
        
        # to_dict 不应该包含空的 reasoning_content
        turn_dict = turn.to_dict()
        assert 'reasoning_content' not in turn_dict
    
    def test_chat_turn_with_reasoning(self):
        """测试包含推理链的 ChatTurn"""
        turn = ChatTurn(
            question="问题",
            answer="回答",
            sources=[],
            timestamp="2025-01-01T00:00:00",
            reasoning_content="推理过程"
        )
        
        assert turn.reasoning_content == "推理过程"
        
        # to_dict 应该包含 reasoning_content
        turn_dict = turn.to_dict()
        assert 'reasoning_content' in turn_dict
        assert turn_dict['reasoning_content'] == "推理过程"
    
    def test_chat_turn_from_dict_backward_compatible(self):
        """测试从字典创建 ChatTurn（向后兼容）"""
        # 旧格式（不包含 reasoning_content）
        old_data = {
            'question': '问题',
            'answer': '回答',
            'sources': [],
            'timestamp': '2025-01-01T00:00:00'
        }
        
        turn = ChatTurn.from_dict(old_data)
        
        assert turn.question == "问题"
        assert turn.answer == "回答"
        assert turn.reasoning_content is None  # 旧格式没有推理链
    
    def test_chat_turn_from_dict_with_reasoning(self):
        """测试从字典创建包含推理链的 ChatTurn"""
        data = {
            'question': '问题',
            'answer': '回答',
            'sources': [],
            'timestamp': '2025-01-01T00:00:00',
            'reasoning_content': '推理过程'
        }
        
        turn = ChatTurn.from_dict(data)
        
        assert turn.reasoning_content == "推理过程"


class TestChatSessionLoad:
    """测试会话加载逻辑"""
    
    def test_load_session_does_not_restore_reasoning_to_memory(self):
        """测试加载会话时，reasoning_content 不会被恢复到 memory"""
        session = ChatSession(session_id="test")
        session.add_turn(
            question="问题1",
            answer="回答1",
            sources=[],
            reasoning_content="推理过程1"  # 包含推理链
        )
        
        # 模拟 memory.put 调用
        memory_messages = []
        
        def mock_memory_put(msg):
            memory_messages.append(msg)
        
        # 模拟 load_session 的逻辑
        for turn in session.history:
            user_msg = ChatMessage(role=MessageRole.USER, content=turn.question)
            assistant_msg = ChatMessage(role=MessageRole.ASSISTANT, content=turn.answer)
            mock_memory_put(user_msg)
            mock_memory_put(assistant_msg)
        
        # 验证 memory 中的消息不包含 reasoning_content
        assert len(memory_messages) == 2
        assert memory_messages[0].content == "问题1"
        assert memory_messages[1].content == "回答1"
        # 验证 ChatMessage 不包含 reasoning_content
        assert not hasattr(memory_messages[0], 'reasoning_content')
        assert not hasattr(memory_messages[1], 'reasoning_content')
        # 验证 assistant 消息的 content 不包含推理链
        assert "推理过程1" not in memory_messages[1].content


class TestExtractReasoningContent:
    """测试推理链提取函数"""
    
    def test_extract_reasoning_from_chat_response(self):
        """测试从 ChatResponse 提取推理链"""
        # 模拟包含 reasoning_content 的响应
        mock_response = Mock()
        mock_message = Mock()
        mock_message.reasoning_content = "推理过程"
        mock_response.message = mock_message
        
        reasoning = extract_reasoning_content(mock_response)
        
        assert reasoning == "推理过程"
    
    def test_extract_reasoning_from_raw_response(self):
        """测试从原始响应提取推理链"""
        mock_response = Mock()
        mock_response.raw = {
            'choices': [{
                'message': {
                    'reasoning_content': '推理过程'
                }
            }]
        }
        
        reasoning = extract_reasoning_content(mock_response)
        
        assert reasoning == "推理过程"
    
    def test_extract_reasoning_no_reasoning(self):
        """测试没有推理链的情况"""
        mock_response = Mock()
        mock_message = Mock()
        mock_message.reasoning_content = None
        mock_response.message = mock_message
        
        reasoning = extract_reasoning_content(mock_response)
        
        assert reasoning is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

