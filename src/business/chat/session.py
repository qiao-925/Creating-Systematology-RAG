"""
对话管理 - 数据模型模块：ChatTurn和ChatSession类

主要功能：
- ChatTurn类：单轮对话数据模型，包含问题、回答、来源、时间戳等
- ChatSession类：对话会话数据模型，包含会话ID、标题、历史记录等
- 支持JSON序列化和反序列化

执行流程：
1. 创建ChatTurn对象
2. 添加到ChatSession
3. 序列化为JSON保存
4. 从JSON反序列化加载

特性：
- 数据模型定义
- JSON序列化支持
- 推理链内容支持
- 完整的元数据管理
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

from src.infrastructure.logger import get_logger

logger = get_logger('chat_manager')


def _convert_source_to_dict(source: Any) -> Dict[str, Any]:
    """将来源对象转换为字典
    
    Args:
        source: 来源对象（可能是 dict 或 SourceModel）
        
    Returns:
        字典格式的来源
    """
    # 如果已经是字典，直接返回
    if isinstance(source, dict):
        return source
    
    # 如果是 Pydantic BaseModel（SourceModel），使用 model_dump()
    if hasattr(source, 'model_dump'):
        return source.model_dump()
    
    # 如果是其他对象，尝试转换为字典
    if hasattr(source, '__dict__'):
        return {k: v for k, v in source.__dict__.items() if not k.startswith('_')}
    
    # 最后尝试直接转换
    return dict(source) if hasattr(source, '__iter__') and not isinstance(source, str) else {'text': str(source)}


@dataclass
class ChatTurn:
    """单轮对话"""
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    timestamp: str
    reasoning_content: Optional[str] = None  # 推理链内容（可选）
    
    def to_dict(self) -> dict:
        """转换为字典"""
        result = asdict(self)
        
        # 处理 sources：确保所有来源都是字典格式
        if 'sources' in result and isinstance(result['sources'], list):
            result['sources'] = [_convert_source_to_dict(source) for source in result['sources']]
        
        # 如果推理链为空，不包含在字典中
        if not result.get('reasoning_content'):
            result.pop('reasoning_content', None)
        return result
    
    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建会话"""
        # 兼容旧会话文件：可能不包含 reasoning_content
        reasoning_content = data.get('reasoning_content')
        turn_data = {k: v for k, v in data.items() if k != 'reasoning_content'}
        turn = cls(**turn_data)
        if reasoning_content:
            turn.reasoning_content = reasoning_content
        return turn


class ChatSession:
    """对话会话"""
    
    def __init__(self, session_id: Optional[str] = None, title: Optional[str] = None):
        """初始化对话会话
        
        Args:
            session_id: 会话ID，如果不提供则自动生成
            title: 会话标题，如果不提供则自动生成
        """
        self.session_id = session_id or self._generate_session_id()
        self.title = title or ""
        self.history: List[ChatTurn] = []
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
    
    @staticmethod
    def _generate_session_id() -> str:
        """生成会话ID"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def add_turn(self, question: str, answer: str, sources: List[dict], reasoning_content: Optional[str] = None):
        """添加一轮对话
        
        Args:
            question: 用户问题
            answer: AI回答
            sources: 引用来源（可以是 dict 或 SourceModel 对象列表）
            reasoning_content: 推理链内容（可选）
        """
        # 确保 sources 都是字典格式
        sources_dict = [_convert_source_to_dict(source) for source in sources]
        
        turn = ChatTurn(
            question=question,
            answer=answer,
            sources=sources_dict,
            timestamp=datetime.now().isoformat(),
            reasoning_content=reasoning_content
        )
        self.history.append(turn)
        self.updated_at = turn.timestamp
        
        # 如果是第一轮对话且没有标题，自动生成标题
        if len(self.history) == 1 and not self.title:
            self.title = self._generate_title(question)
    
    @staticmethod
    def _generate_title(first_question: str) -> str:
        """根据第一条问题生成会话标题
        
        Args:
            first_question: 第一条用户问题
            
        Returns:
            会话标题
        """
        # 取前20个字符作为标题
        if len(first_question) > 20:
            return first_question[:20] + "..."
        return first_question
    
    def get_history(self, last_n: Optional[int] = None) -> List[ChatTurn]:
        """获取对话历史
        
        Args:
            last_n: 获取最近N轮对话，None表示获取全部
            
        Returns:
            对话历史列表
        """
        if last_n is None:
            return self.history
        return self.history[-last_n:]
    
    def clear_history(self):
        """清空对话历史"""
        self.history = []
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'session_id': self.session_id,
            'title': self.title,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'history': [turn.to_dict() for turn in self.history]
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建"""
        session = cls(
            session_id=data['session_id'],
            title=data.get('title', '')
        )
        session.created_at = data['created_at']
        session.updated_at = data['updated_at']
        session.history = [ChatTurn.from_dict(turn) for turn in data['history']]
        return session
    
    def save(self, save_dir: Path):
        """保存会话到文件
        
        Args:
            save_dir: 保存目录
        """
        save_dir.mkdir(parents=True, exist_ok=True)
        file_path = save_dir / f"{self.session_id}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"会话已保存: {file_path}")
    
    @classmethod
    def load(cls, file_path: Path):
        """从文件加载会话
        
        Args:
            file_path: 文件路径
            
        Returns:
            ChatSession对象
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls.from_dict(data)

