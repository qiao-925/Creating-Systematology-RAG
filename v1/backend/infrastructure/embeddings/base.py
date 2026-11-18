"""
Embedding基类：定义统一的向量化接口

主要功能：
- BaseEmbedding类：抽象基类，定义所有Embedding实现必须实现的接口
- get_query_embedding()：生成查询向量
- get_text_embeddings()：批量生成文本向量

执行流程：
1. 子类实现抽象方法
2. 调用向量化方法
3. 返回向量结果

特性：
- 抽象基类设计
- 统一的接口规范
- 支持单条和批量向量化
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class BaseEmbedding(ABC):
    """Embedding模型基类
    
    所有Embedding实现都应继承此类，实现统一接口
    """
    
    @abstractmethod
    def get_query_embedding(self, query: str) -> List[float]:
        """生成查询向量
        
        Args:
            query: 查询文本
            
        Returns:
            向量（浮点数列表）
        """
        pass
    
    @abstractmethod
    def get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """批量生成文本向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表
        """
        pass
    
    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """获取向量维度
        
        Returns:
            向量维度（整数）
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """获取模型名称
        
        Returns:
            模型名称
        """
        pass
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}(model={self.get_model_name()}, dim={self.get_embedding_dimension()})"

