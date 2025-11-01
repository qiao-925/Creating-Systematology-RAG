"""
观察器工厂函数
根据配置创建合适的观察器
"""

from typing import List, Optional
from src.observers.base import BaseObserver
from src.observers.phoenix_observer import PhoenixObserver, LegacyPhoenixObserver
from src.observers.llama_debug_observer import LlamaDebugObserver
from src.observers.manager import ObserverManager
from src.config import config
from src.logger import setup_logger

logger = setup_logger('observer_factory')


def create_default_observers(
    enable_phoenix: bool = True,
    enable_debug: bool = False,
    use_legacy_phoenix: bool = True,  # 默认使用兼容模式
    **kwargs
) -> ObserverManager:
    """创建默认的观察器管理器
    
    Args:
        enable_phoenix: 是否启用 Phoenix
        enable_debug: 是否启用 LlamaDebug
        use_legacy_phoenix: 是否使用兼容模式的Phoenix（推荐）
        **kwargs: 其他参数
        
    Returns:
        配置好的 ObserverManager
    """
    manager = ObserverManager()
    
    # Phoenix 观察器
    if enable_phoenix:
        try:
            if use_legacy_phoenix:
                # 使用兼容模式（推荐）
                phoenix = LegacyPhoenixObserver(
                    enabled=True,
                    launch_app=kwargs.get('launch_phoenix_app', False),
                )
            else:
                # 使用新模式
                phoenix = PhoenixObserver(
                    enabled=True,
                    launch_app=kwargs.get('launch_phoenix_app', False),
                    host=kwargs.get('phoenix_host', '0.0.0.0'),
                    port=kwargs.get('phoenix_port', 6006),
                )
            
            manager.add_observer(phoenix)
            logger.info("✅ 已添加 Phoenix 观察器")
            
        except Exception as e:
            logger.warning(f"⚠️  Phoenix 观察器创建失败: {e}")
    
    # LlamaDebug 观察器
    if enable_debug:
        try:
            debug = LlamaDebugObserver(
                enabled=True,
                print_trace_on_end=kwargs.get('print_trace', True),
            )
            manager.add_observer(debug)
            logger.info("✅ 已添加 LlamaDebug 观察器")
            
        except Exception as e:
            logger.warning(f"⚠️  LlamaDebug 观察器创建失败: {e}")
    
    logger.info(f"📊 观察器管理器已创建: {len(manager.observers)} 个观察器")
    
    return manager


def create_observer_from_config() -> ObserverManager:
    """从配置创建观察器管理器
    
    读取配置文件中的观察器配置
    """
    enable_phoenix = getattr(config, 'ENABLE_PHOENIX', True)
    enable_debug = getattr(config, 'ENABLE_DEBUG_HANDLER', False)
    launch_phoenix_app = getattr(config, 'PHOENIX_LAUNCH_APP', False)
    
    return create_default_observers(
        enable_phoenix=enable_phoenix,
        enable_debug=enable_debug,
        launch_phoenix_app=launch_phoenix_app,
    )

