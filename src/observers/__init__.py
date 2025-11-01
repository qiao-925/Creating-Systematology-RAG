"""
观察器模块
提供统一的可观测性接口，支持多种观察器
"""

# 延迟导入，避免初始化时加载所有依赖

__all__ = [
    'BaseObserver',
    'ObserverType',
    'ObserverManager',
    'PhoenixObserver',
    'LlamaDebugObserver',
    'create_default_observers',
]


def __getattr__(name):
    """延迟导入支持"""
    if name == 'BaseObserver':
        from src.observers.base import BaseObserver
        return BaseObserver
    elif name == 'ObserverType':
        from src.observers.base import ObserverType
        return ObserverType
    elif name == 'ObserverManager':
        from src.observers.manager import ObserverManager
        return ObserverManager
    elif name == 'PhoenixObserver':
        from src.observers.phoenix_observer import PhoenixObserver
        return PhoenixObserver
    elif name == 'LlamaDebugObserver':
        from src.observers.llama_debug_observer import LlamaDebugObserver
        return LlamaDebugObserver
    elif name == 'create_default_observers':
        from src.observers.factory import create_default_observers
        return create_default_observers
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

