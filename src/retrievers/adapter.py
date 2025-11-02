"""
检索器适配器

将LlamaIndex的检索器适配到BaseRetriever接口
"""

from typing import List
from llama_index.core.schema import NodeWithScore, QueryBundle

from src.retrievers.multi_strategy_retriever import BaseRetriever
from src.logger import setup_logger

logger = setup_logger('retriever_adapter')


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

