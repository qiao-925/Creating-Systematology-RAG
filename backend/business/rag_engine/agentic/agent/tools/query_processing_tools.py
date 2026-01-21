"""
查询处理工具模块：将查询处理函数封装为 LlamaIndex FunctionTool

主要功能：
- create_query_processing_tools()：创建查询处理工具列表
- 工具：analyze_intent, rewrite_query, decompose_multi_intent

设计说明：
- 使用 FunctionTool 封装，供规划 Agent 自主决策调用
- 核心实现在 query_processing_impl.py 中
"""

from typing import List
from llama_index.core.tools import FunctionTool

from backend.infrastructure.logger import get_logger
from backend.business.rag_engine.agentic.agent.tools.query_processing_impl import (
    analyze_intent,
    rewrite_query,
    decompose_multi_intent,
)

logger = get_logger('rag_engine.agentic.tools.query_processing')


def create_query_processing_tools() -> List[FunctionTool]:
    """创建查询处理工具列表
    
    Returns:
        FunctionTool列表，包含意图理解、查询改写、多意图分解工具
    """
    tools = []
    
    # 1. 意图理解工具
    intent_tool = FunctionTool.from_defaults(
        fn=analyze_intent,
        name="analyze_intent",
        description=(
            "意图理解工具：分析查询的意图和特征。"
            "输入用户查询，返回查询类型、复杂度、关键实体等分析结果。"
            "在不确定如何处理查询时，应该先使用此工具分析意图。"
        ),
    )
    tools.append(intent_tool)
    
    # 2. 查询改写工具
    rewrite_tool = FunctionTool.from_defaults(
        fn=rewrite_query,
        name="rewrite_query",
        description=(
            "查询改写工具：将查询改写为更适合检索的形式。"
            "保留关键实体，补充领域关键词，扩展语义。"
            "当意图分析显示 needs_rewrite=true 时应使用此工具。"
        ),
    )
    tools.append(rewrite_tool)
    
    # 3. 多意图分解工具
    decompose_tool = FunctionTool.from_defaults(
        fn=decompose_multi_intent,
        name="decompose_multi_intent",
        description=(
            "多意图分解工具：将包含多个问题的查询分解为独立子查询。"
            "当查询包含多个问号、'和'、'以及'等连接词时应考虑使用。"
            "分解后的子查询可以分别检索，最后合并结果。"
        ),
    )
    tools.append(decompose_tool)
    
    logger.info(
        "创建查询处理工具完成",
        tool_count=len(tools),
        tools=["analyze_intent", "rewrite_query", "decompose_multi_intent"]
    )
    
    return tools
