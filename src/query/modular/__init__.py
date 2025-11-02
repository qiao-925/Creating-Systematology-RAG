"""
模块化查询引擎模块 - 向后兼容层
保持向后兼容的接口导出
"""

from src.query.modular.engine import ModularQueryEngine

__all__ = [
    'ModularQueryEngine',
]

