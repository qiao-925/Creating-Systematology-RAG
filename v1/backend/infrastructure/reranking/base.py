"""
RAG引擎重排序模块 - 重排序器基类：定义重排序器的统一接口

主要功能：
- BaseReranker类：抽象基类，定义所有重排序器必须实现的接口
- rerank()：对检索结果进行重排序

执行流程：
1. 子类实现rerank()方法
2. 接收查询和节点列表
3. 执行重排序
4. 返回Top-N结果

特性：
- 抽象基类设计
- 统一的接口规范
- Top-N结果控制
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from llama_index.core.schema import NodeWithScore, QueryBundle

from backend.infrastructure.logger import get_logger

logger = get_logger('rag_engine.reranking')


class BaseReranker(ABC):
    """重排序器基类
    
    所有重排序器实现都应继承此类，实现统一接口
    """
    
    def __init__(self, name: str, top_n: int):
        """初始化重排序器
        
        Args:
            name: 重排序器名称
            top_n: 返回Top-N数量
        """
        self.name = name
        self.top_n = top_n
    
    @abstractmethod
    def rerank(
        self,
        nodes: List[NodeWithScore],
        query: QueryBundle,
    ) -> List[NodeWithScore]:
        """对检索到的节点进行重排序
        
        Args:
            nodes: 检索到的节点列表（带分数）
            query: 查询信息
            
        Returns:
            重排序后的节点列表
        """
        pass
    
    def get_reranker_name(self) -> str:
        """获取重排序器名称"""
        return self.name
    
    def get_top_n(self) -> int:
        """获取返回的Top-N数量"""
        return self.top_n
    
    def get_llama_index_postprocessor(self):
        """获取LlamaIndex兼容的Postprocessor（可选）
        
        如果重排序器直接基于LlamaIndex的Postprocessor，
        可以实现此方法返回底层实例，便于集成
        """
        return None
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.get_reranker_name()}, top_n={self.get_top_n()})"
