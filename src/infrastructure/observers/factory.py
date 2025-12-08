"""
观察器工厂函数：根据配置创建合适的观察器

主要功能：
- create_default_observers()：创建默认的观察器管理器，根据配置启用Phoenix、LlamaDebug、RAGAS等

执行流程：
1. 读取配置
2. 创建相应的观察器实例
3. 注册到观察器管理器
4. 返回管理器实例

特性：
- 工厂模式创建观察器
- 配置驱动
- 支持多种观察器类型
- 统一的观察器管理
"""

from typing import List, Optional
from src.infrastructure.observers.base import BaseObserver
from src.infrastructure.observers.phoenix_observer import PhoenixObserver
from src.infrastructure.observers.llama_debug_observer import LlamaDebugObserver
from src.infrastructure.observers.ragas_evaluator import RAGASEvaluator
from src.infrastructure.observers.manager import ObserverManager
from src.infrastructure.config import config
from src.infrastructure.logger import get_logger

logger = get_logger('observer_factory')


def create_default_observers(
    enable_phoenix: bool = True,
    enable_debug: bool = False,
    enable_ragas: bool = False,
    **kwargs
) -> ObserverManager:
    """创建默认的观察器管理器
    
    Args:
        enable_phoenix: 是否启用 Phoenix
        enable_debug: 是否启用 LlamaDebug
        enable_ragas: 是否启用 RAGAS 评估器
        **kwargs: 其他参数
        
    Returns:
        配置好的 ObserverManager
    """
    manager = ObserverManager()
    
    # Phoenix 观察器
    if enable_phoenix:
        try:
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
    
    # RAGAS 评估器
    if enable_ragas:
        try:
            ragas = RAGASEvaluator(
                enabled=True,
                metrics=kwargs.get('ragas_metrics', None),
                batch_size=kwargs.get('ragas_batch_size', 10),
            )
            manager.add_observer(ragas)
            logger.info("✅ 已添加 RAGAS 评估器")
            
        except Exception as e:
            logger.warning(f"⚠️  RAGAS 评估器创建失败: {e}")
    
    logger.info(f"📊 观察器管理器已创建: {len(manager.observers)} 个观察器")
    
    return manager


def create_observer_from_config() -> ObserverManager:
    """从配置创建观察器管理器
    
    读取配置文件中的观察器配置
    """
    enable_phoenix = getattr(config, 'ENABLE_PHOENIX', True)
    enable_debug = getattr(config, 'ENABLE_DEBUG_HANDLER', False)
    enable_ragas = getattr(config, 'ENABLE_RAGAS', False)
    launch_phoenix_app = getattr(config, 'PHOENIX_LAUNCH_APP', False)
    
    return create_default_observers(
        enable_phoenix=enable_phoenix,
        enable_debug=enable_debug,
        enable_ragas=enable_ragas,
        launch_phoenix_app=launch_phoenix_app,
    )

