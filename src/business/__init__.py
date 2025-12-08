"""
业务层模块 - RAG业务逻辑与流程编排

包含 RAG 特定的业务逻辑，包括：
- RAG 引擎核心
- 检索、重排序、格式化策略
- 查询路由和处理
- API 服务
- 对话管理
等业务能力
"""

# 导出主要接口
__all__ = [
    # RAG Engine
    'rag_engine',
    # RAG API
    'rag_api',
    # Chat
    'chat',
]

