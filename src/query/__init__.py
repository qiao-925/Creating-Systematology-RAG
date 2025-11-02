"""
查询引擎模块 - 向后兼容层
保持向后兼容的接口导出
"""

from src.query.engine import QueryEngine
from src.query.simple import SimpleQueryEngine
from src.query.utils import format_sources, create_query_engine

__all__ = [
    'QueryEngine',
    'SimpleQueryEngine',
    'format_sources',
    'create_query_engine',
]

