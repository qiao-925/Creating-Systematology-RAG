"""
对话管理 - 数据模型模块
ChatTurn和ChatSession类
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

from src.logger import setup_logger

logger = setup_logger('chat_manager')


@dataclass
class ChatTurn:
    """单轮对话"""
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    timestamp: str
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建"""
        return cls(**data)


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
    
    def add_turn(self, question: str, answer: str, sources: List[dict]):
        """添加一轮对话
        
        Args:
            question: 用户问题
            answer: AI回答
            sources: 引用来源
        """
        turn = ChatTurn(
            question=question,
            answer=answer,
            sources=sources,
            timestamp=datetime.now().isoformat()
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

