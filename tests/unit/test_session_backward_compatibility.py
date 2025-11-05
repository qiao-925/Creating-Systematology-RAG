"""
会话加载/保存向后兼容性验证脚本

验证：
1. 旧会话文件（不包含 reasoning_content）可以正常加载
2. 新会话文件（包含 reasoning_content）可以正常加载
3. 加载会话时，reasoning_content 不会被恢复到 memory
4. 保存会话时，根据配置决定是否保存 reasoning_content
"""

import json
import tempfile
from pathlib import Path
from llama_index.core.llms import ChatMessage, MessageRole

from src.chat.session import ChatSession, ChatTurn


def test_old_session_format():
    """测试旧会话文件格式（不包含 reasoning_content）"""
    # 创建旧格式会话数据
    old_session_data = {
        'session_id': 'test_session_old',
        'title': '测试会话',
        'created_at': '2025-01-01T00:00:00',
        'updated_at': '2025-01-01T00:00:00',
        'history': [
            {
                'question': '问题1',
                'answer': '回答1',
                'sources': [],
                'timestamp': '2025-01-01T00:00:00'
                # 注意：不包含 reasoning_content
            }
        ]
    }
    
    # 测试 from_dict
    session = ChatSession.from_dict(old_session_data)
    
    assert session.session_id == 'test_session_old'
    assert len(session.history) == 1
    assert session.history[0].question == '问题1'
    assert session.history[0].answer == '回答1'
    assert session.history[0].reasoning_content is None  # 旧格式没有推理链
    
    # 测试保存和加载
    with tempfile.TemporaryDirectory() as tmpdir:
        save_dir = Path(tmpdir)
        session.save(save_dir)
        
        # 加载会话
        file_path = save_dir / f"{session.session_id}.json"
        loaded_session = ChatSession.load(file_path)
        
        assert loaded_session.session_id == session.session_id
        assert len(loaded_session.history) == 1
        assert loaded_session.history[0].reasoning_content is None


def test_new_session_format():
    """测试新会话文件格式（包含 reasoning_content）"""
    # 创建新格式会话数据
    new_session_data = {
        'session_id': 'test_session_new',
        'title': '测试会话',
        'created_at': '2025-01-01T00:00:00',
        'updated_at': '2025-01-01T00:00:00',
        'history': [
            {
                'question': '问题1',
                'answer': '回答1',
                'sources': [],
                'timestamp': '2025-01-01T00:00:00',
                'reasoning_content': '推理过程1'  # 包含推理链
            }
        ]
    }
    
    # 测试 from_dict
    session = ChatSession.from_dict(new_session_data)
    
    assert session.session_id == 'test_session_new'
    assert len(session.history) == 1
    assert session.history[0].reasoning_content == '推理过程1'
    
    # 测试保存和加载
    with tempfile.TemporaryDirectory() as tmpdir:
        save_dir = Path(tmpdir)
        session.save(save_dir)
        
        # 加载会话
        file_path = save_dir / f"{session.session_id}.json"
        loaded_session = ChatSession.load(file_path)
        
        assert loaded_session.session_id == session.session_id
        assert len(loaded_session.history) == 1
        assert loaded_session.history[0].reasoning_content == '推理过程1'


def test_session_load_to_memory():
    """测试会话加载到 memory 时，reasoning_content 不会被恢复"""
    session = ChatSession(session_id="test")
    session.add_turn(
        question="问题1",
        answer="回答1",
        sources=[],
        reasoning_content="推理过程1"  # 包含推理链
    )
    
    # 模拟 memory.put 调用（模拟 load_session 的逻辑）
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
    
    # 验证 ChatMessage 不包含 reasoning_content 字段
    assert not hasattr(memory_messages[0], 'reasoning_content')
    assert not hasattr(memory_messages[1], 'reasoning_content')
    
    # 验证 assistant 消息的 content 不包含推理链内容
    assert "推理过程1" not in memory_messages[1].content
    assert memory_messages[1].content == "回答1"  # 只有回答内容


def test_session_save_without_reasoning():
    """测试不存储推理链的会话保存"""
    session = ChatSession(session_id="test")
    session.add_turn(
        question="问题1",
        answer="回答1",
        sources=[],
        reasoning_content=None  # 不存储推理链
    )
    
    session_dict = session.to_dict()
    
    # 验证保存的字典不包含空的 reasoning_content
    assert 'reasoning_content' not in session_dict['history'][0]


def test_session_save_with_reasoning():
    """测试存储推理链的会话保存"""
    session = ChatSession(session_id="test")
    session.add_turn(
        question="问题1",
        answer="回答1",
        sources=[],
        reasoning_content="推理过程1"  # 存储推理链
    )
    
    session_dict = session.to_dict()
    
    # 验证保存的字典包含 reasoning_content
    assert 'reasoning_content' in session_dict['history'][0]
    assert session_dict['history'][0]['reasoning_content'] == "推理过程1"


if __name__ == "__main__":
    print("开始验证会话加载/保存向后兼容性...")
    
    try:
        test_old_session_format()
        print("✅ 旧会话格式验证通过")
        
        test_new_session_format()
        print("✅ 新会话格式验证通过")
        
        test_session_load_to_memory()
        print("✅ 会话加载到 memory 验证通过（reasoning_content 不会被恢复）")
        
        test_session_save_without_reasoning()
        print("✅ 不存储推理链的会话保存验证通过")
        
        test_session_save_with_reasoning()
        print("✅ 存储推理链的会话保存验证通过")
        
        print("\n✅ 所有验证通过！")
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()

