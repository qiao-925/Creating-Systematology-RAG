"""
观察器管理器
统一管理多个观察器，协调它们的工作
"""

from typing import Any, Dict, List, Optional
from src.infrastructure.observers.base import BaseObserver, ObserverType
from src.infrastructure.logger import get_logger

logger = get_logger('observer_manager')


class ObserverManager:
    """观察器管理器
    
    统一管理多个观察器，协调它们的工作
    """
    
    def __init__(self):
        """初始化观察器管理器"""
        self.observers: List[BaseObserver] = []
        logger.info("📊 初始化观察器管理器")
    
    def add_observer(self, observer: BaseObserver) -> None:
        """添加观察器
        
        Args:
            observer: 观察器实例
        """
        self.observers.append(observer)
        logger.info(f"➕ 添加观察器: {observer}")
    
    def remove_observer(self, observer: BaseObserver) -> None:
        """移除观察器"""
        if observer in self.observers:
            self.observers.remove(observer)
            logger.info(f"➖ 移除观察器: {observer}")
    
    def get_observers_by_type(self, observer_type: ObserverType) -> List[BaseObserver]:
        """按类型获取观察器"""
        return [
            obs for obs in self.observers
            if obs.get_observer_type() == observer_type and obs.is_enabled()
        ]
    
    def on_query_start(self, query: str, **kwargs) -> Dict[str, Optional[str]]:
        """通知所有观察器：查询开始
        
        Returns:
            观察器名称到追踪ID的映射
        """
        trace_ids = {}
        
        for observer in self.observers:
            if observer.is_enabled():
                try:
                    trace_id = observer.on_query_start(query, **kwargs)
                    if trace_id:
                        trace_ids[observer.name] = trace_id
                except Exception as e:
                    logger.error(f"❌ 观察器 {observer.name} 处理失败: {e}")
        
        return trace_ids
    
    def on_query_end(
        self,
        query: str,
        answer: str,
        sources: List[Dict],
        trace_ids: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> None:
        """通知所有观察器：查询结束"""
        for observer in self.observers:
            if observer.is_enabled():
                try:
                    trace_id = trace_ids.get(observer.name) if trace_ids else None
                    observer.on_query_end(
                        query, answer, sources, trace_id, **kwargs
                    )
                except Exception as e:
                    logger.error(f"❌ 观察器 {observer.name} 处理失败: {e}")
    
    def on_retrieval(self, query: str, nodes: List[Any], **kwargs) -> None:
        """通知所有观察器：检索完成"""
        for observer in self.observers:
            if observer.is_enabled():
                try:
                    observer.on_retrieval(query, nodes, **kwargs)
                except Exception as e:
                    logger.error(f"❌ 观察器 {observer.name} 处理失败: {e}")
    
    def get_callback_handlers(self) -> List[Any]:
        """获取所有观察器的回调处理器（用于LlamaIndex）
        
        Returns:
            回调处理器列表
        """
        handlers = []
        
        for observer in self.observers:
            if observer.is_enabled() and hasattr(observer, 'get_callback_handler'):
                handler = observer.get_callback_handler()
                if handler:
                    handlers.append(handler)
        
        return handlers
    
    def get_summary(self) -> Dict[str, Any]:
        """获取所有观察器的摘要"""
        return {
            "total_observers": len(self.observers),
            "enabled_observers": len([obs for obs in self.observers if obs.is_enabled()]),
            "observers": [obs.get_report() for obs in self.observers],
        }
    
    def teardown_all(self) -> None:
        """清理所有观察器"""
        logger.info("🧹 清理所有观察器")
        
        for observer in self.observers:
            try:
                observer.teardown()
            except Exception as e:
                logger.error(f"❌ 观察器 {observer.name} 清理失败: {e}")
        
        self.observers.clear()

