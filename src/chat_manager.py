"""
多轮对话管理模块
管理对话历史、上下文记忆和会话持久化
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.llms.openai import OpenAI

from src.config import config
from src.indexer import IndexManager


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
    
    def __init__(self, session_id: Optional[str] = None):
        """初始化对话会话
        
        Args:
            session_id: 会话ID，如果不提供则自动生成
        """
        self.session_id = session_id or self._generate_session_id()
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
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'history': [turn.to_dict() for turn in self.history]
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """从字典创建"""
        session = cls(session_id=data['session_id'])
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
        
        print(f"💾 会话已保存: {file_path}")
    
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


class ChatManager:
    """对话管理器"""
    
    def __init__(
        self,
        index_manager: IndexManager,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        memory_token_limit: int = 3000,
        similarity_top_k: Optional[int] = None,
    ):
        """初始化对话管理器
        
        Args:
            index_manager: 索引管理器
            api_key: DeepSeek API密钥
            api_base: API端点
            model: 模型名称
            memory_token_limit: 记忆token限制
            similarity_top_k: 检索相似文档数量
        """
        self.index_manager = index_manager
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        
        # 配置DeepSeek LLM
        self.api_key = api_key or config.DEEPSEEK_API_KEY
        self.api_base = api_base or config.DEEPSEEK_API_BASE
        self.model = model or config.LLM_MODEL
        
        if not self.api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY")
        
        print(f"🤖 初始化DeepSeek LLM (对话模式): {self.model}")
        self.llm = OpenAI(
            api_key=self.api_key,
            api_base=self.api_base,
            model=self.model,
            temperature=0.3,  # 对话模式可以稍微高一点温度
        )
        
        # 创建记忆缓冲区
        self.memory = ChatMemoryBuffer.from_defaults(
            token_limit=memory_token_limit,
        )
        
        # 获取索引
        self.index = self.index_manager.get_index()
        
        # 创建聊天引擎
        print("💬 创建多轮对话引擎")
        self.chat_engine = CondensePlusContextChatEngine.from_defaults(
            retriever=self.index.as_retriever(similarity_top_k=self.similarity_top_k),
            llm=self.llm,
            memory=self.memory,
            context_prompt=(
                "你是一位系统科学领域的专家助手。"
                "请基于以下上下文信息回答用户的问题。"
                "如果上下文中没有相关信息，请诚实地说明。"
                "\n\n上下文信息:\n{context_str}\n\n"
                "请用中文回答问题。"
            ),
        )
        
        # 当前会话
        self.current_session: Optional[ChatSession] = None
        
        print("✅ 对话管理器初始化完成")
    
    def start_session(self, session_id: Optional[str] = None) -> ChatSession:
        """开始新会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            ChatSession对象
        """
        self.current_session = ChatSession(session_id=session_id)
        self.memory.reset()  # 重置记忆
        print(f"🆕 新会话开始: {self.current_session.session_id}")
        return self.current_session
    
    def load_session(self, file_path: Path):
        """加载已有会话
        
        Args:
            file_path: 会话文件路径
        """
        self.current_session = ChatSession.load(file_path)
        
        # 恢复对话历史到记忆
        self.memory.reset()
        for turn in self.current_session.history:
            self.memory.put(ChatMessage(role=MessageRole.USER, content=turn.question))
            self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=turn.answer))
        
        print(f"📂 会话已加载: {self.current_session.session_id}")
        print(f"   包含 {len(self.current_session.history)} 轮对话")
    
    def chat(self, message: str) -> tuple[str, List[dict]]:
        """进行对话
        
        Args:
            message: 用户消息
            
        Returns:
            (回答, 引用来源列表)
        """
        if self.current_session is None:
            self.start_session()
        
        try:
            print(f"\n💬 用户: {message}")
            
            # 执行对话
            response = self.chat_engine.chat(message)
            
            # 提取答案
            answer = str(response)
            
            # 提取引用来源
            sources = []
            if hasattr(response, 'source_nodes') and response.source_nodes:
                for i, node in enumerate(response.source_nodes, 1):
                    source = {
                        'index': i,
                        'text': node.node.text,
                        'score': node.score if hasattr(node, 'score') else None,
                        'metadata': node.node.metadata,
                    }
                    sources.append(source)
            
            # 添加到会话历史
            self.current_session.add_turn(message, answer, sources)
            
            print(f"🤖 AI: {answer[:100]}...")
            print(f"📚 引用来源: {len(sources)} 个")
            
            return answer, sources
            
        except Exception as e:
            print(f"❌ 对话失败: {e}")
            raise
    
    def get_current_session(self) -> Optional[ChatSession]:
        """获取当前会话"""
        return self.current_session
    
    def save_current_session(self, save_dir: Optional[Path] = None):
        """保存当前会话
        
        Args:
            save_dir: 保存目录，默认为项目根目录/sessions
        """
        if self.current_session is None:
            print("⚠️  没有活动会话需要保存")
            return
        
        if save_dir is None:
            save_dir = config.PROJECT_ROOT / "sessions"
        
        self.current_session.save(save_dir)
    
    def reset_session(self):
        """重置当前会话"""
        if self.current_session:
            self.current_session.clear_history()
        self.memory.reset()
        print("🔄 会话已重置")


if __name__ == "__main__":
    # 测试代码
    from llama_index.core import Document as LlamaDocument
    
    print("=== 测试多轮对话管理器 ===\n")
    
    # 创建测试文档
    test_docs = [
        LlamaDocument(
            text="系统科学研究系统的一般规律，包括系统论、控制论、信息论等分支。",
            metadata={"title": "系统科学", "source": "test"}
        ),
        LlamaDocument(
            text="钱学森提出了开放的复杂巨系统理论，强调定性与定量相结合的综合集成方法。",
            metadata={"title": "钱学森理论", "source": "test"}
        ),
    ]
    
    # 创建索引
    index_manager = IndexManager(collection_name="test_chat")
    index_manager.build_index(test_docs)
    
    # 创建对话管理器
    chat_manager = ChatManager(index_manager)
    
    # 开始会话
    session = chat_manager.start_session()
    
    # 模拟多轮对话
    questions = [
        "什么是系统科学？",
        "它包括哪些分支？",
        "钱学森有什么贡献？"
    ]
    
    for q in questions:
        answer, sources = chat_manager.chat(q)
        print(f"\n问: {q}")
        print(f"答: {answer}")
    
    # 保存会话
    chat_manager.save_current_session()
    
    # 清理
    index_manager.clear_index()
    print("\n✅ 测试完成")

