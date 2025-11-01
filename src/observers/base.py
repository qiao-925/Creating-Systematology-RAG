"""
观察器基类
定义统一的可观测性接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from enum import Enum


class ObserverType(Enum):
    """观察器类型"""
    TRACING = "tracing"          # 追踪（Phoenix）
    EVALUATION = "evaluation"    # 评估（RAGAS）
    DEBUG = "debug"              # 调试（LlamaDebug）
    METRICS = "metrics"          # 指标收集


class BaseObserver(ABC):
    """可观测性观察器基类
    
    所有观察器实现都应继承此类，实现统一接口
    """
    
    def __init__(self, name: str, enabled: bool = True):
        """初始化观察器
        
        Args:
            name: 观察器名称
            enabled: 是否启用
        """
        self.name = name
        self.enabled = enabled
    
    @abstractmethod
    def get_observer_type(self) -> ObserverType:
        """获取观察器类型"""
        pass
    
    @abstractmethod
    def setup(self) -> None:
        """设置观察器（初始化）"""
        pass
    
    @abstractmethod
    def on_query_start(self, query: str, **kwargs) -> Optional[str]:
        """查询开始时回调
        
        Args:
            query: 查询文本
            **kwargs: 其他参数
            
        Returns:
            追踪ID（如果支持）
        """
        pass
    
    @abstractmethod
    def on_query_end(
        self,
        query: str,
        answer: str,
        sources: List[Dict],
        trace_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """查询结束时回调
        
        Args:
            query: 查询文本
            answer: 回答
            sources: 引用来源
            trace_id: 追踪ID
            **kwargs: 其他参数（如耗时、token数等）
        """
        pass
    
    def on_retrieval(self, query: str, nodes: List[Any], **kwargs) -> None:
        """检索完成时回调（可选）"""
        pass
    
    def on_rerank(self, query: str, nodes: List[Any], **kwargs) -> None:
        """重排序完成时回调（可选）"""
        pass
    
    def on_generation(self, query: str, answer: str, **kwargs) -> None:
        """生成完成时回调（可选）"""
        pass
    
    @abstractmethod
    def get_report(self) -> Dict[str, Any]:
        """获取观察报告
        
        Returns:
            观察报告字典
        """
        pass
    
    @abstractmethod
    def teardown(self) -> None:
        """清理资源"""
        pass
    
    def is_enabled(self) -> bool:
        """检查观察器是否启用"""
        return self.enabled
    
    def enable(self) -> None:
        """启用观察器"""
        self.enabled = True
    
    def disable(self) -> None:
        """禁用观察器"""
        self.enabled = False
    
    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"{self.__class__.__name__}(name={self.name}, {status})"

