"""
模块化查询引擎 - 响应格式化模块
响应格式化逻辑
"""

from typing import List
from llama_index.core.base.response.schema import Response
from llama_index.core.schema import NodeWithScore

from src.logger import setup_logger

logger = setup_logger('modular_query_engine')


def format_response(nodes: List[NodeWithScore], question: str) -> Response:
    """格式化响应
    
    Args:
        nodes: 检索到的节点列表
        question: 用户问题
        
    Returns:
        格式化的响应对象
    """
    # 提取文本
    text_parts = [node.node.text for node in nodes]
    combined_text = "\n\n".join(text_parts)
    
    # 创建响应对象
    response = Response(
        response=combined_text,
        source_nodes=nodes
    )
    
    return response

