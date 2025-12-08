"""
RAG引擎检索模块 - 适配器：将不同接口的检索器进行适配转换

主要功能：
- LlamaIndexRetrieverAdapter类：将LlamaIndex检索器适配到BaseRetriever接口
- MultiStrategyRetrieverAdapter类：将MultiStrategyRetriever适配为LlamaIndex检索器接口
- GrepRetrieverAdapter类：将GrepRetriever适配为LlamaIndex检索器接口

执行流程：
1. 接收查询
2. 调用底层检索器
3. 转换结果格式
4. 返回适配后的结果

特性：
- 适配器模式
- 双向接口转换（BaseRetriever ↔ LlamaIndex检索器）
- 兼容多种检索器实现
"""

from typing import List
from llama_index.core.schema import NodeWithScore, QueryBundle

from src.business.rag_engine.retrieval.strategies.multi_strategy import BaseRetriever, MultiStrategyRetriever
from src.business.rag_engine.retrieval.strategies.grep import GrepRetriever
from src.infrastructure.logger import get_logger

logger = get_logger('rag_engine.retrieval')


class LlamaIndexRetrieverAdapter(BaseRetriever):
    """LlamaIndex检索器适配器
    
    将LlamaIndex的检索器适配到BaseRetriever接口
    """
    
    def __init__(self, llama_index_retriever, name: str):
        """初始化适配器
        
        Args:
            llama_index_retriever: LlamaIndex检索器实例
            name: 检索器名称
        """
        super().__init__(name)
        self.retriever = llama_index_retriever
    
    def retrieve(self, query: str, top_k: int = 10) -> List[NodeWithScore]:
        """执行检索
        
        Args:
            query: 查询文本
            top_k: 返回Top-K结果
            
        Returns:
            检索结果列表
        """
        try:
            # 创建QueryBundle
            query_bundle = QueryBundle(query_str=query)
            
            # 调用LlamaIndex检索器
            nodes = self.retriever.retrieve(query_bundle)
            
            # 确保返回的是NodeWithScore列表
            result_nodes = []
            for node in nodes:
                if isinstance(node, NodeWithScore):
                    result_nodes.append(node)
                else:
                    # 如果没有分数，设置默认分数
                    result_nodes.append(NodeWithScore(node=node, score=0.5))
            
            # 限制结果数量
            return result_nodes[:top_k]
            
        except Exception as e:
            logger.error(f"检索器 {self.name} 执行失败: {e}")
            return []


class MultiStrategyRetrieverAdapter:
    """MultiStrategyRetriever适配器
    
    将MultiStrategyRetriever适配为LlamaIndex检索器接口
    """
    
    def __init__(self, multi_strategy_retriever: MultiStrategyRetriever):
        """初始化适配器
        
        Args:
            multi_strategy_retriever: MultiStrategyRetriever实例
        """
        self.multi_retriever = multi_strategy_retriever
    
    def retrieve(self, query_bundle):
        """执行检索（LlamaIndex接口）
        
        Args:
            query_bundle: LlamaIndex的QueryBundle对象
            
        Returns:
            检索结果列表（NodeWithScore）
        """
        query_str = query_bundle.query_str if hasattr(query_bundle, 'query_str') else str(query_bundle)
        return self.multi_retriever.retrieve(query_str, top_k=10)


class GrepRetrieverAdapter:
    """GrepRetriever适配器
    
    将GrepRetriever适配为LlamaIndex检索器接口
    """
    
    def __init__(self, grep_retriever: GrepRetriever):
        """初始化适配器
        
        Args:
            grep_retriever: GrepRetriever实例
        """
        self.grep_retriever = grep_retriever
    
    def retrieve(self, query_bundle):
        """执行检索（LlamaIndex接口）
        
        Args:
            query_bundle: LlamaIndex的QueryBundle对象
            
        Returns:
            检索结果列表（NodeWithScore）
        """
        query_str = query_bundle.query_str if hasattr(query_bundle, 'query_str') else str(query_bundle)
        return self.grep_retriever.retrieve(query_str, top_k=10)
