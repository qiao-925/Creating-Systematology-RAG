"""
Agentic RAG 引擎模块：基于 Agent 的自主检索策略选择

核心功能：通过规划 Agent 自主选择检索策略，提升复杂查询质量。

主要接口：
- AgenticQueryEngine: Agentic RAG 查询引擎（与 ModularQueryEngine 接口一致）
"""

from backend.business.rag_engine.agentic.engine import AgenticQueryEngine

__all__ = ['AgenticQueryEngine']

