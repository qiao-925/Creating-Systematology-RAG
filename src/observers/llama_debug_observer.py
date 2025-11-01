"""
LlamaDebug 观察器
提供 LlamaIndex 内置的调试日志功能
"""

from typing import Any, Dict, List, Optional
from llama_index.core.callbacks import LlamaDebugHandler

from src.observers.base import BaseObserver, ObserverType
from src.logger import setup_logger

logger = setup_logger('llama_debug_observer')


class LlamaDebugObserver(BaseObserver):
    """LlamaDebug 观察器
    
    提供 LlamaIndex 内置的调试日志功能
    """
    
    def __init__(
        self,
        name: str = "llama_debug",
        enabled: bool = True,
        print_trace_on_end: bool = True,
    ):
        """初始化 LlamaDebug 观察器
        
        Args:
            name: 观察器名称
            enabled: 是否启用
            print_trace_on_end: 是否在结束时打印追踪信息
        """
        super().__init__(name, enabled)
        self.print_trace_on_end = print_trace_on_end
        self.handler = None
        
        if self.enabled:
            self.setup()
    
    def get_observer_type(self) -> ObserverType:
        return ObserverType.DEBUG
    
    def setup(self) -> None:
        """设置 LlamaDebug"""
        logger.info("🐛 初始化 LlamaDebug 观察器")
        
        try:
            self.handler = LlamaDebugHandler(
                print_trace_on_end=self.print_trace_on_end
            )
            
            logger.info("✅ LlamaDebug 观察器初始化完成")
            
        except Exception as e:
            logger.error(f"❌ LlamaDebug 初始化失败: {e}")
            self.enabled = False
    
    def on_query_start(self, query: str, **kwargs) -> Optional[str]:
        """查询开始时回调"""
        # LlamaDebugHandler 自动处理
        return None
    
    def on_query_end(
        self,
        query: str,
        answer: str,
        sources: List[Dict],
        trace_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """查询结束时回调"""
        # LlamaDebugHandler 自动处理
        pass
    
    def get_callback_handler(self):
        """获取 LlamaIndex 兼容的回调处理器"""
        return self.handler
    
    def get_event_pairs(self):
        """获取事件对"""
        if self.handler:
            return self.handler.get_event_pairs()
        return []
    
    def get_report(self) -> Dict[str, Any]:
        """获取调试报告"""
        report = {
            "observer": self.name,
            "type": self.get_observer_type().value,
            "enabled": self.enabled,
            "print_trace_on_end": self.print_trace_on_end,
        }
        
        if self.handler:
            event_pairs = self.get_event_pairs()
            report["events_count"] = len(event_pairs)
        
        return report
    
    def teardown(self) -> None:
        """清理资源"""
        logger.info("🧹 清理 LlamaDebug 资源")

