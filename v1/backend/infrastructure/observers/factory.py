"""
观察器工厂函数：根据配置创建合适的观察器

主要功能：
- create_default_observers()：创建默认的观察器管理器，根据配置启用LlamaDebug、RAGAS等

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

from backend.infrastructure.observers.llama_debug_observer import LlamaDebugObserver
from backend.infrastructure.observers.ragas_evaluator import RAGASEvaluator
from backend.infrastructure.observers.manager import ObserverManager
from backend.infrastructure.config import config
from backend.infrastructure.logger import get_logger

logger = get_logger('observer_factory')


def create_default_observers(
    enable_debug: bool = True,
    enable_ragas: bool = True,
    **kwargs
) -> ObserverManager:
    """创建默认的观察器管理器
    
    Args:
        enable_debug: 是否启用 LlamaDebug（默认启用）
        enable_ragas: 是否启用 RAGAS 评估器（默认启用）
        **kwargs: 其他参数
        
    Returns:
        配置好的 ObserverManager
    """
    manager = ObserverManager()
    
    # LlamaDebug 观察器（默认启用）
    if enable_debug:
        try:
            debug = LlamaDebugObserver(
                enabled=True,
                print_trace_on_end=kwargs.get('print_trace', True),
            )
            manager.add_observer(debug)
            logger.info("✅ 已添加 LlamaDebug 观察器（默认启用）")
            
        except Exception as e:
            logger.warning(f"⚠️  LlamaDebug 观察器创建失败: {e}")
    
    # RAGAS 评估器（默认启用）
    if enable_ragas:
        try:
            ragas = RAGASEvaluator(
                enabled=True,
                metrics=kwargs.get('ragas_metrics', None),
                batch_size=kwargs.get('ragas_batch_size', 1),  # 每次查询立即评估
            )
            manager.add_observer(ragas)
            logger.info("✅ 已添加 RAGAS 评估器（默认启用）")
            
        except Exception as e:
            logger.warning(f"⚠️  RAGAS 评估器创建失败: {e}")
    
    logger.info(f"📊 观察器管理器已创建: {len(manager.observers)} 个观察器")
    
    return manager


def create_observer_from_config() -> ObserverManager:
    """创建观察器管理器（按配置启用）"""
    return create_default_observers(
        enable_debug=config.ENABLE_DEBUG_HANDLER,
        enable_ragas=config.ENABLE_RAGAS,
        print_trace=config.DEBUG_PRINT_TRACE,
        ragas_metrics=config.RAGAS_METRICS,
        ragas_batch_size=config.RAGAS_BATCH_SIZE,
    )
