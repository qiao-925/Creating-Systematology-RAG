"""
模块化查询引擎 - 向后兼容层
已模块化拆分，此文件保持向后兼容
"""

from src.query.modular.engine import ModularQueryEngine, create_modular_query_engine

__all__ = [
    'ModularQueryEngine',
    'create_modular_query_engine',
]
