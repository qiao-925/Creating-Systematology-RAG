"""
观察器模块：提供统一的可观测性接口，支持多种观察器

主要功能：
- BaseObserver类：观察器基类，定义统一接口
- ObserverType枚举：观察器类型（追踪、评估、调试、指标）
- ObserverManager类：观察器管理器
- PhoenixObserver类：Phoenix追踪观察器
- LlamaDebugObserver类：LlamaDebug调试观察器
- create_default_observers()：创建默认观察器

执行流程：
1. 创建观察器实例
2. 注册到观察器管理器
3. 在查询过程中收集数据
4. 输出可观测性数据

特性：
- 统一的可观测性接口
- 支持多种观察器类型
- 延迟导入机制
- 可插拔设计
"""

# 延迟导入，避免初始化时加载所有依赖

from typing import Any

__all__ = [
    'BaseObserver',
    'ObserverType',
    'ObserverManager',
    'PhoenixObserver',
    'LlamaDebugObserver',
    'create_default_observers',
]


def __getattr__(name: str) -> Any:
    """延迟导入支持"""
    if name == 'BaseObserver':
        from src.infrastructure.observers.base import BaseObserver
        return BaseObserver
    elif name == 'ObserverType':
        from src.infrastructure.observers.base import ObserverType
        return ObserverType
    elif name == 'ObserverManager':
        from src.infrastructure.observers.manager import ObserverManager
        return ObserverManager
    elif name == 'PhoenixObserver':
        from src.infrastructure.observers.phoenix_observer import PhoenixObserver
        return PhoenixObserver
    elif name == 'LlamaDebugObserver':
        from src.infrastructure.observers.llama_debug_observer import LlamaDebugObserver
        return LlamaDebugObserver
    elif name == 'create_default_observers':
        from src.infrastructure.observers.factory import create_default_observers
        return create_default_observers
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

