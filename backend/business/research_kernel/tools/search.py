"""
研究内核检索工具：封装现有检索能力为 Agent 可调用的取证工具

核心职责：
- vector_search：向量语义检索，返回格式化证据片段
- hybrid_search：混合检索（向量 + BM25），返回格式化证据片段

不负责：证据记录（由 evidence 工具负责）、判断形成、状态管理
"""

from __future__ import annotations

from typing import Any, List, Optional

from llama_index.core.tools import FunctionTool

from backend.infrastructure.indexer import IndexManager
from backend.infrastructure.logger import get_logger
from backend.infrastructure.config import config
from backend.business.rag_engine.retrieval.factory import create_retriever

logger = get_logger("research_kernel.tools.search")


def create_search_tools(
    index_manager: IndexManager,
    similarity_top_k: Optional[int] = None,
) -> List[FunctionTool]:
    """创建检索工具列表（vector + hybrid）

    Args:
        index_manager: 索引管理器
        similarity_top_k: Top-K 值（默认使用配置）

    Returns:
        FunctionTool 列表
    """
    index = index_manager.get_index()
    top_k = similarity_top_k or config.SIMILARITY_TOP_K

    def vector_search(query: str) -> str:
        """向量语义检索：适合概念理解、语义相似查询。
        输入研究子问题，返回知识库中语义最相关的文档片段及其来源。"""
        return _execute_search(index, query, "vector", top_k)

    def hybrid_search(query: str) -> str:
        """混合检索：结合向量语义和 BM25 关键词匹配。
        适合需要兼顾语义和精确关键词的查询，召回更全面。"""
        return _execute_search(index, query, "hybrid", top_k)

    tools = [
        FunctionTool.from_defaults(
            fn=vector_search,
            name="vector_search",
            description=vector_search.__doc__,
        ),
        FunctionTool.from_defaults(
            fn=hybrid_search,
            name="hybrid_search",
            description=hybrid_search.__doc__,
        ),
    ]

    logger.info("研究内核检索工具已创建", tool_count=len(tools), top_k=top_k)
    return tools


def _execute_search(index: Any, query: str, strategy: str, top_k: int) -> str:
    """执行检索并格式化结果"""
    query = query.strip()
    if not query:
        return "错误：查询不能为空。"

    try:
        retriever = create_retriever(
            index=index,
            retrieval_strategy=strategy,
            similarity_top_k=top_k,
        )
        nodes = retriever.retrieve(query)

        if not nodes:
            return f'未找到与"{query}"相关的内容。'

        return _format_results(nodes, strategy, query)

    except Exception as exc:
        logger.warning("检索执行失败", strategy=strategy, query=query[:50], error=str(exc))
        return f"检索失败（策略={strategy}）：{exc}"


def _format_results(nodes: list, strategy: str, query: str) -> str:
    """将检索节点格式化为 Agent 可读的文本"""
    lines = [f"检索结果（策略={strategy}，共{len(nodes)}条）：\n"]

    for i, node_with_score in enumerate(nodes, 1):
        node = node_with_score.node if hasattr(node_with_score, "node") else node_with_score
        score = node_with_score.score if hasattr(node_with_score, "score") else 0.0
        text = node.text if hasattr(node, "text") else str(node)
        metadata = node.metadata if hasattr(node, "metadata") else {}
        source_ref = _extract_source_ref(metadata)

        text_preview = text.strip().replace("\n", " ")
        if len(text_preview) > 500:
            text_preview = text_preview[:500] + "..."

        lines.append(
            f"[{i}] 相关度={score:.3f} | 来源={source_ref}\n{text_preview}\n"
        )

    return "\n".join(lines)


def _extract_source_ref(metadata: dict) -> str:
    """从元数据提取来源标注"""
    file_name = metadata.get("file_name") or metadata.get("filename", "")
    if file_name:
        return f"file:{file_name}"
    file_path = metadata.get("file_path", "")
    if file_path:
        return f"path:{file_path}"
    return "unknown"
