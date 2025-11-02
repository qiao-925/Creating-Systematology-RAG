"""
查询引擎模块 - 向后兼容层
已模块化拆分，此文件保持向后兼容
"""

from src.query import (
    QueryEngine,
    SimpleQueryEngine,
    format_sources,
    create_query_engine,
)

__all__ = [
    'QueryEngine',
    'SimpleQueryEngine',
    'format_sources',
    'create_query_engine',
]
