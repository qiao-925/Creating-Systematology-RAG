"""
简单查询引擎模块
不带引用溯源的快速查询引擎
"""

from typing import Optional

from llama_index.llms.deepseek import DeepSeek

from src.config import config
from src.indexer import IndexManager
from src.logger import setup_logger

logger = setup_logger('query_engine')


class SimpleQueryEngine:
    """简单查询引擎（不带引用溯源，用于快速查询）"""
    
    def __init__(
        self,
        index_manager: IndexManager,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model: Optional[str] = None,
        similarity_top_k: Optional[int] = None,
    ):
        """初始化简单查询引擎
        
        Args:
            index_manager: 索引管理器
            api_key: DeepSeek API密钥
            api_base: API端点
            model: 模型名称
            similarity_top_k: 检索相似文档数量
        """
        self.index_manager = index_manager
        self.similarity_top_k = similarity_top_k or config.SIMILARITY_TOP_K
        
        # 配置DeepSeek LLM
        self.api_key = api_key or config.DEEPSEEK_API_KEY
        self.model = model or config.LLM_MODEL
        
        if not self.api_key:
            raise ValueError("未设置DEEPSEEK_API_KEY")
        
        # 使用官方 DeepSeek 集成
        self.llm = DeepSeek(
            api_key=self.api_key,
            model=self.model,
            temperature=0.5,
            max_tokens=4096,
        )
        
        # 获取索引
        self.index = self.index_manager.get_index()
        
        # 创建标准查询引擎
        self.query_engine = self.index.as_query_engine(
            llm=self.llm,
            similarity_top_k=self.similarity_top_k,
        )
    
    def query(self, question: str) -> str:
        """执行简单查询
        
        Args:
            question: 用户问题
            
        Returns:
            答案文本
        """
        try:
            response = self.query_engine.query(question)
            return str(response)
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            raise

