"""
模块化查询引擎 - 重排序模块
重排序逻辑
"""

from typing import List
from llama_index.core.schema import NodeWithScore

from src.logger import setup_logger

logger = setup_logger('modular_query_engine')


def rerank_nodes(nodes: List[NodeWithScore], question: str, top_n: int) -> List[NodeWithScore]:
    """重排序节点
    
    Args:
        nodes: 节点列表
        question: 用户问题
        top_n: 保留Top-N个节点
        
    Returns:
        重排序后的节点列表
    """
    # 简单实现：按分数排序并取Top-N
    # 实际应用中可以使用更复杂的重排序模型
    sorted_nodes = sorted(nodes, key=lambda x: x.score or 0.0, reverse=True)
    return sorted_nodes[:top_n]

